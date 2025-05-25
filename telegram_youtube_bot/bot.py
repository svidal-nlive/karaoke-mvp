import os
import logging
import json
import asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import yt_dlp
import musicbrainzngs

# Log level via env
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging.basicConfig(
    level=LEVELS.get(LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logging.info(f"Logging initialized at {LOG_LEVEL} level")

# Directories and env config
INPUT_DIR = os.environ.get("INPUT_DIR", "/input")
META_DIR = os.environ.get("META_DIR", "/metadata/json")
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
YTDLP_COOKIES = os.environ.get("YT_DLP_COOKIES_FILE", "/cookies/cookies.txt")

# States
AWAITING_METADATA = 1

# Helper: Download YouTube audio (with cookies if present)
def download_youtube_audio(url, output_dir=INPUT_DIR):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "noplaylist": True,
    }
    if os.path.exists(YTDLP_COOKIES):
        ydl_opts["cookiefile"] = YTDLP_COOKIES
        logging.info(f"Using yt-dlp cookies: {YTDLP_COOKIES}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = (
            ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
        )
        return filename, info.get("title", "")

# Save metadata as JSON
def save_metadata_json(base_name, metadata):
    os.makedirs(META_DIR, exist_ok=True)
    json_path = os.path.join(META_DIR, f"{base_name}.mp3.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    return json_path

# MusicBrainz fuzzy search
async def musicbrainz_search(title, artist=""):
    musicbrainzngs.set_useragent("KaraokePipeline", "1.0", "https://yourdomain.com")
    try:
        results = musicbrainzngs.search_recordings(
            recording=title, artist=artist, limit=12
        )
        options = []
        for rec in results["recording-list"]:
            rec_title = rec.get("title", "Unknown")
            rec_artist = (
                rec["artist-credit"][0]["artist"]["name"]
                if rec.get("artist-credit")
                else "Unknown"
            )
            rec_album = (
                rec.get("release-list", [{}])[0].get("title", "Unknown Album")
                if rec.get("release-list")
                else "Unknown Album"
            )
            options.append((rec_title, rec_artist, rec_album))
        return options
    except Exception as e:
        logging.warning(f"MusicBrainz search failed: {e}")
        return []

# Helper: Show paged search results
async def show_search_options(update, context, page=0, page_size=4):
    options = context.user_data.get("match_options", [])
    total = len(options)
    page = max(0, page)
    start = page * page_size
    end = start + page_size
    shown = options[start:end]
    context.user_data["search_page"] = page

    if not shown:
        await update.message.reply_text(
            "No matches left. Send metadata in format: Title;Artist;Album"
        )
        return

    msg = "Select a number, reply 'more' for more options, or 'manual' to enter your own metadata:\n"
    for idx, (title, artist, album) in enumerate(shown, 1):
        msg += f"{idx}. {title} / {artist} / {album}\n"
    if end < total:
        msg += "\nType 'more' to see additional matches."
    await update.message.reply_text(msg)

# Telegram commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send /make <youtube-url> to process a new song."
    )

async def make(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /make <youtube-url>")
        return ConversationHandler.END

    url = context.args[0]
    await update.message.reply_text("Downloading audio...")

    try:
        filename, yt_title = await asyncio.get_event_loop().run_in_executor(
            None, download_youtube_audio, url
        )
        base = os.path.splitext(os.path.basename(filename))[0]
        await update.message.reply_text(f"Searching MusicBrainz for: {base} ...")

        options = await musicbrainz_search(base)
        context.user_data["match_options"] = options
        context.user_data["base"] = base
        context.user_data["search_page"] = 0

        if options:
            await show_search_options(update, context, 0)
            return AWAITING_METADATA
        else:
            await update.message.reply_text(
                "No close matches found.\nSend metadata in format: Title;Artist;Album"
            )
            return AWAITING_METADATA
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

async def receive_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    options = context.user_data.get("match_options", [])
    base = context.user_data.get("base")
    page = context.user_data.get("search_page", 0)
    page_size = 4

    def is_valid_metadata(parts):
        return len(parts) == 3 and parts[0] and parts[1]

    # Show next page if requested
    if text.lower() == "more" and options:
        page += 1
        if page * page_size >= len(options):
            await update.message.reply_text("No more matches.")
            return AWAITING_METADATA
        context.user_data["search_page"] = page
        await show_search_options(update, context, page)
        return AWAITING_METADATA

    if text.lower() == "manual":
        await update.message.reply_text(
            "Send metadata in format: Title;Artist;Album"
        )
        return AWAITING_METADATA

    # Direct manual entry
    if text.count(";") == 2:
        parts = [p.strip() for p in text.split(";")]
        if not is_valid_metadata(parts):
            await update.message.reply_text(
                "Invalid format. Please send as: Title;Artist;Album (both title and artist required)."
            )
            return AWAITING_METADATA
        metadata = {
            "TIT2": parts[0],
            "TPE1": parts[1],
            "TALB": parts[2] or "YouTube Music",
        }
    elif text.isdigit() and options:
        idx = int(text) - 1 + page * page_size
        if 0 <= idx < len(options):
            m = options[idx]
            metadata = {"TIT2": m[0], "TPE1": m[1], "TALB": m[2]}
        else:
            await update.message.reply_text("Invalid selection. Choose a shown number.")
            return AWAITING_METADATA
    else:
        await update.message.reply_text(
            "Invalid input. Reply with a number, 'more', or send Title;Artist;Album."
        )
        return AWAITING_METADATA

    # Save JSON, warn if overwriting
    json_path = os.path.join(META_DIR, f"{base}.mp3.json")
    if os.path.exists(json_path):
        await update.message.reply_text(
            f"A metadata file for '{base}.mp3' already exists and will be overwritten."
        )

    save_metadata_json(base, metadata)
    await update.message.reply_text(
        f"Metadata saved!\n\nTitle: {metadata['TIT2']}\nArtist: {metadata['TPE1']}\nAlbum: {metadata['TALB']}\n\nReady for pipeline processing."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("make", make)],
        states={
            AWAITING_METADATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_metadata)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logging.basicConfig(level=logging.INFO)
    app.run_polling()

if __name__ == "__main__":
    main()
