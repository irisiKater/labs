import pandas as pd
from pathlib import Path
from typing import Iterator, Tuple, Optional, Dict, Any


class AudioDatasetIterator:
    """
    Итератор для аудиофайлов из датасета
    """
    
    def __init__(self, annotation_path: Optional[Path] = None, 
                 dataset_dir: Optional[Path] = None):
        """
        Инициализация итератора
        
        Args:
            annotation_path: Путь к файлу аннотации
            dataset_dir: Путь к папке с датасетом
        """
        self.annotation_path = annotation_path
        self.dataset_dir = dataset_dir
        self.current_index = 0
        self.dataframe = None
        self.audio_files = []
        
        if annotation_path:
            self._load_from_annotation()
        elif dataset_dir:
            self._load_from_directory()
    
    def _load_from_annotation(self) -> None:
        """Загрузка данных из файла аннотации"""
        try:
            self.dataframe = pd.read_csv(self.annotation_path, encoding='utf-8')
            print(f"Загружено {len(self.dataframe)} записей из аннотации")
            
            # Получаем пути к аудиофайлам
            if 'absolute_path' in self.dataframe.columns:
                self.audio_files = self.dataframe['absolute_path'].tolist()
            elif 'relative_path' in self.dataframe.columns:
                self.audio_files = self.dataframe['relative_path'].tolist()
            else:
                raise ValueError("Файл аннотации должен содержать колонку 'absolute_path' или 'relative_path'")
                
        except Exception as e:
            raise RuntimeError(f"Ошибка при загрузке аннотации: {e}")
    
    def _load_from_directory(self) -> None:
        """Загрузка данных из директории"""
        try:
            # Ищем все аудиофайлы в директории и поддиректориях
            audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'}
            self.audio_files = []
            
            for ext in audio_extensions:
                audio_files = list(self.dataset_dir.rglob(f'*{ext}'))
                self.audio_files.extend([str(f) for f in audio_files])
            
            print(f"Найдено {len(self.audio_files)} аудиофайлов в директории")
            
            # Создаем простой DataFrame для совместимости
            self.dataframe = pd.DataFrame({
                'file_path': self.audio_files,
                'filename': [Path(f).name for f in self.audio_files]
            })
            
        except Exception as e:
            raise RuntimeError(f"Ошибка при загрузке директории: {e}")
    
    def __iter__(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """Возвращает итератор"""
        return self
    
    def __next__(self) -> Tuple[str, Dict[str, Any]]:
        """Получение следующего аудиофайла"""
        if self.current_index >= len(self.audio_files):
            raise StopIteration
        
        audio_path = self.audio_files[self.current_index]
        metadata = self._get_metadata(self.current_index)
        self.current_index += 1
        
        return audio_path, metadata
    
    def __len__(self) -> int:
        """Количество аудиофайлов"""
        return len(self.audio_files)
    
    def reset(self) -> None:
        """Сброс итератора"""
        self.current_index = 0
    
    def get_current(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Получение текущего элемента"""
        if self.current_index >= len(self.audio_files):
            return None
        
        audio_path = self.audio_files[self.current_index]
        metadata = self._get_metadata(self.current_index)
        
        return audio_path, metadata
    
    def next(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Получение следующего элемента без остановки итератора"""
        if self.current_index >= len(self.audio_files):
            return None
        
        result = self.get_current()
        self.current_index += 1
        return result
    
    def previous(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Получение предыдущего элемента"""
        if self.current_index <= 1:  # 1 потому что current_index указывает на следующий
            return None
        
        self.current_index -= 2  # Возвращаемся на два шага назад
        if self.current_index < 0:
            self.current_index = 0
            
        return self.get_current()
    
    def _get_metadata(self, index: int) -> Dict[str, Any]:
        """Получение метаданных для файла"""
        metadata = {
            'filename': Path(self.audio_files[index]).name,
            'file_path': self.audio_files[index],
            'index': index,
            'total': len(self.audio_files)
        }
        
        # Добавляем дополнительные метаданные из DataFrame если они есть
        if self.dataframe is not None and index < len(self.dataframe):
            row = self.dataframe.iloc[index]
            for col in self.dataframe.columns:
                if col not in metadata and col not in ['absolute_path', 'relative_path']:
                    metadata[col] = row[col]
        
        return metadata
    
    def get_by_index(self, index: int) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Получение элемента по индексу"""
        if 0 <= index < len(self.audio_files):
            old_index = self.current_index
            self.current_index = index
            result = self.get_current()
            self.current_index = old_index
            return result
        return None