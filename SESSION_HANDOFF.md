# ◈ MOBATA — COMPLETE PROJECT CONTINUITY & HANDOFF GUIDE
> **Generated for seamless transition to a new laptop / workstation.**  
> Keep this file in your repository root. When starting on your new laptop, feed this file to your AI assistant (Antigravity / Claude / ChatGPT) to resume with 100% full context.

---

## 1. 🚀 Quick Prompt for AI on New Laptop
*(Copy-paste the prompt below into Antigravity or your AI assistant on your new laptop to instantly restore full context:)*

```markdown
Hello! I am continuing work on my project "Mobata" which I transferred from my previous laptop.
Please read `SESSION_HANDOFF.md` and `README.md` completely. 
You will find all architectural decisions, recent bug fixes, website design tokens, typography rules, FTP deployment credentials, and current upload queue state documented there.
Review the codebase and confirm you are ready to continue where we left off.
```

---

## 2. ⚠️ CRITICAL: Files You MUST Manually Copy to New Laptop
Because Git ignores sensitive files and databases, **`git clone` ALONE will NOT copy these 3 vital files**. You must copy them manually via Pen Drive, Google Drive, or local transfer from this laptop:

| File Name | Location | Size | Why It Is Critical |
| :--- | :--- | :--- | :--- |
| **`uploaded_history.txt`** | Root `Mobata/` | ~415 KB (10,378+ lines) | **Database of all ~5,189 files already uploaded.** If missing, the uploader will re-upload everything from scratch! |
| **`telethon_upload_session.session`** | Root `Mobata/` | ~102 KB | **Active Telegram MTProto Login Session.** Saves you from re-logging in or requesting SMS/OTP codes. |
| **`.env`** | Root `Mobata/` | ~450 B | Contains your Telegram API ID, API Hash, Phone, Channel ID, and folder configuration. |

> [!IMPORTANT]
> **Check `UPLOAD_FOLDER` in `.env` on your new laptop!**  
> On this laptop it was set to: `UPLOAD_FOLDER=C:\Users\jites\Documents\Upload`  
> If your new laptop has a different Windows username or media folder path, update line 11 of `.env` accordingly.

---

## 3. 🌐 Project Links & Deployment Credentials

