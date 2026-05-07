import yt_dlp
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Downloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)

    async def get_info(self, url):
        """Extracts info without downloading"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self._extract_info, url)

    def _extract_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    async def download_video(self, url):
        """Downloads the video and returns the file path"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self._download, url)

    def _download(self, url):
        # Unique filename based on title or ID
        ydl_opts = {
            'format': 'best[ext=mp4]/best', # Prefer mp4 for better compatibility
            'outtmpl': f'{self.download_path}/%(id)s.%(ext)s',
            'max_filesize': 48 * 1024 * 1024, # 48MB limit for Telegram
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If the extension changed during download (e.g. merging)
            # yt-dlp might change the filename extension
            actual_filename = filename
            if not os.path.exists(actual_filename):
                # Check for same id with different extension
                base = os.path.splitext(filename)[0]
                for f in os.listdir(self.download_path):
                    if f.startswith(os.path.basename(base)):
                        actual_filename = os.path.join(self.download_path, f)
                        break
            
            return actual_filename, info.get('title', 'video')

downloader = Downloader()
