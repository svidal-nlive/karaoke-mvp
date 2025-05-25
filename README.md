
---

# Karaoke-MVP Microservices Pipeline

A full-stack, multi-container karaoke processing pipeline built with Python microservices and Docker. Designed for **local development**, **CI/CD automation**, and **easy deployment** with multi-architecture image builds, Telegram notifications, and robust code quality checks.

[GitHub Repo](https://github.com/svidal-nlive/karaoke-mvp)

---

## 🚀 Features

- **Multi-Container Architecture**: Modular microservices for watcher, metadata, splitter, packager, organizer, status-api, maintenance, and Telegram bot.
- **CI/CD Integration**: Automated builds, tests, and linting with GitHub Actions and local dry-runs using [act](https://github.com/nektos/act) and `ci-preflight.sh`.
- **Telegram Notifications**: Build results and failures are sent to your Telegram group or chat.
- **Configurable with `.env`/secrets**: Works locally and in CI with GitHub secrets for credentials and tokens.
- **Multi-Arch Docker Images**: Build and push to DockerHub and GHCR for both `amd64` and `arm64`.
- **Pre-push Code Formatting**: Supports [autopep8](https://github.com/hhatto/autopep8) for consistent Python style across all services.

---

## 📦 Project Structure

```

.  
├── watcher/  
├── metadata/  
├── splitter/  
├── packager/  
├── organizer/  
├── status-api/  
├── maintenance/  
├── telegram_youtube_bot/  
├── shared/  
├── .env.example  
├── .github/  
│ └── workflows/  
│ └── docker-multi-build.yml  
├── ci-preflight.sh  
└── README.md

````

---

## ⚡ Quick Start: Local Development

### 1. **Clone the Repo**

```bash
git clone https://github.com/svidal-nlive/karaoke-mvp.git
cd karaoke-mvp
````

### 2. **Set Up Your `.env`**

Copy the example file and fill in the required variables:

```bash
cp .env.example .env
# Edit .env and provide required values (see below)
```

**Required .env variables:**

- Any microservice-level config (see `.env.example` for guidance)
    
- `DOCKERHUB_USER`, etc. (see secrets below)
    

### 3. **Install Prerequisites**

- Docker & Docker Compose
    
- Python 3.11+
    
- (Optional for local CI dry-run) [act](https://github.com/nektos/act)
    
- (Optional for code formatting) `autopep8`:
    
    ```bash
    pip install autopep8
    ```
    

### 4. **Preflight CI Checks (Optional, Recommended)**

Run this to simulate the CI build, lint, and push locally before you commit/push:

```bash
./ci-preflight.sh
```

- Lints GitHub Actions workflows
    
- Validates `.env`
    
- Runs [act](https://github.com/nektos/act) for a local CI dry-run (if installed)
    
- Dry-run builds all Docker images
    

### 5. **Run the Full Stack**

```bash
docker compose up --build
```

---

## 🛡️ CI/CD Pipeline (GitHub Actions)

- On every push to `main` (or a tagged release), [docker-multi-build.yml](https://chatgpt.com/c/.github/workflows/docker-multi-build.yml) will:
    
    - Lint & test each service
        
    - Build and push Docker images for each microservice to DockerHub & GHCR
        
    - Send a Telegram notification on success/failure
        
    - Run nightly scheduled builds for freshness
        

### GitHub Secrets Required (for CI)

In your repo settings (`Settings > Secrets and variables > Actions > Repository secrets`):

- `DOCKERHUB_USERNAME`
    
- `DOCKERHUB_TOKEN`
    
- `TELEGRAM_BOT_TOKEN`
    
- `TELEGRAM_CHAT_ID`
    

These will override local `.env`/env vars for CI/CD runs.

---

## 🔔 Telegram Notification Setup

1. **Create a bot:** [BotFather](https://t.me/botfather)
    
2. **Add your bot to a group or DM**
    
3. **Get the `chat_id`**: Use [this trick](https://stackoverflow.com/a/32572159) or ask the bot for `/start`.
    
4. **Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in GitHub Secrets (above)**
    

Notifications will be sent automatically during CI builds.

---

## 🎨 Code Formatting (autopep8)

**To auto-format your whole repo (recommended before pushing):**

```bash
autopep8 . --in-place --recursive --aggressive --aggressive
```

---

## 🏗️ Multi-Arch Docker Builds

- The CI will build both `linux/amd64` and `linux/arm64` images for all services
    
- Images are tagged with `${IMAGE_TAG}` (git tag if present, else `latest`)
    
- Pushed to:
    
    - DockerHub: `${DOCKERHUB_USER}/karaoke-<service>:<tag>`
        
    - GHCR: `ghcr.io/<github_owner>/karaoke-<service>:<tag>`
        

---

## 📝 Fresh Pull Checklist

1. Clone repo and `cd karaoke-mvp`
    
2. Copy and edit `.env.example` to `.env`
    
3. Install Python, Docker, and autopep8 if needed
    
4. (Optional) Run `./ci-preflight.sh` to simulate CI pipeline locally
    
5. Run `docker compose up --build`
    
6. Check Telegram for build/push results (if using CI/CD)
    

---

## 💬 Need Help?

- See `.env.example` for config tips
    
- File issues or PRs on [GitHub](https://github.com/svidal-nlive/karaoke-mvp)
    
- For Telegram notifications, check [Bot API docs](https://core.telegram.org/bots/api#sendmessage)
    

---

Happy karaoke hacking! 🎤

---
