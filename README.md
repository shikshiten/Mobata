<div align="center">

  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo.png">
    <img alt="Mobata Logo" src="assets/logo.png" width="220" />
  </picture>

  # Mobata
  ### High-Performance Automated Media Uploader for Telegram
  
  [![Website](https://img.shields.io/badge/Website-mobata.unaux.com-4F46E5?style=for-the-badge&logo=google-chrome&logoColor=white)](http://mobata.unaux.com)
  [![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Telegram MTProto](https://img.shields.io/badge/Telegram-MTProto%20Telethon-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/api)
  [![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

  <p align="center">
    <b>Upload thousands of photos and multi-gigabyte 4K videos to private Telegram channels autonomously.</b><br>
    Zero duplicates • Auto-resume • FloodWait handling • ISP anti-throttling
  </p>

  [◈ Live Website](http://mobata.unaux.com) • [⬡ Why Mobata?](WHY_MOBATA.md) • [▸ Quick Start](#-quick-start-local-setup) • [◼ Docker](#-docker-deployment) • [✦ Cloud & Koyeb](#-cloud-deployment-koyeb--heroku--vps) • [● n8n Automation](#-automation--webhooks-n8n--zapier)

</div>

---

## ◈ About Mobata

**Mobata** is an autonomous, high-throughput media backup system engineered to archive thousands of high-resolution photos and multi-gigabyte 4K videos directly into private Telegram channels with zero manual drag-and-drop effort.

Unlike standard Telegram bots that are artificially throttled and strictly capped at 50 MB, Mobata establishes direct client connections via Telegram's MTProto protocol using native C hardware acceleration (`cryptg`). It features intelligent self-healing FloodWait recovery, connection obfuscation to bypass restrictive ISP deep-packet inspection, in-app video streaming flags, and persistent atomic state tracking ensuring zero duplicate uploads across machine restarts.

* ◈ **Interactive Showcase & Documentation**: [http://mobata.unaux.com](http://mobata.unaux.com)
* ◈ **Local Setup Guide**: [mobata.unaux.com/setup.html](http://mobata.unaux.com/setup.html)
* ◈ **Docker & NAS Sync Guide**: [mobata.unaux.com/docker.html](http://mobata.unaux.com/docker.html)
* ◈ **Cloud VPS & n8n Guide**: [mobata.unaux.com/cloud.html](http://mobata.unaux.com/cloud.html)

---

## ✦ Features at a Glance

* ✦ **No 50 MB Bot Limit**: Powered by MTProto (Telethon), uploading files up to **2 GB** (or **4 GB** with Telegram Premium).
* ✦ **Zero-Loss Auto Resume**: Tracks uploaded files in `uploaded_history.txt`. If your PC restarts or internet disconnects, it resumes exactly where it stopped without duplicating files.
* ✦ **Self-Healing Rate Limits**: Automatically catches Telegram `FloodWaitError`, sleeps for the requested duration, and resumes without crashing.
* ✦ **Hardware Accelerated (`cryptg`)**: Uses compiled C AES-NI hardware encryption, delivering 20x to 80x faster uploads than standard pure-Python libraries.
* ✦ **Anti-Throttling Protocol**: Employs `ConnectionTcpObfuscated` to bypass restrictive Wi-Fi networks, firewalls, and ISP deep-packet inspection (DPI).
* ✦ **Streamable Video Formatting**: Automatically flags uploaded videos with `supports_streaming=True` so they play instantly inside Telegram.
* ✦ **Smart Priority Queue**: Automatically prioritizes smaller photos first to ensure rapid progress, followed by large videos.
* ✦ **Atomic Instance Protection**: Includes built-in process locking (`uploader.lock`) to prevent concurrent session conflicts.

---

## ▸ Quick Start (Local Setup)

### Step 1: Clone the Repository
```bash
git clone https://github.com/shikshiten/Mobata.git
cd Mobata
```

### Step 2: Install Dependencies
Ensure you have **Python 3.9+** installed:
```bash
pip install -r requirements.txt
```

### Step 3: Get Telegram Credentials
You will need your own Telegram API credentials:
1. Go to [my.telegram.org](https://my.telegram.org) and log in with your Telegram account.
2. Click on **"API Development Tools"**.
3. Create an app (enter any name, e.g. `Mobata`).
4. Copy your **`API ID`** and **`API HASH`**.

### Step 4: Configure `.env`
Copy `.env.example` to `.env`:
* **Windows (Command Prompt / PowerShell)**:
  ```powershell
  copy .env.example .env
  ```
* **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

Open `.env` in any text editor and fill in your details:
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_32_character_api_hash
TELEGRAM_PHONE=+1234567890

# Target Channel: ID or Invite Link
TELEGRAM_CHANNEL_ID=-1001234567890
TELEGRAM_INVITE_LINK=https://t.me/+AbCdEfGhIjK

# Folder with media to upload
UPLOAD_FOLDER=C:\Users\YourName\Pictures\Upload
UPLOAD_DELAY=0.5
```

> **[SECURITY TIP]**: Never commit your `.env` or `.session` file to GitHub! They are already protected in `.gitignore`.

### Step 5: Run the Uploader

* **Windows**: Double-click `run_uploader.bat`, or run:
  ```powershell
  python uploader.py
  ```
* **Linux / macOS**:
  ```bash
  python3 uploader.py
  ```

> **[INITIAL AUTHENTICATION]**: Telegram will send a one-time 5-digit login code to your Telegram app. Enter it once into the terminal. Telethon will generate a `.session` file locally and you will never be asked again!

---

## ◼ Docker Deployment

If you want to run Mobata headless on a NAS (TrueNAS, Unraid, Synology) or a local Linux server:

1. Put your media files inside a folder named `media_uploads/`.
2. Configure `.env` with your credentials.
3. Run the container:
   ```bash
   docker compose up -d
   ```
4. View live logs:
   ```bash
   docker compose logs -f
   ```

---

## ✦ Cloud Deployment (Koyeb / Heroku / VPS)

You can run Mobata as a background worker on free or low-cost cloud platforms.

### Option A: Koyeb / Heroku Worker
1. **Pre-generate Session**: Log in once on your local machine so you have `telethon_upload_session.session`.
2. Add your environment variables in Koyeb/Heroku settings (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, etc.).
3. The repo includes a `Procfile`:
   ```text
   worker: python uploader.py
   ```
4. Deploy the repository as a **Worker** service (not a web service).

### Option B: Linux VPS (Systemd Service)
To keep Mobata running permanently in the background on Ubuntu/Debian:
```bash
sudo nano /etc/systemd/system/mobata.service
```
Add:
```ini
[Unit]
Description=Mobata Telegram Auto Uploader
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/Mobata
ExecStart=/usr/bin/python3 /home/your_username/Mobata/uploader.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mobata
sudo systemctl start mobata
```

---

## ● Automation & Webhooks (n8n / Zapier)

Want to trigger Mobata whenever new photos arrive from Google Drive, Nextcloud, or Dropbox?

### Architecture with n8n:
```text
[Google Drive / Camera / Phone] 
               │
               ▼ (New file downloaded)
   [n8n / Local Webhook Node]
               │
               ▼ (Executes local script or drops file into folder)
          [Mobata Queue]
               │
               ▼ (MTProto Chunk Upload)
    [Private Telegram Channel]
```

* **n8n Workflow**:
  1. Add a **Google Drive / Dropbox Node** (Trigger on "New File").
  2. Add a **Write Binary File Node** to save files directly into your `UPLOAD_FOLDER`.
  3. Mobata automatically detects new files in the folder and uploads them without re-uploading older ones!

---

## ◈ Troubleshooting & FAQ

<details>
<summary><b>Q: Telegram says "Server replied with a wrong session ID"?</b></summary>
This happens if you run two instances of the script at the same time using the same session. Mobata includes an automatic <code>uploader.lock</code> mechanism to stop duplicate processes. Simply close any open terminal windows and re-run.
</details>

<details>
<summary><b>Q: My Wi-Fi or ISP network drops the connection (WinError 64)?</b></summary>
Mobata defaults to <code>ConnectionTcpObfuscated</code> and auto-reconnects on network drops. If your current Wi-Fi network or ISP throttles upload bandwidth, connecting to an alternate network or <b>mobile hotspot (5G/4G)</b> can significantly increase speeds.
</details>

<details>
<summary><b>Q: Can I stop and resume anytime?</b></summary>
Yes! Press <code>Ctrl + C</code> at any time. Mobata immediately flushes progress to <code>uploaded_history.txt</code>. When you restart the script, it checks the history in milliseconds and resumes right where you stopped.
</details>

---

## ⬡ License
This project is open-source under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Engineered for autonomous, unlimited media archival. Star the repository if you found it useful!</sub>
</div>
