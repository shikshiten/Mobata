# ⚡ Why Mobata? (The Story & Engineering Behind It)

> *"Why did we build Mobata, and why can't you just use a standard Telegram Bot or the official Desktop App?"*

If you have ever tried backing up **5,000+ personal photos and 4K videos** (10GB–50GB+) from your phone or PC to a private Telegram channel, you will inevitably hit a wall of technical limitations. 

Here is why **Mobata** was engineered and how it solves every single one of those problems.

---

## 🚫 The 4 Big Problems With Standard Uploading

### 1. The 50 MB Telegram Bot Wall
* **The Problem**: Standard Telegram bots (built with `python-telegram-bot` or `@BotFather`) have a hard ceiling of **50 MB** per file. A modern 30-second mobile video recorded in 1080p or 4K easily exceeds 60 MB–200 MB.
* **Mobata's Solution**: Mobata is built on top of Telegram's **MTProto protocol (Telethon User API)**. This unlocks the full **2 GB per file** limit (and up to **4 GB** for Telegram Premium accounts), allowing full-length 4K movies and large video clips to upload effortlessly.

### 2. ISP Throttling & Deep Packet Inspection (DPI)
* **The Problem**: On many restricted Wi-Fi networks, corporate/public firewalls, and certain regional ISPs, raw MTProto traffic is actively inspected and throttled to as low as **6–20 kB/s**, frequently dropping TCP sockets (`[WinError 64] The specified network name is no longer available`).
* **Mobata's Solution**: 
  - Uses **`ConnectionTcpObfuscated`** to encapsulate and encrypt MTProto framing. Firewalls and ISPs cannot inspect or throttle the payload.
  - Uses native **`cryptg` (C-extension AES-NI)** for hardware-accelerated encryption instead of slow Python bytecode (`pyaes`), resulting in **20x to 80x faster throughput**.

### 3. Telegram FloodWait & Rate Limits
* **The Problem**: Telegram aggressively rate-limits accounts that post hundreds of messages in rapid bursts. If a script doesn't catch these exceptions, the upload crashes and you lose track of where you were.
* **Mobata's Solution**: Smart rate-limiting backoff. If Telegram asks the client to wait 15 seconds, Mobata automatically pauses, sleeps for the exact duration requested by the Telegram server, and resumes automatically without crashing.

### 4. The Crash & Duplicate Nightmare (Zero-Loss Resume)
* **The Problem**: If your power cuts, Wi-Fi drops, or laptop restarts at file 3,420 out of 5,000, running a normal upload tool starts all over again, filling your channel with thousands of duplicates.
* **Mobata's Solution**: Built-in state logging (`uploaded_history.txt`). Every completed upload is flushed to disk instantly. On restart, Mobata scans the folder, compares it against the history in milliseconds, and picks up right at file 3,421.

---

## 📊 Comparison Matrix

| Feature | Telegram Web / Desktop App | Standard Telegram Bot | **Mobata (MTProto)** |
| :--- | :---: | :---: | :---: |
| **Max File Size** | 2 GB (Manual only) | 50 MB strictly | **2 GB – 4 GB** |
| **5,000+ Batch Queue** | Freezes / UI hangs | Fails on large videos | **Fully Automated** |
| **Automatic Resume** | ❌ No | ❌ No | **✅ Yes (Zero Duplicates)** |
| **FloodWait Recovery** | ❌ Crashes / Manual | ❌ Manual handling | **✅ Self-Healing** |
| **ISP DPI Bypass** | ❌ No | ❌ No | **✅ `ConnectionTcpObfuscated`** |
| **Video Streaming** | Depends on codec | Often Document only | **✅ `supports_streaming=True`** |
| **Headless / Cloud Run** | ❌ Requires GUI | ✅ Yes | **✅ CLI / Docker / VPS / Koyeb** |

---

## 💡 Who Is Mobata For?
1. **Photographers & Content Creators**: Archive thousands of RAW photos and 4K footage directly to cloud storage without paid monthly subscriptions.
2. **Everyday Users & Power Users**: Automated backups even on throttled, restricted, or unstable Wi-Fi networks without connection drops.
3. **Homelab & NAS Enthusiasts**: Run Mobata inside a Docker container on your TrueNAS, Unraid, or Raspberry Pi to automatically sync camera dumps to your private channel.
