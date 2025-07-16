from typing import Dict, Optional, List
import logging
import os

import yt_dlp


logger = logging.getLogger("YOUTUBE")

class YouTubeService:
    @staticmethod
    async def get_video_info(url: str) -> Optional[Dict]:
        logger.info(f"Получаем информацию о видео с YouTube: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiefile': 'cookies.txt',
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not isinstance(info, dict):
                    logger.error(f"yt-dlp вернул не dict: {type(info)}")
                    return None
                return {
                    'title': info.get('title', 'YouTube Video'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url', url),
                    'uploader': info.get('uploader'),
                    'formats': info.get('formats', [])
                }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о видео: {e}")
            return None

    @staticmethod
    def extract_video_audio_formats(formats: List[Dict]) -> Dict[str, List[Dict]]:
        video = []
        audio = []
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                video.append(f)
            elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                audio.append(f)
        return {'video': video, 'audio': audio}

    @staticmethod
    async def download_format(url: str, format_id: str, output_path: str) -> bool:
        logger.info(f"Скачиваем формат {format_id} с YouTube: {url}")
        logger.info(f"Путь для сохранения: {output_path}")
        
        try:

            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info("Удалён существующий файл")
                except Exception as e:
                    logger.warning(f"Не удалось удалить существующий файл: {e}")
            

            ydl_opts = {
                'format': f'{format_id}+bestaudio/best',
                'outtmpl': output_path.replace('.webm', '.mp4'),
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                'overwrites': True,
                'noplaylist': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                },
                'merge_output_format': 'mp4',
                'cookiefile': 'cookies.txt',
            }
            
            logger.info(f"Настройки yt-dlp: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Начинаем скачивание...")
                ydl.download([url])
            return True
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании формата: {e}")
            return False

    @staticmethod
    async def download_audio_mp3(url: str, output_path: str) -> bool:
        logger.info(f"Скачиваем mp3 с YouTube: {url}")
        logger.info(f"Путь для сохранения: {output_path}")
        

        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.info("Удалён существующий файл")
            except Exception as e:
                logger.warning(f"Не удалось удалить существующий файл: {e}")
        
        try:

            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': output_path,
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                'overwrites': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                },
                'cookiefile': 'cookies.txt',
            }
            
            logger.info(f"Настройки yt-dlp для MP3: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Начинаем скачивание MP3...")
                ydl.download([url])
            return True
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании mp3: {e}")
            return False 
