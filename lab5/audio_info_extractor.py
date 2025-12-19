import soundfile as sf
import mutagen
from pathlib import Path
from typing import Dict, Any
import numpy as np


class AudioExtractionError(Exception):
    """Базовое исключение для ошибок извлечения информации об аудио"""
    pass


class AudioFileError(AudioExtractionError):
    """Исключение для ошибок файлов"""
    pass


class AudioMetadataError(AudioExtractionError):
    """Исключение для ошибок метаданных"""
    pass


class AudioWaveformError(AudioExtractionError):
    """Исключение для ошибок получения волны"""
    pass


class AudioInfoExtractor:
    """
    Класс для извлечения информации из аудиофайлов
    """
    
    @staticmethod
    def get_audio_info(audio_path: str) -> Dict[str, Any]:
        """
        Получение информации об аудиофайле
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Словарь с информацией об аудиофайле
            
        Raises:
            AudioFileError: Если файл не найден или нет доступа
            AudioMetadataError: Если возникла ошибка при получении метаданных
            AudioExtractionError: Если возникла другая ошибка при извлечении информации
        """
        try:
            path_obj = Path(audio_path)
            
            # Проверяем существование файла
            if not path_obj.exists():
                raise AudioFileError(f"Файл не найден: {audio_path}")
            
            if not path_obj.is_file():
                raise AudioFileError(f"Путь не является файлом: {audio_path}")
            
            # Базовая информация о файле
            try:
                file_stat = path_obj.stat()
                file_size = file_stat.st_size
            except PermissionError as e:
                raise AudioFileError(f"Нет доступа к файлу: {audio_path}") from e
            
            info = {
                'title': '',
                'artist': '',
                'album': '',
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'bitrate': 0,
                'file_size': file_size,
                'file_format': path_obj.suffix.lower(),
                'path': str(path_obj),
                'filename': path_obj.name,
                'stem': path_obj.stem
            }
            
            # Получаем информацию с помощью soundfile
            try:
                with sf.SoundFile(audio_path) as audio_file:
                    info['duration'] = len(audio_file) / audio_file.samplerate
                    info['sample_rate'] = audio_file.samplerate
                    info['channels'] = audio_file.channels
                    info['file_format'] = audio_file.format
            except sf.LibsndfileError as e:
                raise AudioMetadataError(f"Не удалось прочитать аудиофайл: {e}") from e
            except (FileNotFoundError, PermissionError) as e:
                raise AudioFileError(f"Ошибка доступа к файлу: {e}") from e
            
            # Пытаемся получить метаданные с помощью mutagen
            try:
                audio = mutagen.File(audio_path, easy=True)
                if audio:
                    # Название композиции
                    if 'title' in audio:
                        info['title'] = audio['title'][0]
                    else:
                        # Используем имя файла как название
                        info['title'] = path_obj.stem
                    
                    # Исполнитель
                    if 'artist' in audio:
                        info['artist'] = audio['artist'][0]
                    
                    # Альбом
                    if 'album' in audio:
                        info['album'] = audio['album'][0]
                    
                    # Продолжительность (если mutagen может получить)
                    if hasattr(audio.info, 'length'):
                        info['duration'] = audio.info.length
                    
                    # Битрейт
                    if hasattr(audio.info, 'bitrate'):
                        info['bitrate'] = audio.info.bitrate // 1000  # В kbps
            except mutagen.MutagenError as e:
                raise AudioMetadataError(f"Не удалось получить метаданные: {e}") from e
            except (FileNotFoundError, PermissionError) as e:
                # Этот случай уже должен быть обработан выше, но для безопасности
                raise AudioFileError(f"Ошибка доступа к файлу при чтении метаданных: {e}") from e
            
            # Форматируем продолжительность
            info['duration_formatted'] = AudioInfoExtractor._format_duration(info['duration'])
            
            # Форматируем размер файла
            info['file_size_formatted'] = AudioInfoExtractor._format_file_size(info['file_size'])
            
            return info
            
        except (AudioFileError, AudioMetadataError, AudioExtractionError):
            # Пробрасываем наши собственные исключения дальше без изменений
            raise
        except Exception as e:
            # Все остальные исключения оборачиваем в AudioExtractionError
            raise AudioExtractionError(f"Непредвиденная ошибка при получении информации об аудиофайле {audio_path}: {e}") from e
    
    @staticmethod
    def get_audio_info_safe(audio_path: str) -> Dict[str, Any]:
        """
        Безопасная версия get_audio_info, которая никогда не бросает исключения
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Словарь с информацией об аудиофайле или пустой словарь при ошибке
        """
        try:
            return AudioInfoExtractor.get_audio_info(audio_path)
        except Exception as e:
            # Возвращаем минимальную информацию о файле
            path_obj = Path(audio_path)
            return {
                'title': path_obj.stem,
                'artist': '',
                'album': '',
                'duration': 0,
                'sample_rate': 0,
                'channels': 0,
                'bitrate': 0,
                'file_size': 0,
                'file_format': path_obj.suffix.lower(),
                'path': str(path_obj),
                'filename': path_obj.name,
                'stem': path_obj.stem,
                'duration_formatted': '00:00',
                'file_size_formatted': '0 B',
                'error': str(e)
            }
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Форматирование продолжительности в ЧЧ:ММ:СС"""
        if seconds <= 0:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _format_file_size(bytes_size: int) -> str:
        """Форматирование размера файла"""
        if bytes_size <= 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    
    @staticmethod
    def get_waveform_data(audio_path: str, num_points: int = 100) -> np.ndarray:
        """
        Получение данных для визуализации аудиоволны
        
        Args:
            audio_path: Путь к аудиофайлу
            num_points: Количество точек для визуализации
            
        Returns:
            Массив с данными волны
            
        Raises:
            AudioFileError: Если файл не найден или нет доступа
            AudioWaveformError: Если возникла ошибка при получении данных волны
            AudioExtractionError: Если возникла другая ошибка
        """
        try:
            # Проверяем существование файла
            path_obj = Path(audio_path)
            if not path_obj.exists():
                raise AudioFileError(f"Файл не найден: {audio_path}")
            
            if not path_obj.is_file():
                raise AudioFileError(f"Путь не является файлом: {audio_path}")
            
            # Читаем аудиофайл
            try:
                audio_data, sample_rate = sf.read(audio_path, always_2d=False)
            except sf.LibsndfileError as e:
                raise AudioWaveformError(f"Ошибка чтения аудиофайла: {e}") from e
            except (FileNotFoundError, PermissionError) as e:
                raise AudioFileError(f"Ошибка доступа к файлу: {e}") from e
            
            # Если многоканальное, преобразуем в моно
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Сжимаем данные для визуализации
            if len(audio_data) > num_points:
                step = len(audio_data) // num_points
                compressed = []
                for i in range(0, len(audio_data), step):
                    chunk = audio_data[i:min(i+step, len(audio_data))]
                    if len(chunk) > 0:
                        compressed.append(np.max(np.abs(chunk)))
                    if len(compressed) >= num_points:
                        break
                waveform = np.array(compressed[:num_points])
            else:
                waveform = np.abs(audio_data)
            
            # Нормализуем
            if waveform.max() > 0:
                waveform = waveform / waveform.max()
            
            return waveform
            
        except (AudioFileError, AudioWaveformError):
            # Пробрасываем наши собственные исключения дальше
            raise
        except MemoryError as e:
            raise AudioWaveformError(f"Недостаточно памяти для обработки файла: {e}") from e
        except Exception as e:
            raise AudioExtractionError(f"Непредвиденная ошибка при получении данных волны: {e}") from e
    
    @staticmethod
    def get_waveform_data_safe(audio_path: str, num_points: int = 100) -> np.ndarray:
        """
        Безопасная версия get_waveform_data, которая никогда не бросает исключения
        
        Args:
            audio_path: Путь к аудиофайлу
            num_points: Количество точек для визуализации
            
        Returns:
            Массив с данными волны или нулевой массив при ошибке
        """
        try:
            return AudioInfoExtractor.get_waveform_data(audio_path, num_points)
        except Exception:
            # Возвращаем нулевой массив при любой ошибке
            return np.zeros(num_points)
    
    @staticmethod
    def get_basic_audio_info(audio_path: str) -> Dict[str, Any]:
        """
        Получение только базовой информации об аудиофайле (без метаданных)
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Словарь с базовой информацией
            
        Raises:
            AudioFileError: Если файл не найден или нет доступа
            AudioExtractionError: Если возникла другая ошибка
        """
        try:
            path_obj = Path(audio_path)
            
            if not path_obj.exists():
                raise AudioFileError(f"Файл не найден: {audio_path}")
            
            try:
                file_stat = path_obj.stat()
                file_size = file_stat.st_size
            except PermissionError as e:
                raise AudioFileError(f"Нет доступа к файлу: {audio_path}") from e
            
            info = {
                'filename': path_obj.name,
                'stem': path_obj.stem,
                'file_size': file_size,
                'file_format': path_obj.suffix.lower(),
                'file_size_formatted': AudioInfoExtractor._format_file_size(file_size)
            }
            
            # Пробуем получить информацию о длительности
            try:
                with sf.SoundFile(audio_path) as audio_file:
                    info['duration'] = len(audio_file) / audio_file.samplerate
                    info['sample_rate'] = audio_file.samplerate
                    info['channels'] = audio_file.channels
                    info['duration_formatted'] = AudioInfoExtractor._format_duration(info['duration'])
            except sf.LibsndfileError as e:
                # Если не удалось прочитать аудио, оставляем нулевые значения
                info['duration'] = 0
                info['sample_rate'] = 0
                info['channels'] = 0
                info['duration_formatted'] = '00:00'
            except (FileNotFoundError, PermissionError) as e:
                # Этот случай уже должен быть обработан выше, но для безопасности
                raise AudioFileError(f"Ошибка доступа к файлу: {e}") from e
            
            return info
            
        except AudioFileError:
            raise
        except Exception as e:
            raise AudioExtractionError(f"Непредвиденная ошибка при получении базовой информации: {e}") from e

