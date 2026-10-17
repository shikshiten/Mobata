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

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "").strip()
PHONE = os.getenv("TELEGRAM_PHONE", "").strip()
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "").strip()
INVITE_LINK = os.getenv("TELEGRAM_INVITE_LINK", "").strip()

raw_upload_folder = os.getenv("UPLOAD_FOLDER", "./Upload").strip()
upload_path = Path(raw_upload_folder)
if not upload_path.is_absolute():
    upload_path = (BASE_DIR / upload_path).resolve()

if not upload_path.exists():
    fallback_path = BASE_DIR / "Upload"
    if fallback_path.exists():
        upload_path = fallback_path

UPLOAD_FOLDER = str(upload_path)
UPLOAD_DELAY = float(os.getenv("UPLOAD_DELAY", "0.5"))

SESSION_NAME = str(BASE_DIR / "telethon_upload_session")
HISTORY_FILE = str(BASE_DIR / "uploaded_history.txt")
LOCK_FILE = str(BASE_DIR / "uploader.lock")
LOG_FILE = str(BASE_DIR / "uploader.log")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".3gp", ".m4v"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


def write_log(message: str):
    """Write timestamped entry to uploader.log."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
    except Exception:
        pass



def acquire_lock():
    """Ensure only one instance of the uploader runs to avoid session ID conflicts."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, old_pid)
                if handle:
                    exit_code = ctypes.c_ulong()
                    still_running = False
                    if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                        still_running = (exit_code.value == 259)
                    kernel32.CloseHandle(handle)
                    if still_running:
                        print(f"[ERROR] Another uploader process (PID {old_pid}) is already running!")
                        print("[*] Please close the other terminal window or kill existing python processes before starting.")
                        sys.exit(1)
            else:
                os.kill(old_pid, 0)
                print(f"[ERROR] Another uploader process (PID {old_pid}) is already running!")
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


