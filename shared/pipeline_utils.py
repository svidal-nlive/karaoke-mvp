"""
Pipeline utility functions shared across all karaoke-mvp services.

- Status and error tracking (via Redis)
- Retry logic per stage
- Notification helpers (Telegram, Slack, Email)
- String sanitation for filenames
- Health endpoint
"""

import os
import logging
logging.basicConfig(level=logging.INFO)
import redis
import requests
import smtplib
from email.message import EmailMessage
import traceback
import datetime
import time

# -------- ENV VARS --------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
NOTIFY_EMAILS = os.environ.get("NOTIFY_EMAILS")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

# -------- REDIS CLIENT (singleton) --------
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# -------- STRING SANITIZATION --------
def clean_string(s):
    """Sanitize input for safe filesystem usage."""
    if not isinstance(s, str):
        s = str(s)
    # Remove null bytes, slashes, and whitespace
    return s.replace('\x00', '').replace('/', '-').replace('\\', '-').strip()

# -------- STATUS & ERROR MANAGEMENT --------
def set_file_status(filename, status, error=None, extra=None):
    """Set file status in Redis, optionally adding error or extra info."""
    key = f"file:{filename}"
    value = {"status": status}
    if error:
        value["error"] = error
    if extra:
        value.update(extra)
    # Use hset with mapping (hmset is deprecated in redis-py >= 3.5)
    redis_client.hset(key, mapping=value)

def get_files_by_status(status):
    """List all files in Redis with the given status."""
    all_keys = redis_client.keys("file:*")
    files = []
    for key in all_keys:
        val = redis_client.hgetall(key)
        if val.get("status") == status:
            files.append(key.replace("file:", ""))
    return files

def set_file_error(filename, error):
    """Set status to error, attach error details."""
    set_file_status(filename, "error", error=error)

def clear_file_error(filename):
    """Remove error status from file (set to queued, clear retries)."""
    key = f"file:{filename}"
    redis_client.hset(key, "status", "queued")
    for stage in ["metadata", "splitter", "packager", "organizer"]:
        redis_client.delete(f"{stage}_retries:{filename}")
    redis_client.hdel(key, "error")

# -------- NOTIFICATIONS --------
def send_telegram_message(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data, timeout=5)
        except Exception:
            pass

def send_slack_message(message):
    if SLACK_WEBHOOK_URL:
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        except Exception:
            pass

def send_email(subject, message):
    if NOTIFY_EMAILS and SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD:
        try:
            msg = EmailMessage()
            msg.set_content(message)
            msg['Subject'] = subject
            msg['From'] = SMTP_USERNAME
            msg['To'] = [e.strip() for e in NOTIFY_EMAILS.split(",")]
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        except Exception:
            pass

def notify_all(subject, message):
    send_telegram_message(message)
    send_slack_message(message)
    send_email(subject, message)

# -------- RETRY UTILITIES --------
def get_retry_count(stage, filename):
    """Return the current retry count for this stage/filename."""
    return int(redis_client.get(f"{stage}_retries:{filename}") or 0)

def increment_retry(stage, filename):
    """Increment and return the retry count for this stage/filename."""
    retries = get_retry_count(stage, filename) + 1
    redis_client.set(f"{stage}_retries:{filename}", retries)
    return retries

def reset_retry(stage, filename):
    """Clear retry counter for stage/filename."""
    redis_client.delete(f"{stage}_retries:{filename}")

# -------- GENERIC AUTO-RETRY LOGIC --------
def handle_auto_retry(stage, filename, func, max_retries=3, retry_delay=5, notify_fail=True):
    """
    Run func(); if it raises, auto-retry up to max_retries.
    - stage: str, e.g. 'splitter'
    - filename: the file being processed
    - func: callable (should take no arguments)
    """
    for attempt in range(1, max_retries + 1):
        try:
            result = func()
            reset_retry(stage, filename)
            return result
        except Exception as e:
            retries = increment_retry(stage, filename)
            tb = traceback.format_exc()
            timestamp = datetime.datetime.now().isoformat()
            error_details = f"{timestamp}\nException: {e} (attempt {retries})\n\nTraceback:\n{tb}"
            set_file_error(filename, error_details)
            if attempt < max_retries:
                time.sleep(retry_delay)
            elif notify_fail:
                notify_all(
                    f"Pipeline Error [{stage}]",
                    f"❌ {stage.capitalize()} FAILED for {filename} after {max_retries} retries\n\n{e}\n\n{tb}"
                )
            if attempt == max_retries:
                raise

# -------- FILE STATUS SUMMARY --------
def get_file_status(filename):
    """Return status and last error for the given file from Redis."""
    key = f"file:{filename}"
    data = redis_client.hgetall(key)
    return {
        "filename": filename,
        "status": data.get("status", "unknown"),
        "last_error": data.get("error", "")
    }

# -------- HEALTHCHECK UTILS --------
def health_response():
    """Simple Flask healthcheck endpoint."""
    return "ok", 200

