import os
import sys
import time
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, errors, types, functions, utils, helpers
from telethon.network.connection.tcpobfuscated import ConnectionTcpObfuscated
from telethon.tl.functions.messages import ImportChatInviteRequest
from tqdm import tqdm

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
PHONE = os.getenv("TELEGRAM_PHONE", "").strip()
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
INVITE_LINK = os.getenv("TELEGRAM_INVITE_LINK", "").strip()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./media_uploads").strip()
UPLOAD_DELAY = float(os.getenv("UPLOAD_DELAY", "0.5"))

SESSION_NAME = "telethon_upload_session"
HISTORY_FILE = "uploaded_history.txt"
LOCK_FILE = "uploader.lock"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".3gp", ".m4v"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def acquire_lock():
    """Ensure only one instance of the uploader runs to avoid session ID conflicts."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            # Check if old process is still alive on Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, old_pid)
            if handle:
                kernel32.CloseHandle(handle)
                print(f"[ERROR] Another uploader process (PID {old_pid}) is already running!")
                print("[*] Please close the other terminal window or kill existing python processes before starting.")
                sys.exit(1)
        except Exception:
            pass

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    """Remove lock file on exit."""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass


def load_history():
    """Load set of already uploaded files."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def append_history(file_identifier: str):
    """Save an uploaded file to history immediately."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{file_identifier}\n")
        f.flush()


def get_files_to_upload(folder_path: str):
    """Scan folder recursively and return sorted list of supported media files."""
    path = Path(folder_path)
    if not path.exists():
        print(f"[ERROR] Directory does not exist: {folder_path}")
        return []

    files = [
        f for f in path.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS and f.stat().st_size > 0
    ]
    # Small files (photos) first, so progress is rapid and not blocked by huge videos
    files.sort(key=lambda p: (1 if p.suffix.lower() in VIDEO_EXTENSIONS else 0, p.stat().st_size))
    return files


async def resolve_channel(client: TelegramClient):
    """Find and return the target channel entity."""
    target_entity = None

    if CHANNEL_ID:
        try:
            channel_int = int(CHANNEL_ID)
            target_entity = await client.get_entity(channel_int)
            print(f"[OK] Connected to channel: {getattr(target_entity, 'title', channel_int)}")
            return target_entity
        except Exception as e:
            print(f"[!] Could not resolve channel by ID ({e}). Trying invite link...")

    if INVITE_LINK:
        try:
            invite_hash = INVITE_LINK.split("+")[-1] if "+" in INVITE_LINK else INVITE_LINK.split("/")[-1]
            try:
                updates = await client(ImportChatInviteRequest(invite_hash))
                target_entity = updates.chats[0]
                print(f"[OK] Joined channel via invite link: {getattr(target_entity, 'title', 'Channel')}")
                return target_entity
            except errors.UserAlreadyParticipantError:
                target_entity = await client.get_entity(INVITE_LINK)
                print(f"[OK] Channel found via invite link: {getattr(target_entity, 'title', 'Channel')}")
                return target_entity
        except Exception as e:
            print(f"[ERROR] Could not resolve channel via invite link: {e}")

    return target_entity


async def main():
    acquire_lock()
    print("=" * 65)
    print("   Telegram Auto Media Uploader (High-Reliability Mode)")
    print("=" * 65)

    if not API_ID or not API_HASH:
        print("[ERROR] Please provide TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        release_lock()
        sys.exit(1)

    print(f"[*] Media Directory: {UPLOAD_FOLDER}")
    files = get_files_to_upload(UPLOAD_FOLDER)
    total_found = len(files)
    print(f"[*] Total media files found: {total_found}")

    if total_found == 0:
        print("[!] No supported media files found in the folder.")
        release_lock()
        return

    uploaded_set = load_history()
    pending_files = [f for f in files if str(f.resolve()) not in uploaded_set and f.name not in uploaded_set]
    already_done = total_found - len(pending_files)

    print(f"[*] Already uploaded previously: {already_done}")
    print(f"[*] Remaining files to upload: {len(pending_files)}")

    if not pending_files:
        print("[OK] All files have already been uploaded!")
        release_lock()
        return

    # Use ConnectionTcpObfuscated to bypass ISP packet filtering
    # timeout=300 prevents TimeoutError on large video uploads (50-250MB)
    client = TelegramClient(
        SESSION_NAME,
        API_ID,
        API_HASH,
        connection=ConnectionTcpObfuscated,
        request_retries=10,
        connection_retries=10,
        timeout=300,
        flood_sleep_threshold=120
    )

    await client.start(phone=PHONE)
    print("[OK] Authenticated with Telegram session!")

    channel = await resolve_channel(client)
    if not channel:
        print("[ERROR] Failed to access destination channel. Check Channel ID or Invite Link.")
        await client.disconnect()
        release_lock()
        return

    print("\n[*] Starting upload queue (Photos prioritized first for fast progress).")
    print("[*] Press Ctrl+C at any time to pause safely.\n")

    success_count = 0
    fail_count = 0

    try:
        for idx, file_path in enumerate(pending_files, start=1):
            file_name = file_path.name
            file_size = file_path.stat().st_size
            ext = file_path.suffix.lower()
            is_video = ext in VIDEO_EXTENSIONS

            curr_total_idx = already_done + idx
            progress_prefix = f"[{curr_total_idx}/{total_found}]"

            pbar = tqdm(
                total=file_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"{progress_prefix} {file_name[:24]}",
                leave=True,
                ncols=85
            )

            last_bytes = 0

            def upload_progress(current, total):
                nonlocal last_bytes
                if total and pbar.total != total:
                    pbar.total = total
                delta = current - last_bytes
                if delta > 0:
                    pbar.update(delta)
                    last_bytes = current

            # More retries for large files that are prone to network drops
            max_retries = 8 if file_size > 50 * 1024 * 1024 else 5
            uploaded_ok = False

            for attempt in range(1, max_retries + 1):
                try:
                    if not client.is_connected():
                        print(f"[*] Reconnecting to Telegram...")
                        await client.connect()

                    await client.send_file(
                        entity=channel,
                        file=str(file_path.resolve()),
                        supports_streaming=is_video,
                        progress_callback=upload_progress
                    )
                    # Complete progress bar to 100%
                    pbar.total = pbar.n if pbar.n > 0 else file_size
                    pbar.n = pbar.total
                    pbar.refresh()
                    pbar.close()
                    uploaded_ok = True
                    break
                except errors.FloodWaitError as e:
                    pbar.close()
                    wait_time = e.seconds + 2
                    print(f"\n[!] Telegram FloodWait: Sleeping {wait_time}s to respect rate limits...")
                    await asyncio.sleep(wait_time)
                    pbar = tqdm(
                        total=file_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc=f"{progress_prefix} Retry {file_name[:20]}",
                        leave=False,
                        ncols=85
                    )
                    last_bytes = 0
                except (ConnectionError, errors.RPCError, asyncio.TimeoutError, OSError) as e:
                    pbar.close()
                    # Exponential backoff: 5s, 10s, 20s, 30s, 45s...
                    backoff = min(5 * (2 ** (attempt - 1)), 60)
                    print(f"\n[!] Network drop on attempt {attempt}/{max_retries}: {e}")
                    if attempt < max_retries:
                        print(f"[*] Waiting {backoff}s before retry...")
                        await asyncio.sleep(backoff)
                        try:
                            # Full disconnect-reconnect cycle for clean state
                            await client.disconnect()
                        except Exception:
                            pass
                        try:
                            await client.connect()
                        except Exception:
                            pass
                        pbar = tqdm(
                            total=file_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=f"{progress_prefix} Retry {file_name[:20]}",
                            leave=False,
                            ncols=85
                        )
                        last_bytes = 0
                    else:
                        print(f"[ERROR] Skipped {file_name} after {max_retries} connection attempts.")
                except Exception as e:
                    pbar.close()
                    print(f"\n[ERROR] Unexpected error uploading {file_name}: {e}")
                    break

            if uploaded_ok:
                append_history(str(file_path.resolve()))
                append_history(file_name)
                success_count += 1
            else:
                fail_count += 1

            if UPLOAD_DELAY > 0:
                await asyncio.sleep(UPLOAD_DELAY)

    except KeyboardInterrupt:
        print("\n\n[!] Upload paused by user (Ctrl+C).")
        print("[*] All completed files are saved. Run again anytime to resume.")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        release_lock()
        print("\n" + "=" * 65)
        print(f"[*] Session Finished.")
        print(f"[*] Uploaded in this run : {success_count}")
        print(f"[*] Failed/Skipped       : {fail_count}")
        print(f"[*] Total Completed      : {already_done + success_count}/{total_found}")
        print("=" * 65)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