def detect_media_type(file_path: Path):
    """
    Detect whether file is a video, image, or generic document.
    Reads magic bytes to accurately catch motion photo MP4 videos disguised as .jpg.
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(32)
        # MP4, QuickTime MOV, 3GP, WebM, MKV
        if b"ftyp" in header or header.startswith(b"\x1aE\xdf\xa3"):
            return "video"
        # JPEG, PNG, WebP, BMP, GIF
        if header.startswith(b"\xff\xd8\xff") or header.startswith(b"\x89PNG") or b"WEBP" in header or header.startswith(b"BM"):
            return "image"
    except Exception:
        pass

    ext = file_path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    return "document"


def extract_video_info_and_thumb(file_path: Path):
    """
    Extract video width, height, duration and a preview thumbnail image.
    Generates a crisp thumbnail from 1.5s into the video (avoiding black intro frames).
    Returns (width, height, duration, thumb_path).
    """
    width = 0
    height = 0
    duration = 0
    thumb_path = None

    try:
        import cv2
        cap = cv2.VideoCapture(str(file_path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if fps > 0 and frame_count > 0:
                duration = int(frame_count / fps)

            # Seek past intro black frames (target 1.5s or 10% of total video)
            target_frame = min(int(fps * 1.5), int(frame_count * 0.1)) if frame_count > 15 else 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret and frame_count > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

            if ret and frame is not None:
                # Resize thumbnail to max 320x320 for Telegram guidelines
                h, w = frame.shape[:2]
                scale = min(320 / max(w, 1), 320 / max(h, 1), 1.0)
                thumb_w, thumb_h = max(int(w * scale), 1), max(int(h * scale), 1)
                resized = cv2.resize(frame, (thumb_w, thumb_h), interpolation=cv2.INTER_AREA)

                temp_thumb = file_path.parent / f"_thumb_{file_path.stem}.jpg"
                cv2.imwrite(str(temp_thumb), resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                thumb_path = str(temp_thumb)

            cap.release()
    except Exception:
        pass

    # Fallback to hachoir if cv2 couldn't get duration or dimensions
    if duration == 0 or width == 0:
        try:
            from hachoir.metadata import extractMetadata
            from hachoir.parser import createParser
            parser = createParser(str(file_path))
            if parser:
                with parser:
                    meta = extractMetadata(parser)
                    if meta:
                        if duration == 0 and meta.has("duration"):
                            duration = int(meta.get("duration").total_seconds())
                        if width == 0 and meta.has("width"):
                            width = int(meta.get("width"))
                        if height == 0 and meta.has("height"):
                            height = int(meta.get("height"))
        except Exception:
            pass

    return width, height, duration, thumb_path


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
        write_log(f"No supported media files found in {UPLOAD_FOLDER}")
        release_lock()
        return

    uploaded_set = load_history()
    pending_files = [f for f in files if str(f.resolve()) not in uploaded_set and f.name not in uploaded_set]
    already_done = total_found - len(pending_files)

    print(f"[*] Already uploaded previously: {already_done}")
    print(f"[*] Remaining files to upload: {len(pending_files)}")
    write_log(f"Started upload session. Media Folder: {UPLOAD_FOLDER} | Total: {total_found} | Already Done: {already_done} | Pending: {len(pending_files)}")

    if not pending_files:
        print("[OK] All files have already been uploaded!")
        write_log("All files already uploaded. Exiting.")
        release_lock()
        return

    # Use ConnectionTcpObfuscated to bypass ISP packet filtering
    # timeout=600 prevents TimeoutError on large files (50-250MB+)
    client = TelegramClient(
        SESSION_NAME,
        API_ID,
        API_HASH,
        connection=ConnectionTcpObfuscated,
        request_retries=15,
        connection_retries=15,
        timeout=600,
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
            media_type = detect_media_type(file_path)
            is_video = (media_type == "video")

            # Telegram has a strict 10MB limit for compressed photos.
            # If an image > 9.5MB or is an MP4 motion photo with .jpg extension,
            # send with force_document=True so Telegram accepts it up to 2GB.
            force_doc = False
            if media_type == "image" and file_size > 9.5 * 1024 * 1024:
                force_doc = True
            elif is_video and ext in IMAGE_EXTENSIONS:
                force_doc = True

            # Extract video metadata and generate preview thumbnail to fix black box & 00:00 duration
            thumb_path = None
            attributes = []
            if is_video:
                vid_w, vid_h, vid_dur, thumb_path = extract_video_info_and_thumb(file_path)
                if vid_dur > 0 or vid_w > 0:
                    attributes.append(
                        types.DocumentAttributeVideo(
                            duration=int(vid_dur),
                            w=int(vid_w or 1280),
                            h=int(vid_h or 720),
                            supports_streaming=True
                        )
                    )

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
                        thumb=thumb_path if (thumb_path and os.path.exists(thumb_path)) else None,
                        attributes=attributes if attributes else None,
                        supports_streaming=is_video,
                        force_document=force_doc,
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
                    err_msg = str(e).lower()
                    err_name = type(e).__name__.lower()

                    # Telegram Photo Limit Rejection (e.g. photo exceeds 10MB or motion photo)
                    is_photo_limit = (
                        "cannot be saved by telegram" in err_msg
                        or "exceeds 10mb" in err_msg
                        or "photocrop" in err_name
                        or "photoinvalid" in err_name
                        or "dimension" in err_msg
                    )

                    if is_photo_limit and not force_doc:
                        print(f"\n[!] Photo limitation detected ({e}). Re-uploading cleanly as Document/Video...")
                        force_doc = True
                        pbar = tqdm(
                            total=file_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=f"{progress_prefix} Doc {file_name[:20]}",
                            leave=False,
                            ncols=85
                        )
                        last_bytes = 0
                        continue  # Immediate retry with force_document=True!

                    # Exponential backoff: 4s, 8s, 16s, 24s...
                    backoff = min(4 * attempt, 30)
                    print(f"\n[!] Network drop on attempt {attempt}/{max_retries}: {e}")
                    if attempt < max_retries:
                        print(f"[*] Waiting {backoff}s before retry...")
                        await asyncio.sleep(backoff)
                        try:
                            if not client.is_connected():
                                await client.connect()
                        except Exception:
                            try:
                                await client.disconnect()
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
                        err_str = f"Skipped {file_name} after {max_retries} connection attempts."
                        print(f"[ERROR] {err_str}")
                        write_log(f"FAILED: {err_str}")
                except Exception as e:
                    pbar.close()
                    print(f"\n[ERROR] Unexpected error uploading {file_name}: {e}")
                    write_log(f"ERROR: {file_name}: {e}")
                    break

            # Clean up temporary thumbnail file if generated
            if thumb_path and os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except Exception:
                    pass

            if uploaded_ok:
                append_history(str(file_path.resolve()))
                append_history(file_name)
                success_count += 1
                write_log(f"SUCCESS: [{curr_total_idx}/{total_found}] {file_name} ({file_size} bytes)")
            else:
                fail_count += 1

            if UPLOAD_DELAY > 0:
                await asyncio.sleep(UPLOAD_DELAY)

    except KeyboardInterrupt:
        print("\n\n[!] Upload paused by user (Ctrl+C).")
        print("[*] All completed files are saved. Run again anytime to resume.")
        write_log("Upload paused by user (Ctrl+C).")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        release_lock()
        summary_msg = f"Session Finished. Uploaded: {success_count} | Failed: {fail_count} | Total Done: {already_done + success_count}/{total_found}"
        write_log(summary_msg)
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