* **GitHub Repository**: [https://github.com/shikshiten/Mobata](https://github.com/shikshiten/Mobata)
  * Default Branch: `main`
* **Live Website**: [http://mobata.unaux.com](http://mobata.unaux.com)
* **Website FTP Hosting Credentials**:
  * **FTP Host**: `ftpupload.net`
  * **FTP Username**: `ezyro_42998424`
  * **FTP Password**: `11d2cf`
  * **Web Root Directory**: `/htdocs/`
  * **Fonts Directory**: `/htdocs/assets/fonts/`

---

## 4. 🧠 Summary of Recent Work, Decisions & Fixes

### A. Uploader Architecture (`uploader.py`)
1. **The 10 MB Telegram Photo Bug (SOLVED)**:
   - **Issue**: Upload was stalling on file `[4837/5241]` (`IMG_20260919_131424_317.jpg`, 17.6 MB) with repeated `[!] Network drop: The photo you tried to send cannot be saved by Telegram. A reason may be that it exceeds 10MB`.
   - **Root Cause**: Phone camera Motion Photos and burst videos are actually **MP4 video files** saved with a `.jpg` extension. Telethon defaulted to sending them as compressed photos, which Telegram hard-caps at 10 MB.
   - **Fix Implemented**:
     - Added `detect_media_type(file_path)` using **Magic Byte header inspection** (`ftyp`, `isom`, `moov`).
     - Auto-flagged any media `> 9.5 MB` or video container with `force_document=True` (allowing up to 2 GB per file via Telegram's Document pipeline).
     - Added instant error interceptor: If Telegram throws any photo size/dimension error, it switches instantly to Document mode without 5x retry loops.
     - Increased client timeout to **600 seconds (10 mins)** and optimized exponential backoff to handle large files (50-250 MB) without Windows socket drops (`WinError 1236`, `WinError 64`).

2. **Core Features**:
   - `cryptg` C-extension AES-NI hardware encryption.
   - `ConnectionTcpObfuscated` protocol to bypass ISP DPI / firewall throttling.
   - Atomic instance locking (`uploader.lock`) preventing concurrent session corruptions.
   - Self-healing FloodWait rate-limit handler.
   - `supports_streaming=True` on all video uploads.

### B. Website UI & Typography (`website/`)
1. **Responsive Dual Typography Split**:
   - **Desktop / Laptop View (`min-width: 769px`)**:
     - Global Body & Headings: **Doto** font (`https://fonts.googleapis.com/css2?family=Doto:wght@400..900&display=swap`) with `font-variation-settings: "ROND" 0;`.
     - Code & Terminals: **JetBrains Mono** monospace.
   - **Mobile View (`max-width: 768px`)**:
     - Global Body: **Atyp** font family (Variable & OTF weights locally served from `assets/fonts/`).
     - Headings: **Atyp Display**.
     - Code & Terminals: **JetBrains Mono** monospace.
   - All 4 pages (`index.html`, `setup.html`, `docker.html`, `cloud.html`) share this identical typographic hierarchy.

2. **Mobile Scroll & 3D Tilt Fixes**:
   - **Problem**: 3D tilt on cards previously had `touch-action: none;` which froze mobile vertical touch scrolling and caused cards to jitter on touch.
   - **Fix**: 3D tilt is strictly gated in CSS and JS to desktop fine-pointer devices (`(hover: hover) and (pointer: fine)`). On mobile / touch screens, tilt transforms are completely disabled and cards have `touch-action: pan-y !important;` for buttery smooth native scrolling.

3. **Comparison Table ("Why Traditional Methods Fail")**:
   - **Desktop**: Fixed `100%` container width with `overflow: hidden;` and proportional column widths (`27%`, `24%`, `22%`, `27%`), eliminating horizontal scrollbars on PC.
   - **Mobile**: Touch-friendly horizontal scroll with `overflow-x: auto !important;` and a clear badge hint: `⇄ Swipe to compare features`. Section `.scroll-fade` forced to `opacity: 1 !important;` so the table never remains hidden.

4. **Navigation Layout**:
   - Desktop: Sticky top floating capsule.
   - Mobile: Clean split architecture — brand and actions locked at top; Apple-style floating dock pill at bottom.

---

## 5. 🛠 How to Set Up & Run on the New Laptop

### Step 1: Install Python & Git
- Install **Python 3.10+** (ensure "Add Python to PATH" is checked during installation).
- Install **Git**.

### Step 2: Clone or Copy the Folder
```bash
git clone https://github.com/shikshiten/Mobata.git
cd Mobata
```
*(Or copy your entire `Mobata` folder directly from your old laptop).*

### Step 3: Paste the 3 Critical Files
Ensure the root directory contains:
- `.env`
- `uploaded_history.txt`
- `telethon_upload_session.session`

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
pip install cryptg Pillow
```

### Step 5: Run the Uploader
```powershell
python uploader.py
```
It will automatically connect to your Telegram channel and resume uploading from where you stopped without duplicate files.

### Step 6: Deploying Website Changes (If modified)
To upload website updates to the live hosting:
```powershell
python -c "
import ftplib, os
ftp = ftplib.FTP('ftpupload.net', 'ezyro_42998424', '11d2cf')
ftp.cwd('htdocs')
for f in ['index.html', 'setup.html', 'docker.html', 'cloud.html']:
    with open(os.path.join('website', f), 'rb') as fp:
        ftp.storbinary(f'STOR {f}', fp)
ftp.quit()
print('Website deployed!')
"
```

---

## 6. 📂 Directory Structure

```
Mobata/
├── .env                              # Telegram credentials & paths (DO NOT COMMIT)
├── .env.example                      # Sanitized credentials template
├── .gitignore                        # Git exclusion rules
├── LICENSE                           # MIT License
├── README.md                         # Project documentation for GitHub
├── SESSION_HANDOFF.md                # THIS FILE (Full project state & context)
├── WHY_MOBATA.md                     # Deep technical comparison article
├── docker-compose.yml                # Docker compose configuration
├── Dockerfile                        # Headless Linux container definition
├── Procfile                          # Heroku / Koyeb process descriptor
├── requirements.txt                  # Python dependencies
├── run_uploader.bat                  # One-click Windows launch script
├── telethon_upload_session.session   # Active Telegram MTProto auth session
├── uploaded_history.txt              # Database of completed file IDs
├── uploader.py                       # Main high-performance upload engine
│
├── assets/                           # Branding assets (logos, badges)
│   ├── logo.png
│   └── logo-dark.png
│
└── website/                          # Showcase documentation website
    ├── index.html                    # Main landing page & benchmark matrix
    ├── setup.html                    # Workstation setup guide
    ├── docker.html                   # Docker & NAS guide
    ├── cloud.html                    # Cloud VPS & n8n guide
    └── assets/
        └── fonts/                    # Extracted Atyp font family files
            ├── Atyp-Variable.ttf
            ├── Atyp-Regular.otf
            ├── Atyp-Medium.otf
            ├── Atyp-Semibold.otf
            ├── Atyp-Bold.otf
            └── AtypDisplay-Bold.otf
```

---
*Created on 2026-10-09. All systems tested and fully operational.*
