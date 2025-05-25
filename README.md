# 🎤 karaoke-mvp

A modular, production-ready, self-hosted karaoke pipeline:  
**Download songs, extract metadata, split stems, package instrumentals, organize files, and monitor everything.**  
All services are isolated microservices, built for Docker Compose, with advanced networking, monitoring, and Telegram/Prometheus integration.

---

## 🚀 Quick Start

### 1. **Clone the Repo**

```bash
git clone https://github.com/yourusername/karaoke-mvp.git
cd karaoke-mvp
````

### 2. **Configure Your Environment**

Copy `.env.example` to `.env` and edit as needed (use strong secrets!).

```bash
cp .env.example .env
nano .env
```

- Set `STACK_PREFIX` for naming all containers/volumes.
    
- Set `BACKEND_NETWORK` (usually `${STACK_PREFIX}_backend`).
    
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` for notifications.
    
- (Optional) Set `TUNNEL_TOKEN` for Cloudflare Tunnel access.
    
- (Optional) Set `YT_DLP_COOKIES_FILE` and `YT_DLP_COOKIES_DIR` for YouTube cookies.
    

### 3. **Initialize Data Volumes (Set Permissions)**

**_You MUST do this once after first clone or whenever resetting volumes!_**

```bash
docker compose -f docker-compose.init.yml --env-file .env up
```

This will create and `chown` all Docker named volumes for your pipeline.

---

## 🟢 Run the Core Pipeline (Production)

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.prod.override.yml --env-file .env up -d
```

- All services run on an isolated internal network.
    
- Ports are bound to localhost only (use a reverse proxy or tunnel for outside access).
    
- Healthchecks and logs included for all services.
    

---

## 🌐 Cloudflare Tunnel (Secure Public Access)

**Expose your stack securely to the Internet—no open inbound ports required!**

1. **Set your `TUNNEL_TOKEN` in `.env`** (from Cloudflare dashboard).
    
2. **Bring up the tunnel:**
    

```bash
docker compose -f docker-compose.tunnel.yml --env-file .env up -d
```

All your stack’s internal services are now accessible via your Cloudflare tunnel.

- Make sure all other services join the same `${BACKEND_NETWORK}`.
    
- Tunnels are isolated from the public net—only exposed through Cloudflare.
    

---

## 🍪 yt-dlp Cookies Support

Some YouTube downloads require authentication cookies for higher-quality or region-locked content.  
**This stack fully supports mounting a cookies.txt file for `yt-dlp`!**

**How to use:**

1. Place your cookies file in a host directory (e.g., `./cookies/cookies.txt`).
    
2. Set these variables in `.env`:
    
    ```
    YT_DLP_COOKIES_FILE=/cookies/cookies.txt
    YT_DLP_COOKIES_DIR=./cookies
    ```
    
3. When running the Telegram bot service, the cookie file will be automatically mounted and used.
    

**Example:**

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.prod.override.yml --env-file .env up -d
```

- The Telegram bot now uses your cookies file for yt-dlp requests.
    

---

## 🧩 Modular Overrides: dev / prod / support / tunnel

- **Production**:  
    `docker-compose.prod.yml` + `docker-compose.prod.override.yml`
    
- **Development**:  
    `docker-compose.dev.yml` + `docker-compose.dev.override.yml`  
    (_Builds from source, hot reload, local changes only_)
    
- **Support Services** (e.g., Prometheus, Grafana, Deemix, Jellyfin):  
    `docker-compose.support.yml` + `docker-compose.support.override.yml`
    
- **Tunnel**:  
    `docker-compose.tunnel.yml`  
    (_Brings up Cloudflare tunnel container—other services must join the same backend network_)
    

You can combine/override as needed for your stack:

```bash
docker compose \
  -f docker-compose.prod.yml \
  -f docker-compose.prod.override.yml \
  -f docker-compose.support.yml \
  -f docker-compose.support.override.yml \
  -f docker-compose.tunnel.yml \
  --env-file .env up -d
```

