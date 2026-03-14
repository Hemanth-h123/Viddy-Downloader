import os
import time
import re
from web.downloaders.base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class LinkedInDownloader(BaseDownloader):
    """LinkedIn video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "LinkedIn"
    
    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None, media_type="video"):
        """Download media from LinkedIn
        
        Args:
            url (str): The LinkedIn post URL
            save_path (str): The directory to save the downloaded file
            quality (str): The desired quality
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            media_type (str): The type of media to download (video or image)
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Clean the URL to ensure it's valid
            url = self._clean_url(url)
            
            # Ensure output path exists
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(save_path, exist_ok=True)
            
            # LinkedIn may require specific options based on media type
            if not extra_opts:
                extra_opts = {}
            
            if media_type == "image":
                # For LinkedIn images, we might need a different strategy if yt-dlp fails
                # but for now, we'll try yt-dlp with image-specific format
                extra_opts['format'] = 'best'
                extra_opts['writethumbnail'] = False
            else:
                # For videos
                extra_opts['format'] = 'bestvideo+bestaudio/best'
                extra_opts['writethumbnail'] = False
            
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name=self.platform,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=extra_opts,
                media_type=media_type,
            )
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None
            
    def _clean_url(self, url):
        """Clean and validate LinkedIn URL
        
        Args:
            url (str): The LinkedIn video URL
            
        Returns:
            str: Cleaned URL
        """
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a LinkedIn URL
        if not ('linkedin.com' in url):
            raise ValueError("Not a valid LinkedIn URL")
            
        return url
