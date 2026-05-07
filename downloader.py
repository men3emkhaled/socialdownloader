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

    async def download_video(self, url, is_audio=False):
        """Downloads the video or audio and returns the file path"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self._download, url, is_audio)

    def _download(self, url, is_audio=False):
        # Base options
        ydl_opts = {
            'outtmpl': f'{self.download_path}/%(id)s.%(ext)s',
            'max_filesize': 48 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        if is_audio:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'best[ext=mp4]/best',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If it was audio, extension changed to mp3
            if is_audio:
                filename = os.path.splitext(filename)[0] + ".mp3"
            
            # Final check for actual filename
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for f in os.listdir(self.download_path):
                    if f.startswith(os.path.basename(base)):
                        filename = os.path.join(self.download_path, f)
                        break
            
            return filename, info.get('title', 'video')

downloader = Downloader()
