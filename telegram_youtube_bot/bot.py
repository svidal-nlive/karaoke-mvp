import os
import json
import logging
import asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
)
import yt_dlp
import musicbrainzngs

# --- Constants
INPUT_DIR = "/input"
META_DIR = "/metadata/json"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# --- State tracking
AWAITING_METADATA = range(1)

# --- Helper: Download audio
def download_youtube_audio(url, output_dir=INPUT_DIR):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
        return filename, info.get("title", "")

# --- Helper: Save metadata JSON directly to /metadata/json/
def save_metadata_json(base_name, metadata):
    os.makedirs(META_DIR, exist_ok=True)
    json_path = os.path.join(META_DIR, f"{base_name}.mp3.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    return json_path

# --- Helper: Fuzzy search with MusicBrainz
async def musicbrainz_search(title, artist=""):
    musicbrainzngs.set_useragent("KaraokePipeline", "1.0", "https://yourdomain.com")
    try:
        results = musicbrainzngs.search_recordings(recording=title, artist=artist, limit=5)
        options = []
        for rec in results["recording-list"]:
            rec_title = rec.get("title", "Unknown")
            rec_artist = rec["artist-credit"][0]["artist"]["name"] if rec.get("artist-credit") else "Unknown"
            rec_album = rec.get("release-list", [{}])[0].get("title", "Unknown Album")
            options.append((rec_title, rec_artist, rec_album))
        return options
    except Exception as e:
        logging.warning(f"MusicBrainz search failed: {e}")
        return []

# --- Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send /make <youtube-url> to start processing a new song."
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
        # Fuzzy search
        options = await musicbrainz_search(base)
        if options:
            # Present choices
            msg = "Select the closest match or reply 'manual' to enter your own:\n"
            for idx, (title, artist, album) in enumerate(options, 1):
                msg += f"{idx}. {title} / {artist} / {album}\n"
            context.user_data["match_options"] = options
            context.user_data["base"] = base
            await update.message.reply_text(msg)
            return AWAITING_METADATA
        else:
            # No matches, ask for manual entry
            context.user_data["base"] = base
            await update.message.reply_text(
                "No close matches found.\nSend metadata in format:\nTitle;Artist;Album"
            )
            return AWAITING_METADATA
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

async def receive_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    base = context.user_data.get("base")
    options = context.user_data.get("match_options", [])

    def is_valid_metadata(parts):
        if len(parts) != 3:
            return False
        # Optionally: check for non-empty title and artist (album can be "YouTube Music")
        if not parts[0] or not parts[1]:
            return False
        return True

    if text.lower() == "manual" or text.count(";") == 2:
        if text.lower() == "manual":
            await update.message.reply_text("Send metadata in format:\nTitle;Artist;Album")
            return AWAITING_METADATA
        parts = [p.strip() for p in text.split(";")]
        if not is_valid_metadata(parts):
            await update.message.reply_text(
                "Invalid format. Please send as: Title;Artist;Album\nBoth title and artist must be filled."
            )
            return AWAITING_METADATA
        metadata = {
            "TIT2": parts[0],
            "TPE1": parts[1],
            "TALB": parts[2] or "YouTube Music"
        }
    elif text.isdigit() and 1 <= int(text) <= len(options):
        sel = int(text) - 1
        m = options[sel]
        metadata = {"TIT2": m[0], "TPE1": m[1], "TALB": m[2]}
    else:
        await update.message.reply_text(
            "Invalid response. Reply with a number, or send metadata as Title;Artist;Album"
        )
        return AWAITING_METADATA

    # Final validation: avoid duplicate metadata files
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
            AWAITING_METADATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_metadata)],
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
