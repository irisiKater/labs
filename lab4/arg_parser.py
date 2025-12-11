import argparse
from pathlib import Path
from typing import Dict, Any


def parse_arguments() -> Dict[str, Any]:
    """
    Парсинг аргументов командной строки
    
    Returns:
        Dict[str, Any]: Словарь с аргументами
    """
    parser = argparse.ArgumentParser(
        description='Анализ аудиофайлов: вычисление максимальной амплитуды'
    )
    
    parser.add_argument(
        '--annotation', '-a',
        required=True,
        type=str,
        help='Путь к CSV-файлу аннотации (annotation.csv)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='lab4_results',
        help='Папка для сохранения результатов (по умолчанию: lab4_results)'
    )
    
    parser.add_argument(
        '--plot-type', '-p',
        choices=['scatter', 'histogram'],
        default='scatter',
        help='Тип графика: scatter или histogram'
    )
    
    parser.add_argument(
        '--bins', '-b',
        type=int,
        default=5,
        help='Количество диапазонов для гистограммы'
    )
    
    parser.add_argument(
        '--filter-min',
        type=float,
        default=0.1,
        help='Минимальная амплитуда для фильтрации'
    )
    
    parser.add_argument(
        '--filter-max',
        type=float,
        help='Максимальная амплитуда для фильтрации'
    )
    
    args = parser.parse_args()
    
    # Возвращаем словарь с аргументами
    return {
        'annotation_path': Path(args.annotation),
        'output_folder': Path(args.output),
        'plot_type': args.plot_type,
        'bins': args.bins,
        'filter_min': args.filter_min,
        'filter_max': args.filter_max
    }