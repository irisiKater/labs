import pandas as pd
from typing import Optional

from audio_processor import calculate_max_amplitude_soundfile


def sort_by_amplitude(df: pd.DataFrame, ascending: bool = False) -> pd.DataFrame:
    """
    Сортировка DataFrame по максимальной амплитуде
    
    Args:
        df: DataFrame для сортировки
        ascending: Направление сортировки
        
    Returns:
        Отсортированный DataFrame
    """
    sort_direction = "возрастанию" if ascending else "убыванию"
    print(f"\nСортировка по {sort_direction} максимальной амплитуды...")
    
    sorted_df = df.sort_values(by='max_amplitude', ascending=ascending)
    
    print(f"\nТоп-10 файлов после сортировки:")
    for i, (_, row) in enumerate(sorted_df.head(10).iterrows(), 1):
        print(f"{i:2}. {row['filename'][:35]:35} → Амплитуда: {row['max_amplitude']:.6f}")
    
    return sorted_df


def add_max_amplitude_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавление колонки с максимальной амплитудой
    
    Args:
        df: DataFrame с путями к аудиофайлам
        
    Returns:
        DataFrame с добавленной колонкой max_amplitude
    """
    print("\n" + "="*60)
    print("ВЫЧИСЛЕНИЕ МАКСИМАЛЬНОЙ АМПЛИТУДЫ ДЛЯ АУДИОФАЙЛОВ")
    print("="*60)
    
    # Применяем функцию вычисления амплитуды ко всем файлам
    df['max_amplitude'] = df['absolute_path'].apply(calculate_max_amplitude_soundfile)
    
    # Удаляем строки, где не удалось вычислить амплитуду
    original_count = len(df)
    df = df.dropna(subset=['max_amplitude'])
    final_count = len(df)
    
    print(f"\nУспешно обработано: {final_count} из {original_count} файлов")
    
    if final_count > 0:
        # Выводим статистику
        amp_data = df['max_amplitude']
        print(f"Диапазон амплитуд: от {amp_data.min():.6f} до {amp_data.max():.6f}")
        print(f"Средняя амплитуда: {amp_data.mean():.6f}")
        print(f"Медианная амплитуда: {amp_data.median():.6f}")
        print(f"Стандартное отклонение: {amp_data.std():.6f}")
    
    return df


def filter_by_amplitude(df: pd.DataFrame, 
                       min_amp: Optional[float] = None, 
                       max_amp: Optional[float] = None) -> pd.DataFrame:
    """
    Фильтрация по диапазону амплитуды
    
    Args:
        df: DataFrame для фильтрации
        min_amp: Минимальная амплитуда
        max_amp: Максимальная амплитуда
        
    Returns:
        Отфильтрованный DataFrame
    """
    filtered = df.copy()
    
    conditions = []
    if min_amp is not None:
        filtered = filtered[filtered['max_amplitude'] >= min_amp]
        conditions.append(f"≥ {min_amp:.4f}")
    
    if max_amp is not None:
        filtered = filtered[filtered['max_amplitude'] <= max_amp]
        conditions.append(f"≤ {max_amp:.4f}")
    
    condition_str = " и ".join(conditions) if conditions else "без фильтра"
    
    print(f"\nФильтрация амплитуды ({condition_str}):")
    print(f"  Найдено: {len(filtered)} из {len(df)} файлов")
    
    if len(filtered) > 0:
        print("  Примеры отфильтрованных файлов:")
        for i, (_, row) in enumerate(filtered.head(5).iterrows(), 1):
            print(f"    {i}. {row['filename'][:30]:30} → {row['max_amplitude']:.6f}")
    
    return filtered


def create_amplitude_ranges(df: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """
    Создание колонки с диапазонами амплитуды для гистограммы
    
    Args:
        df: DataFrame с данными
        bins: Количество диапазонов
        
    Returns:
        DataFrame с добавленной колонкой amplitude_range
    """
    if 'max_amplitude' not in df.columns:
        raise ValueError("DataFrame должен содержать колонку 'max_amplitude'")
    
    # Создаем диапазоны
    ranges = pd.cut(df['max_amplitude'], bins=bins, precision=4)
    
    # Создаем читаемые метки
    range_labels = []
    for interval in ranges.cat.categories:
        lower = round(interval.left, 4)
        upper = round(interval.right, 4)
        range_labels.append(f"{lower:.4f}-{upper:.4f}")
    
    # Применяем метки
    df['amplitude_range'] = pd.cut(df['max_amplitude'], bins=bins, labels=range_labels)
    
    print(f"\nСоздано {bins} диапазонов амплитуды:")
    for label, count in df['amplitude_range'].value_counts().sort_index().items():
        print(f"  {label}: {count} файлов")
    
    return df