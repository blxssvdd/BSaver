import yt_dlp
import logging
import os
from typing import Dict, Optional, List

logger = logging.getLogger("YOUTUBE")

class YouTubeService:
    @staticmethod
    async def get_video_info(url: str) -> Optional[Dict]:
        logger.info(f"Получаем информацию о видео с YouTube: {url}")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
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
            # Удаляем файл если он существует
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.info("Удалён существующий файл")
                except Exception as e:
                    logger.warning(f"Не удалось удалить существующий файл: {e}")
            
            # Используем переданный format_id для выбора качества
            ydl_opts = {
                'format': f'{format_id}+bestaudio/best',  # Используем выбранный формат + лучший аудио
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
            }
            
            logger.info(f"Настройки yt-dlp: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Начинаем скачивание...")
                ydl.download([url])
                
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Файл создан, размер: {file_size} байт")
                return file_size > 0
            else:
                logger.error("Файл не был создан")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании формата: {e}")
            return False

    @staticmethod
    async def download_audio_mp3(url: str, output_path: str) -> bool:
        logger.info(f"Скачиваем mp3 с YouTube: {url}")
        logger.info(f"Путь для сохранения: {output_path}")
        
        # Удаляем файл если он существует
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.info("Удалён существующий файл")
            except Exception as e:
                logger.warning(f"Не удалось удалить существующий файл: {e}")
        
        try:
            # Сначала пробуем стандартный способ
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',  # Предпочитаем m4a
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
            }
            
            logger.info(f"Настройки yt-dlp для MP3: {ydl_opts}")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info("Начинаем скачивание MP3...")
                    ydl.download([url])
                    
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"MP3 файл создан, размер: {file_size} байт")
                    return file_size > 0
                else:
                    # Проверяем файл с двойным расширением .mp3.mp3
                    double_ext_path = output_path + '.mp3'
                    if os.path.exists(double_ext_path):
                        file_size = os.path.getsize(double_ext_path)
                        logger.info(f"MP3 файл создан с двойным расширением, размер: {file_size} байт")
                        # Переименовываем в правильное имя
                        os.rename(double_ext_path, output_path)
                        return file_size > 0
                    else:
                        logger.error("MP3 файл не был создан")
                        return False
                    
            except Exception as e:
                logger.warning(f"Стандартный способ не работает: {e}")
                
                # Альтернативный способ: скачиваем аудио файл, потом конвертируем
                temp_audio_path = output_path.replace('.mp3', '_temp.m4a')
                
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                
                ydl_opts_alt = {
                    'format': '140',  # m4a аудио
                    'outtmpl': temp_audio_path,
                    'quiet': False,
                    'no_warnings': False,
                    'verbose': True,
                    'overwrites': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                    },
                }
                
                logger.info("Пробуем альтернативный способ...")
                
                with yt_dlp.YoutubeDL(ydl_opts_alt) as ydl:
                    ydl.download([url])
                
                if os.path.exists(temp_audio_path):
                    file_size = os.path.getsize(temp_audio_path)
                    logger.info(f"Аудио файл скачан, размер: {file_size} байт")
                    
                    if file_size > 0:
                        # Конвертируем в MP3 с помощью FFmpeg
                        import subprocess
                        try:
                            cmd = [
                                'ffmpeg', '-y', '-i', temp_audio_path, 
                                '-acodec', 'mp3', '-ab', '192k', 
                                output_path
                            ]
                            logger.info(f"Конвертируем в MP3: {' '.join(cmd)}")
                            
                            result = subprocess.run(cmd, capture_output=True, text=True)
                            
                            if result.returncode == 0 and os.path.exists(output_path):
                                final_size = os.path.getsize(output_path)
                                logger.info(f"MP3 файл создан, размер: {final_size} байт")
                                os.remove(temp_audio_path)  # Удаляем временный файл
                                return final_size > 0
                            else:
                                logger.error(f"Ошибка конвертации: {result.stderr}")
                        except Exception as e:
                            logger.error(f"Ошибка при конвертации: {e}")
                        finally:
                            if os.path.exists(temp_audio_path):
                                os.remove(temp_audio_path)
                
            logger.error("MP3 файл не был создан")
            return False
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании mp3: {e}")
            return False 