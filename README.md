# Karaoke-MVP: End-to-End Automated Karaoke Track Generator

![CI/CD](https://img.shields.io/badge/build-passing-brightgreen)
![Docker Compose](https://img.shields.io/badge/docker-compose-blue)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Overview

Karaoke-MVP is a modular, containerized, multi-stage audio processing pipeline that converts source audio (from YouTube, Deemix, or manual upload) into fully-tagged, organized karaoke instrumental tracks. The system features interactive control via Telegram, robust error handling, automated notifications, and maintenance routines for efficient storage management.

- **Modular microservices** (Python, Flask, Watchdog, Spleeter, etc.)
- **Interactive Telegram bot** for pipeline control and metadata injection
- **Persistent Redis state** and robust file status tracking
- **MusicBrainz fuzzy metadata search** (with fallback/manual entry)
- **Automated error notifications** (Telegram, Slack, email)
- **Maintenance and cleanup services** (Dockerized + Cron support)
- **Production-ready, scalable, and resource-efficient** (run on PC or Synology NAS)

---

## Features

- **Input audio via local upload, YouTube, or Deemix**
- **Automatic pipeline:** `watcher` → `metadata` → `splitter` → `packager` → `organizer`
- **Chunked audio splitting for memory efficiency**
- **Flexible metadata assignment** (auto or interactive/manual)
- **Error recovery, retries, and user escalation**
- **Status API for monitoring**
- **Telegram bot:** `/make <url>` triggers YouTube download + pipeline, metadata selection, error/health notifications
- **Docker Compose orchestration**
- **Scheduled or manual cleanup of residual files**
- **Low resource usage—suitable for NAS and home servers**

---

## Folder Structure

karaoke-mvp/  
├── watcher/ # Monitors input for new audio  
├── metadata/ # Extracts and writes metadata JSON  
├── splitter/ # Spleeter-powered stem separation  
├── packager/ # Tags instrumentals as MP3  
├── organizer/ # Moves finalized files to organized structure  
├── maintenance/ # Cleanup scripts/services  
├── status-api/ # Flask API for status/health  
├── telegram-bot/ # Telegram user control and integration  
├── shared/ # Shared utils (e.g., pipeline_utils.py)  
├── docker-compose.yml  
├── requirements.txt # Per service  
└── README.md


---

## Requirements

- **Docker** & **Docker Compose** (Linux, Windows, macOS, Synology NAS)
- **Telegram bot token** (see setup below)
- **(Optional) Slack webhook, SMTP for notifications**
- DockerHub or public registry (if not building images locally)

---

## Quick Start for Developers

1. Copy `.env.example` to `.env` and fill in secrets.
2. Build and start all services (with local builds):
docker compose -f docker-compose.build.yml up --build

rust
Copy
Edit
3. Or use pre-built images for fastest start:
docker compose -f docker-compose.pull.yml up

bash
Copy
Edit

### Building & Publishing Images (for Maintainers)

```bash
./build_and_push_all.sh
Update DOCKERHUB_USER in the script.

Make sure to push after any code changes to core pipeline services.

---

## Quickstart

1. **Clone the Repository**

    ```sh
    git clone https://github.com/YOUR_USERNAME/karaoke-mvp.git
    cd karaoke-mvp
    ```

2. **Create & Configure `.env`**

    - Copy `.env.example` to `.env` and set all required secrets:
      ```sh
      cp .env.example .env
      ```

    - Set values for `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, etc.

3. **(Optional) Build Images Locally**

    ```sh
    docker compose build
    docker compose up -d
    ```

    Or **pull from DockerHub** (see [Running With Prebuilt Images](#running-with-prebuilt-images)).

4. **Connect the Telegram Bot**

    - Create a bot at https://t.me/BotFather.
    - Add your bot to your group/channel (or DM yourself), get the chat ID.
    - Add the bot token and chat ID to your `.env`.

5. **Upload or Use `/make <YouTube URL>`**

    - The pipeline will:
        - Download audio
        - Ask for or guess metadata
        - Process and notify you at every stage

---

## Maintenance & Cleanup

- **Run maintenance manually**:
    ```sh
    docker compose run --rm maintenance --live
    ```
- **Enable scheduled cleanup with Dockerized cron** (see `maintenance-cron` service).

---

## Status API

- **Check health and file status:**
    ```
    http://localhost:5001/status
    http://localhost:5001/error-files
    http://localhost:5001/metrics
    ```

---

## Running With Prebuilt Images

If running on a NAS or low-powered device, **use DockerHub images** for fastest deployment.

1. **Build and Push Images** (run on your PC):

    ```sh
    # Example
    docker build -t yourdockerhubuser/karaoke-watcher:latest ./watcher
    docker push yourdockerhubuser/karaoke-watcher:latest
    # Repeat for each service
    ```

2. **Create `docker-compose.pull.yml`**:

    ```yaml
    version: "3.8"
    services:
      watcher:
        image: yourdockerhubuser/karaoke-watcher:latest
        ... # all the same volumes/env as original
      metadata:
        image: yourdockerhubuser/karaoke-metadata:latest
        ...
      splitter:
        image: yourdockerhubuser/karaoke-splitter:latest
        ...
      packager:
        image: yourdockerhubuser/karaoke-packager:latest
        ...
      organizer:
        image: yourdockerhubuser/karaoke-organizer:latest
        ...
      status-api:
        image: yourdockerhubuser/karaoke-status-api:latest
        ...
      telegram-bot:
        image: yourdockerhubuser/karaoke-telegram-bot:latest
        ...
      maintenance:
        image: yourdockerhubuser/karaoke-maintenance:latest
        ...
      maintenance-cron:
        image: yourdockerhubuser/karaoke-maintenance-cron:latest
        ...
      redis:
        image: redis:alpine
        ...
    volumes:
      ... # same as before
    ```

3. **Deploy With Pulled Images**:

    ```sh
    docker compose -f docker-compose.pull.yml up -d
    ```

---

## Advanced Topics

- **Add new features via the Telegram bot or pipeline agents**
- **Customize chunk length, Spleeter model, or metadata rules**
 **Monitor logs and interactively retry or clear errors from Redis**

---

## Contribution & License

- **Contributions are welcome!** See `CONTRIBUTING.md`.
- **License:** MIT (see `LICENSE`).

---

## Troubleshooting

- **Splitter fails with “Killed”:**  
  Increase container RAM or reduce chunk length (see splitter config).
- **Telegram bot doesn’t respond:**  
  Double-check your bot token and chat ID in `.env`.
- **Permissions errors on NAS:**  
  Ensure correct user/group mapping for Docker volumes.

---

## Contact

For support, open a GitHub issue or reach out via Telegram!

---

