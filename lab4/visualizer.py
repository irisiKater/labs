import matplotlib.pyplot as plt
import pandas as pd


def plot_amplitude_visualization(df: pd.DataFrame, plot_type: str = 'scatter') -> plt.Figure:
    """
    Построение графика амплитуды
    
    Args:
        df: DataFrame с данными
        plot_type: Тип графика
        
    Returns:
        Объект Figure с графиком
    """
    if 'max_amplitude' not in df.columns:
        raise ValueError("DataFrame должен содержать колонку 'max_amplitude'")
    
    plt.figure(figsize=(14, 8))
    
    if plot_type == 'scatter':
        # Точечный график: номер файла vs амплитуда
        plt.subplot(2, 2, (1, 2))
        x = range(len(df))
        y = df['max_amplitude']
        
        plt.scatter(x, y, alpha=0.7, s=40, color='royalblue', 
                   edgecolor='navy', linewidth=0.5)
        plt.title('Максимальная амплитуда аудиофайлов', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Номер файла в отсортированном списке', fontsize=12)
        plt.ylabel('Максимальная амплитуда', fontsize=12)
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # Гистограмма распределения амплитуд
        plt.subplot(2, 2, 3)
        plt.hist(y, bins=30, alpha=0.7, color='mediumseagreen', 
                edgecolor='darkgreen')
        plt.title('Распределение амплитуд', fontsize=12)
        plt.xlabel('Максимальная амплитуда', fontsize=11)
        plt.ylabel('Количество файлов', fontsize=11)
        plt.grid(True, alpha=0.3)
        
        # Box plot
        plt.subplot(2, 2, 4)
        plt.boxplot(y, vert=True, patch_artist=True, 
                   boxprops=dict(facecolor='lightcoral'),
                   medianprops=dict(color='red', linewidth=2))
        plt.title('Box plot амплитуд', fontsize=12)
        plt.ylabel('Максимальная амплитуда', fontsize=11)
        plt.grid(True, alpha=0.3)
        
    elif plot_type == 'histogram':
        if 'amplitude_range' not in df.columns:
            raise ValueError("Для histogram требуется колонка 'amplitude_range'")
        
        # Гистограмма по диапазонам
        range_counts = df['amplitude_range'].value_counts().sort_index()
        
        plt.bar(range(range_counts.shape[0]), range_counts.values, 
               color='skyblue', edgecolor='black', alpha=0.8)
        
        plt.title('Распределение файлов по диапазонам амплитуды', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Диапазон амплитуды', fontsize=12)
        plt.ylabel('Количество файлов', fontsize=12)
        
        # Устанавливаем метки на оси X
        plt.xticks(range(range_counts.shape[0]), range_counts.index, 
                  rotation=45, ha='right')
        
        # Добавляем значения на столбцы
        for i, v in enumerate(range_counts.values):
            plt.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=10)
        
        plt.grid(True, alpha=0.3, axis='y')
    else:
        raise ValueError(f"Неизвестный тип графика: {plot_type}")
    
    plt.tight_layout()
    return plt