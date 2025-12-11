from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf


def calculate_max_amplitude_soundfile(audio_file_path: str) -> Optional[float]:
    """
    Вычисление максимальной амплитуды с использованием soundfile
    
    Args:
        audio_file_path: Путь к аудиофайлу (строка)
        
    Returns:
        Максимальная амплитуда или None в случае ошибки
        
    Raises:
        FileNotFoundError: Если файл не существует
        RuntimeError: Если произошла ошибка при чтении файла
    """
    try:
        # Преобразуем строку в Path для проверки существования
        path_obj = Path(audio_file_path)
        
        # Проверка существования файла
        if not path_obj.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_file_path}")
        
        # Читаем аудиофайл с помощью soundfile
        audio_data, sample_rate = sf.read(audio_file_path, always_2d=False)
        
        # Если аудио многоканальное, преобразуем в моно
        if audio_data.ndim > 1:
            # Среднее по каналам для преобразования в моно
            audio_data = np.mean(audio_data, axis=1)
        
        # Вычисляем максимальную амплитуду по модулю
        max_amplitude = np.max(np.abs(audio_data))
        
        # Получаем имя файла
        filename = path_obj.name
        
        # Дополнительная информация для отладки
        print(f"  {filename:30} → "
              f"Амплитуда: {max_amplitude:.6f}, "
              f"Длина: {len(audio_data)}, "
              f"Формат: {audio_data.dtype}")
        
        return round(float(max_amplitude), 6)
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        raise
    except Exception as e:
        filename = Path(audio_file_path).name if isinstance(audio_file_path, str) else "unknown"
        error_msg = f"Ошибка при обработке {filename}: {str(e)}"
        print(f"Ошибка: {error_msg}")
        raise RuntimeError(error_msg) from e