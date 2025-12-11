import pandas as pd
from pathlib import Path
from typing import Optional


def create_dataframe_from_annotation(annotation_csv_path: Path) -> Optional[pd.DataFrame]:
    """
    Создание DataFrame из аннотационного CSV-файла
    
    Args:
        annotation_csv_path: Путь к CSV-файлу
        
    Returns:
        DataFrame с данными или None в случае ошибки
        
    Raises:
        FileNotFoundError: Если файл не существует
        ValueError: Если файл имеет неверный формат
    """
    try:
        if not annotation_csv_path.exists():
            raise FileNotFoundError(f"Файл аннотации не найден: {annotation_csv_path}")
        
        df = pd.read_csv(annotation_csv_path, encoding='utf-8')
        print(f"Загружено {len(df)} записей из аннотации")
        
        # Проверка необходимых колонок
        required_columns = ['absolute_path', 'relative_path']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
        
        # Создаем DataFrame с нужными колонками
        result_df = pd.DataFrame({
            'absolute_path': df['absolute_path'],
            'relative_path': df['relative_path'],
            'filename': df['absolute_path'].apply(lambda x: Path(x).name)
        })
        
        print(f"\nПервые 5 файлов:")
        for i, row in result_df.head().iterrows():
            print(f"  {i+1}. {row['filename']}")
        
        return result_df
        
    except FileNotFoundError as e:
        print(f"Ошибка: {e}")
        raise
    except Exception as e:
        error_msg = f"Ошибка при чтении CSV: {str(e)}"
        print(f"Ошибка: {error_msg}")
        raise RuntimeError(error_msg) from e