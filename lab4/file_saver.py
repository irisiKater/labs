from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt



def save_results(df: pd.DataFrame, plot: plt.Figure, output_folder: Path) -> None:
    """
    Сохранение результатов анализа
    
    Args:
        df: DataFrame с результатами
        plot: Объект Figure с графиком
        output_folder: Папка для сохранения
        
    Raises:
        PermissionError: Если нет прав на запись
        OSError: При других ошибках файловой системы
    """
    try:
        # Создаем папку для результатов
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # 1. Сохраняем DataFrame в CSV
        csv_path = output_folder / 'audio_analysis.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"\nDataFrame сохранен: {csv_path}")
        
        # 2. Сохраняем график
        plot_path = output_folder / 'amplitude_analysis.png'
        plot.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"График сохранен: {plot_path}")
        
        # 3. Создаем отчет со статистикой
        save_analysis_report(df, output_folder)
        
        print(f"\nВсе файлы сохранены в папке: {output_folder.absolute()}")
        
    except PermissionError as e:
        raise PermissionError(f"Нет прав на запись в папку {output_folder}: {e}")
    except Exception as e:
        raise OSError(f"Ошибка при сохранении результатов: {e}")


def save_analysis_report(df: pd.DataFrame, output_folder: Path) -> None:
    """
    Создание текстового отчета с анализом
    
    Args:
        df: DataFrame с результатами
        output_folder: Папка для сохранения
    """
    report_path = output_folder / 'analysis_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("ОТЧЕТ ПО АНАЛИЗУ АУДИОФАЙЛОВ\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Общее количество файлов: {len(df)}\n")
        
        # Анализ форматов файлов
        if 'filename' in df.columns:
            file_extensions = df['filename'].apply(
                lambda x: Path(x).suffix.lower()
            ).value_counts()
            f.write(f"Формат файлов:\n{file_extensions.to_string()}\n\n")
        
        f.write("СТАТИСТИКА ПО МАКСИМАЛЬНОЙ АМПЛИТУДЕ:\n")
        f.write("-" * 40 + "\n")
        
        if 'max_amplitude' in df.columns:
            amp_data = df['max_amplitude']
            f.write(f"Минимальная амплитуда: {amp_data.min():.6f}\n")
            f.write(f"Максимальная амплитуда: {amp_data.max():.6f}\n")
            f.write(f"Средняя амплитуда: {amp_data.mean():.6f}\n")
            f.write(f"Медианная амплитуда: {amp_data.median():.6f}\n")
            f.write(f"Стандартное отклонение: {amp_data.std():.6f}\n\n")
        
        f.write("ТОП-5 ФАЙЛОВ ПО АМПЛИТУДЕ:\n")
        f.write("-" * 40 + "\n")
        
        if 'max_amplitude' in df.columns and 'filename' in df.columns:
            top_files = df.sort_values('max_amplitude', ascending=False).head()
            for i, (_, row) in enumerate(top_files.iterrows(), 1):
                f.write(f"{i}. {row['filename']}\n")
                f.write(f"   Амплитуда: {row['max_amplitude']:.6f}\n")
    
    print(f"Отчет сохранен: {report_path}")