import os
import time
import logging
from urllib.parse import urlparse
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

logger = logging.getLogger(__name__)

class InstagramDownloader(BaseDownloader):
    def __init__(self):
        super().__init__()
        self.platform_name = "Instagram"
        print("Using web/downloaders/instagram_downloader.py")

    def extract_shortcode(self, url):
        """Extract the Instagram post shortcode from the URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/').split('/')
        if path and path[-1]:
            return path[-1].split('?')[0]
        return None

    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None):
        """Download Instagram video from the given URL.
        
        Args:
            url (str): The Instagram video URL
            save_path (str): The directory to save the downloaded video
            quality (str): The desired quality of the video (not used for Instagram)
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Instagram supports both videos and images - let yt-dlp auto-detect
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path or os.getcwd(),
                platform_name=self.platform_name,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                media_type="auto",  # Auto-detect videos or images
            )
            return final_path
        except Exception as e:
            logger.error(f"Failed to download Instagram video: {str(e)}")
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None