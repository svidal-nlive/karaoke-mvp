
![CI/CD](https://img.shields.io/badge/build-passing-brightgreen)  
![Docker Compose](https://img.shields.io/badge/docker-compose-blue)  
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## Overview

Karaoke-MVP is a modular, containerized, multi-stage audio processing pipeline that converts source audio (from YouTube, Deemix, or manual upload) into fully-tagged, organized karaoke instrumental tracks.  
The system features interactive control via Telegram, robust error handling, automated notifications, and maintenance routines for efficient storage management.

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

```text
karaoke-mvp/
├── watcher/                # Monitors input for new audio
├── metadata/               # Extracts and writes metadata JSON
├── splitter/               # Spleeter-powered stem separation
├── packager/               # Tags instrumentals as MP3
├── organizer/              # Moves finalized files to organized structure
├── maintenance/            # Cleanup scripts/services
├── status-api/             # Flask API for status/health
├── telegram_youtube_bot/   # Telegram user control and integration
├── shared/                 # Shared utils (e.g., pipeline_utils.py)
├── docker-compose.yml
├── requirements.txt        # Per service
└── README.md
```

---

## Requirements

- **Docker** & **Docker Compose** (Linux, Windows, macOS, Synology NAS)
    
- **Telegram bot token** (see setup below)
    
- **(Optional) Slack webhook, SMTP for notifications**
    
- DockerHub or public registry (if not building images locally)
    

---

## Quick Start for Developers

### 1. Clone the Repository

```sh
git clone https://github.com/YOUR_USERNAME/karaoke-mvp.git
cd karaoke-mvp
```

### 2. Create & Configure `.env`

Copy the example file and fill in all secrets:

```sh
cp .env.example .env
```

Set values for `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, etc. in your `.env`.

### 3. (Optional) Build Images Locally

```sh
docker compose -f docker-compose.build.yml up --build
```

Or use the default Compose file:

```sh
docker compose build
docker compose up -d
```

### 4. Or Use Pre-built Images

For the fastest start (especially on a NAS):

```sh
docker compose -f docker-compose.pull.yml up -d
```

### 5. Connect the Telegram Bot

- Create a bot at [BotFather](https://t.me/BotFather).
    
- Add your bot to your group/channel (or DM yourself), get the chat ID.
    
- Add the bot token and chat ID to your `.env`.
    

### 6. Upload or Use `/make <YouTube URL>`

- The pipeline will:
    
    - Download audio
        
    - Ask for or guess metadata
        
    - Process and notify you at every stage
        

---

## Docker Build Contexts for Each Service

> **Each microservice must be built with its own context.**  
> For example, when building `metadata`, the build context should be the `metadata/` folder.

|Service|Build Context Directory|Dockerfile Location|Exposed Port|Notes|
|---|---|---|---|---|
|watcher|`./watcher`|`watcher/Dockerfile`|5000|Requires `ffmpeg`, mounts `/input` and `/queue`|
|metadata|`./metadata`|`metadata/Dockerfile`|5000|Uses shared utils from `shared/`|
|splitter|`./splitter`|`splitter/Dockerfile`|5000|Requires `ffmpeg` and model files in `/models`|
|packager|`./packager`|`packager/Dockerfile`|5000|Requires `ffmpeg`|
|organizer|`./organizer`|`organizer/Dockerfile`|5000|Uses `shared/` utilities|
|maintenance|`./maintenance`|`maintenance/Dockerfile`|(optional)|Installs cron, no web server unless extended|
|status-api|`./status-api`|`status-api/Dockerfile`|5001|Flask API for status|
|telegram_youtube_bot|`./telegram_youtube_bot`|`telegram_youtube_bot/Dockerfile`|5000|Requires `ffmpeg`, Telegram bot, health optional|

**When building with Docker Compose:**

- The build context and Dockerfile are set per-service in the Compose file.
    
- If building manually:
    

```sh
docker build -t myuser/karaoke-metadata:latest ./metadata -f metadata/Dockerfile
```

**Tip:**  
Never build from the project root unless using multi-stage builds that require cross-service files.  
Always use the service’s subdirectory as context for best performance and smallest images.

---

## Maintenance & Cleanup

- **Run maintenance manually**:
    
    ```sh
    docker compose run --rm maintenance --live
    ```
    
- **Enable scheduled cleanup with Dockerized cron** (see `maintenance-cron` service in Compose).
    

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

### 1. Build and Push Images (run on your PC):

```sh
# Example for one service:
docker build -t yourdockerhubuser/karaoke-watcher:latest ./watcher -f watcher/Dockerfile
docker push yourdockerhubuser/karaoke-watcher:latest
# Repeat for each service
```

### 2. Create `docker-compose.pull.yml`:

Example snippet:

```yaml
version: "3.8"
services:
  watcher:
    image: yourdockerhubuser/karaoke-watcher:latest
    # all the same volumes/env as original
  metadata:
    image: yourdockerhubuser/karaoke-metadata:latest
  # ...repeat for all services
  redis:
    image: redis:alpine
volumes:
  # same as before
```

### 3. Deploy With Pulled Images:

```sh
docker compose -f docker-compose.pull.yml up -d
```

---

## Troubleshooting

- **Splitter fails with “Killed”:**  
    Increase container RAM or reduce chunk length (see splitter config).
    
- **Telegram bot doesn’t respond:**  
    Double-check your bot token and chat ID in `.env`.
    
- **Permissions errors on NAS:**  
    Ensure correct user/group mapping for Docker volumes.
    
- **Build fails for a single service:**  
    Check that the build context and Dockerfile path match the table above.
    
- **Stale containers after code changes:**  
    Run `docker compose down -v` to remove old containers and volumes, then rebuild.
    

---

## Contribution & License

- **Contributions are welcome!** See `CONTRIBUTING.md`.
    
- **License:** MIT (see `LICENSE`).
    

---

## Contact

For support, open a GitHub issue or reach out via Telegram!

---
