import matplotlib.pyplot as plt

from arg_parser import parse_arguments
from data_loader import create_dataframe_from_annotation
from data_processor import (
    add_max_amplitude_column, 
    sort_by_amplitude, 
    filter_by_amplitude, 
    create_amplitude_ranges
)
from file_saver import save_results
from visualizer import plot_amplitude_visualization


def main() -> None:
    """
    Основная функция программы
    """
    print("=" * 70)
    print("ЛАБОРАТОРНАЯ РАБОТА №2 - АНАЛИЗ АУДИОФАЙЛОВ")
    print("=" * 70)
    
    try:
        # Шаг 1: Парсинг аргументов
        args = parse_arguments()
        
        # Шаг 2: Проверяем наличие soundfile
        try:
            import soundfile as sf
            print("✓ Библиотека soundfile доступна")
        except ImportError:
            print("✗ Ошибка: библиотека soundfile не установлена")
            print("Установите ее командой: pip install soundfile")
            print("Для работы с MP3 также нужен: pip install pysoundfile")
            return
        
        # Шаг 3: Загрузка данных
        df = create_dataframe_from_annotation(args['annotation_path'])
        if df is None or len(df) == 0:
            print("Нет данных для анализа")
            return
        
        # Шаг 4: Добавление колонки с максимальной амплитудой
        df = add_max_amplitude_column(df)
        if len(df) == 0:
            print("Нет данных для анализа после обработки амплитуд")
            return
        
        # Шаг 5: Сортировка
        sorted_df = sort_by_amplitude(df, ascending=False)
        
        # Шаг 6: Фильтрация
        filtered_df = filter_by_amplitude(
            sorted_df, 
            min_amp=args['filter_min'], 
            max_amp=args['filter_max']
        )
        
        # Шаг 7: Создание диапазонов (для гистограммы)
        if args['plot_type'] == 'histogram':
            final_df = create_amplitude_ranges(filtered_df, bins=args['bins'])
        else:
            final_df = filtered_df
        
        # Шаг 8: Визуализация
        plot = plot_amplitude_visualization(final_df, plot_type=args['plot_type'])
        
        # Шаг 9: Сохранение результатов
        save_results(final_df, plot, args['output_folder'])
        
        # Показываем график
        plt.show()
        
        print("\n" + "=" * 70)
        print("ВЫПОЛНЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("=" * 70)
        
    except FileNotFoundError as e:
        print(f"\n✗ Ошибка: Файл не найден - {e}")
    except PermissionError as e:
        print(f"\n✗ Ошибка: Проблема с правами доступа - {e}")
    except ValueError as e:
        print(f"\n✗ Ошибка: Неверные данные - {e}")
    except RuntimeError as e:
        print(f"\n✗ Ошибка выполнения: {e}")
    except Exception as e:
        print(f"\n✗ Неизвестная ошибка: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Примеры запуска:
    # python main.py --annotation "путь/к/annotation.csv"
    # python main.py --annotation "annotation.csv" --plot-type histogram --bins 7
    # python main.py -a "annotation.csv" -o "my_results" -p scatter
    
    main()