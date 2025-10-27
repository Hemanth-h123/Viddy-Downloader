import time
import os
import logging
from datetime import datetime, timedelta
from web.models import Download
from web.database import db
from web.downloaders import get_downloader
from app import create_app

logger = logging.getLogger(__name__)

def process_download(download_id):
    """Process a single download"""
    app = create_app()
    with app.app_context():
        try:
            download = Download.query.get(download_id)
            if not download:
                logger.error(f"Download {download_id} not found")
                return
                
            # Update status to downloading
            download.status = 'downloading'
            download.started_at = datetime.utcnow()
            db.session.commit()
            
            # Get the appropriate downloader
            downloader = get_downloader(download.platform)
            if not downloader:
                raise Exception(f"No downloader available for {download.platform}")
            
            # Create download directory
            download_dir = os.path.join(app.root_path, 'downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            # Start the download
            download_path = downloader.download(
                url=download.url,
                save_path=download_dir,
                quality=download.quality
            )
            
            # Update status
            if download_path and os.path.exists(download_path):
                download.status = 'completed'
                download.file_path = download_path
                download.completed_at = datetime.utcnow()
                db.session.commit()
                return True
            else:
                raise Exception("Download failed - no file was saved")
                
        except Exception as e:
            logger.error(f"Error processing download {download_id}: {str(e)}")
            if 'download' in locals():
                download.status = 'failed'
                download.error_message = str(e)
                db.session.commit()
            return False