---

## 🛠️ Telegram Bot – Features

- **Download from YouTube**:  
    `/make <url>` command pulls audio using yt-dlp (with cookie support).
    
- **Improved Metadata Search**:
    
    - Automatic MusicBrainz lookup for title/artist/album after download.
        
    - Paging and “manual” metadata entry supported.
        
    - Select from close matches or enter your own info.
        
- **Metadata JSON is saved and ready for the karaoke pipeline.**
    

---

## 📈 Monitoring & Alerting

- **Prometheus** scrapes `/metrics` from status-api.
    
- **Alertmanager** sends critical notifications to Telegram or email.
    
- **Grafana** is included for dashboards.
    
- **Healthcheck endpoints** on every service for status and troubleshooting.
    
- **Pipeline errors** trigger Telegram notifications with details.
    

---

## 📦 Project Structure

```
.
├── watcher/           # Watches input, triggers pipeline
├── metadata/          # Extracts MP3 metadata
├── splitter/          # Splits audio into stems (Spleeter)
├── packager/          # Repackages to karaoke MP3s
├── organizer/         # Sorts into artist/album folders
├── telegram_youtube_bot/ # Telegram bot: download + metadata
├── maintenance/       # Cleanup and cron jobs
├── status-api/        # Health, metrics, and file status API
├── monitoring/        # Prometheus/Alertmanager config
├── support/           # Jellyfin, Grafana, Deemix configs
├── docker-compose.*.yml # Compose stacks and overrides
├── .env.example       # Sample env config
└── README.md
```

---

## 💡 Common Commands

**Start/stop the pipeline (prod):**

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.prod.override.yml --env-file .env up -d
docker compose down
```

**Start Cloudflare Tunnel:**

```bash
docker compose -f docker-compose.tunnel.yml --env-file .env up -d
```

**Start support services:**

```bash
docker compose -f docker-compose.support.yml -f docker-compose.support.override.yml --env-file .env up -d
```

**Initialize permissions:**

```bash
docker compose -f docker-compose.init.yml --env-file .env up
```

**Rebuild development images (live-reload):**

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.dev.override.yml --env-file .env up --build -d
```

---

## 🐳 CI/CD

- **Images are built/pushed to Docker Hub & GHCR** via [GitHub Actions](https://chatgpt.com/c/.github/workflows/docker-multi-build.yml).
    
- All services are built and linted independently.
    
- Custom healthchecks run for HTTP-exposed services.
    
- Telegram notifications are sent on build success/failure.
    

---

## 🛡️ Security & Notes

- Never commit your real `.env`—use `.env.example` for safe sharing.
    
- Keep `TUNNEL_TOKEN` and `TELEGRAM_BOT_TOKEN` secret.
    
- All internal services run on an isolated Docker bridge network; only Cloudflare Tunnel exposes public endpoints.
    
- For self-hosted HTTPS, use Traefik/Nginx in addition to or instead of Cloudflare.
    

---

## 🤝 Contributing

- Fork and PRs welcome!
    
- Please lint Python code with `flake8` before submitting.
    
- For new microservices, update Compose files and CI workflow.
    

---

## 📚 FAQ

**Q: Where do I get a YouTube cookies file?**  
A: Use browser extensions like [Get cookies.txt](https://www.getcookies.txt/) to export your logged-in YouTube cookies.

**Q: How do I use my own stack prefix or network?**  
A: Set `STACK_PREFIX` and `BACKEND_NETWORK` in your `.env`.

**Q: How do I add new support services?**  
A: Create/modify `docker-compose.support.yml` and the matching `.override.yml`.

---

## ✨ Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
    
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
    
- [MusicBrainz](https://musicbrainz.org/)
    
- [Spleeter](https://github.com/deezer/spleeter)
    
- [Flask](https://flask.palletsprojects.com/)
    

---

** Questions or bugs? Open an issue or ping the Telegram channel set in your `.env`!
