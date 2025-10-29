import os
import re
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import unquote
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class FacebookDownloader(BaseDownloader):
    """Facebook video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "Facebook"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def get_video_info(self, url):
        """Get video information from Facebook URL"""
        try:
            # Clean and validate the URL
            url = self._clean_url(url)
            
            # Make request to the Facebook page
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch video page: HTTP {response.status_code}")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract video title (best effort)
            title = None
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                title = meta_title['content']
            else:
                # Try to find title in other elements
                title_elem = soup.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|header'))
                if title_elem:
                    title = title_elem.get_text().strip()
            
            if not title:
                title = "Facebook Video"
            
            # For demonstration purposes, we'll return placeholder qualities
            # In a real implementation, we would extract actual video URLs
            return {
                "title": title,
                "qualities": ["Best", "HD", "SD"],
                "thumbnail": None,
                "duration": None,
            }
        
        except Exception as e:
            return {"title": "Facebook Video", "qualities": ["Best"]}
    
    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):
        """Download video from Facebook
        
        Args:
            url (str): The Facebook video URL
            save_path (str): The directory to save the downloaded video
            quality (str): The desired quality of the video
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Clean the URL to ensure it's valid
            url = self._clean_url(url)
            
            # Get video info
            if status_callback:
                status_callback("Fetching video information...")
            
            video_info = self.get_video_info(url)
            title = video_info.get("title", "Facebook Video")
            
            # Generate filename
            filename = self.generate_filename(title)
            
            # Ensure output path exists
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(save_path, exist_ok=True)
            
            # Full path for the output file
            output_file = os.path.join(save_path, filename)
            
            if status_callback:
                status_callback("Starting download...")
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path or os.getcwd(),
                platform_name=self.platform,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=extra_opts or {},
            )
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            
            # Clean up partial download if it exists
            if 'output_file' in locals() and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            
            return None
            
    def _clean_url(self, url):
        """Clean and validate Facebook URL
        
        Args:
            url (str): The Facebook video URL
            
        Returns:
            str: Cleaned URL
        """
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a Facebook video URL
        if not ('facebook.com' in url or 'fb.com' in url or 'fb.watch' in url):
            raise ValueError("Not a valid Facebook URL")
            
        # Convert mobile URLs to desktop
        url = url.replace('m.facebook.com', 'www.facebook.com')
        
        return url
    
    def get_available_qualities(self, url):
        """Get available video qualities"""
        try:
            video_info = self.get_video_info(url)
            return video_info["qualities"]
        except Exception:
            return ["Best"]  # Default fallback