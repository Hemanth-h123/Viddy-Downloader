import os
import logging
from typing import Optional, Callable, Dict, Any

import yt_dlp
from . import load_config
import shutil


logger = logging.getLogger(__name__)


def sanitize_filename(title: str, platform_name: str) -> str:
    safe = "".join(c for c in title if c not in '\\/*?:"<>|').strip()
    if not safe:
        safe = "Video"
    return f"{safe}_{platform_name}"


def download_with_ytdlp(
    url: str,
    save_path: str,
    platform_name: str,
    quality: str = "Best",
    progress_callback: Optional[Callable[[int], None]] = None,
    status_callback: Optional[Callable[[str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    extra_opts: Optional[Dict[str, Any]] = None,
    media_type: str = "auto",  # auto, video, image, audio
) -> Optional[str]:
    """Download media using yt-dlp with consistent handling.

    Returns the final file path on success, or None on failure/cancel.
    """
    os.makedirs(save_path, exist_ok=True)

    # Progress hook to bridge to UI
    def hook(d: Dict[str, Any]):
        if cancel_check and cancel_check():
            raise KeyboardInterrupt("Download cancelled by user")
        if d.get("status") == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded_bytes = d.get("downloaded_bytes")
            if total_bytes and downloaded_bytes and progress_callback:
                try:
                    pct = int(downloaded_bytes / total_bytes * 100)
                    progress_callback(max(0, min(100, pct)))
                    # Log progress for debugging
                    if status_callback:
                        status_callback(f"Downloaded {downloaded_bytes/1024/1024:.1f}MB of {total_bytes/1024/1024:.1f}MB ({pct}%)")
                except Exception as e:
                    logger.error(f"Progress calculation error: {e}")
            elif progress_callback:
                # Even without size info, send some progress to show activity
                progress_callback(1)  # Just to show it's working
        elif d.get("status") == "finished":
            if progress_callback:
                progress_callback(100)
            if status_callback:
                status_callback("Download finished, processing file...")

    # Map our "quality" to yt-dlp format selector based on media type
    ffmpeg_available = shutil.which("ffmpeg") is not None
    
    if media_type == "image":
        # For images, get the highest resolution image
        fmt = "best[height<=4096]/best"
    elif media_type == "audio":
        # For audio only
        fmt = "bestaudio/best"
    else:
        # For videos or auto-detect
        fmt = "bestvideo+bestaudio/best" if ffmpeg_available else "best[ext=mp4]/best"
        if quality:
            q = quality.lower()
            if q in {"audio", "audio only", "audio-only"}:
                fmt = "bestaudio/best"
            elif q in {"1080p", "720p", "480p", "360p"}:
                # Attempt exact height, fallback to best under that height
                height = q.replace("p", "")
                if ffmpeg_available:
                    fmt = f"bv*[height={height}]+ba/b[height={height}]/bv*+ba/best"
                else:
                    if q == "1080p":
                        height = "720"
                    fmt = f"best[height={height}][ext=mp4]/best[height<={height}][ext=mp4]/best[ext=mp4]/best"

    ytdlp_opts: Dict[str, Any] = {
        "outtmpl": os.path.join(save_path, "%(_title)s_%(id)s.%(ext)s"),
        "format": fmt,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        # Retries and network resilience
        "retries": 15,
        "fragment_retries": 15,
        "concurrent_fragment_downloads": 5,
        "socket_timeout": 30,
        "extractor_retries": 10,
        "file_access_retries": 5,
        # YouTube specific options to handle bot detection
        "extractor_args": {'youtube': {'skip_webpage': False, 'player_skip': False}},
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive",
        },
        # Cookies can help with sites like Instagram/Facebook if configured
        # Users can place cookies.txt at project root or web/ for auth-required content
    }

    if ffmpeg_available:
        # Only set merge target when ffmpeg is present
        ytdlp_opts["merge_output_format"] = "mp4"

    # Apply auth options from config if available
    try:
        cfg = load_config()
    except Exception:
        cfg = {}
    auth = (cfg or {}).get("auth", {}) or {}

    # Cookies: explicit file from config first
    cookies_file = auth.get("cookies_file") or ""
    if cookies_file:
        if os.path.isabs(cookies_file):
            cookie_candidate = cookies_file
        else:
            # Relative to project root
            cookie_candidate = os.path.abspath(cookies_file)
        if os.path.isfile(cookie_candidate):
            ytdlp_opts["cookiefile"] = cookie_candidate
    else:
        # Auto-discover cookies.txt
        for candidate in (
            "cookies.txt",
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.join(save_path, "cookies.txt"),
        ):
            if os.path.isfile(candidate):
                ytdlp_opts["cookiefile"] = candidate
                break

    # Cookies from browser
    browser = (auth.get("cookies_from_browser") or "").strip()
    if browser:
        # yt-dlp supports tuple: (browser, None) or (browser, profile)
        ytdlp_opts["cookiesfrombrowser"] = (browser, None)

    # Credentials
    username = (auth.get("username") or "").strip()
    password = (auth.get("password") or "").strip()
    if username and password:
        ytdlp_opts["username"] = username
        ytdlp_opts["password"] = password

    prod_env = any(os.environ.get(k) for k in ("RENDER", "RAILWAY", "HEROKU", "VERCEL", "FLY_IO", "PRODUCTION")) or os.path.exists("/.dockerenv")
    if prod_env:
        ytdlp_opts.pop("cookiesfrombrowser", None)
        ytdlp_opts.setdefault("youtube_include_dash_manifest", False)
        ytdlp_opts.setdefault("youtube_include_hls_manifest", False)
        ytdlp_opts.setdefault("nocheckcertificate", True)

    if extra_opts:
        ytdlp_opts.update(extra_opts)

    if status_callback:
        status_callback("Starting download...")

    # Try download with current options first
    try:
        with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Compute final path
            if "requested_downloads" in info:
                # Multi-part; choose first completed output
                for item in info["requested_downloads"]:
                    fp = item.get("_filename")
                    if fp and os.path.exists(fp):
                        return fp
            # Single item path
            out = ydl.prepare_filename(info)
            # If post-processing changed extension
            root, _ = os.path.splitext(out)
            # Check for various file extensions based on media type
            if media_type == "image":
                extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
            elif media_type == "audio":
                extensions = (".mp3", ".m4a", ".wav", ".flac", ".ogg")
            else:
                extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov")
            
            for ext in extensions:
                candidate = root + ext
                if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
                    return candidate
            if os.path.exists(out) and os.path.getsize(out) > 1024:
                return out
            return None
    except KeyboardInterrupt:
        # Cancelled by user
        return None
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a DPAPI or cookie/login-related error
        if any(keyword in error_msg for keyword in [
            "dpapi",
            "failed to decrypt",
            "cookies",
            "browser",
            "login required",
            "sign in",
            "private",
            "account required",
        ]):
            logger.warning("Browser cookie extraction failed (likely DPAPI issue): %s", e)
            logger.info("Retrying download without browser cookies...")
            
            # Create a new options dict without browser cookies
            fallback_opts = ytdlp_opts.copy()
            fallback_opts.pop("cookiesfrombrowser", None)
            fallback_opts.pop("cookiefile", None)
            
            if status_callback:
                status_callback("Retrying without browser cookies...")
            
            try:
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    # Compute final path (same logic as above)
                    if "requested_downloads" in info:
                        for item in info["requested_downloads"]:
                            fp = item.get("_filename")
                            if fp and os.path.exists(fp):
                                return fp
                    out = ydl.prepare_filename(info)
                    root, _ = os.path.splitext(out)
                    if media_type == "image":
                        extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
                    elif media_type == "audio":
                        extensions = (".mp3", ".m4a", ".wav", ".flac", ".ogg")
                    else:
                        extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov")
                    
                    for ext in extensions:
                        candidate = root + ext
                        if os.path.exists(candidate) and os.path.getsize(candidate) > 1024:
                            return candidate
                    if os.path.exists(out) and os.path.getsize(out) > 1024:
                        return out
                    return None
            except Exception as retry_e:
                logger.error("Download failed even without browser cookies: %s", retry_e)
                if status_callback:
                    status_callback(f"Error: {retry_e}")
                return None
        else:
            # Other types of errors
            logger.error("yt-dlp download failed: %s", e)
            if status_callback:
                status_callback(f"Error: {e}")
            return None


