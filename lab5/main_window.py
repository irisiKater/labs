import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog,
                            QMessageBox, QSlider, QGroupBox,
                            QFormLayout, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import numpy as np

from dataset_iterator import AudioDatasetIterator
from audio_info_extractor import AudioInfoExtractor, AudioExtractionError


class WaveformWidget(QWidget):
    """Виджет для отображения аудиоволны"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = np.array([])
        self.current_position = 0
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        
        # Настройка цвета
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
    
    def set_waveform_data(self, data):
        """Установка данных волны"""
        if data is not None and isinstance(data, (list, np.ndarray)) and len(data) > 0:
            self.waveform_data = np.array(data)
        else:
            self.waveform_data = np.array([])
        self.update()
    
    def set_position(self, position):
        """Установка текущей позиции воспроизведения"""
        self.current_position = max(0.0, min(1.0, position))
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка волны"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
        # Фон
        painter.fillRect(self.rect(), QColor(40, 40, 40))
    
        # Проверяем массив на пустоту
        if self.waveform_data is None or len(self.waveform_data) == 0:
            # Рисуем заглушку
            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных волны")
            return
        
        # Рисуем волну
        width = self.width()
        height = self.height()
        num_points = len(self.waveform_data)
        
        if num_points == 0:
            return
        
        # Линия прогресса
        progress_x = int(self.current_position * width)
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DotLine))
        painter.drawLine(progress_x, 0, progress_x, height)
        
        # Волна
        step = width / num_points
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        
        for i in range(num_points - 1):
            x1 = int(i * step)
            x2 = int((i + 1) * step)
            y1 = height // 2 - int(self.waveform_data[i] * height // 3)
            y2 = height // 2 - int(self.waveform_data[i + 1] * height // 3)
            
            painter.drawLine(x1, y1, x2, y2)
        
        # Зеркальная часть волны
        painter.setPen(QPen(QColor(0, 150, 255, 100), 1))
        for i in range(num_points - 1):
            x1 = int(i * step)
            x2 = int((i + 1) * step)
            y1 = height // 2 + int(self.waveform_data[i] * height // 3)
            y2 = height // 2 + int(self.waveform_data[i + 1] * height // 3)
            
            painter.drawLine(x1, y1, x2, y2)


class AudioPlayerWindow(QMainWindow):
    """Главное окно аудиоплеера"""
    
    def __init__(self):
        super().__init__()
        self.dataset_iterator = None
        self.current_audio_info = None
        self.waveform_data = np.array([])
        
        # Инициализация медиаплеера
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Таймер для обновления прогресса
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Аудио Датсет Просмотрщик")
        self.setGeometry(100, 100, 900, 700)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Панель управления
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Разделитель
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Верхняя панель - информация об аудио
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)
        
        # Нижняя панель - управление воспроизведением
        player_panel = self.create_player_panel()
        splitter.addWidget(player_panel)
        
        splitter.setSizes([400, 200])
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов к работе")
    
    def create_control_panel(self) -> QWidget:
        """Создание панели управления"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Кнопки загрузки
        self.btn_load_annotation = QPushButton("Загрузить аннотацию (CSV)")
        self.btn_load_annotation.clicked.connect(self.load_annotation)
        self.btn_load_annotation.setMinimumHeight(40)
        
        self.btn_load_folder = QPushButton("Загрузить папку с аудио")
        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_load_folder.setMinimumHeight(40)
        
        layout.addWidget(self.btn_load_annotation)
        layout.addWidget(self.btn_load_folder)
        
        # Информация о загрузке
        self.lbl_dataset_info = QLabel("Датасет не загружен")
        self.lbl_dataset_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_dataset_info)
        
        return panel
    
    def create_info_panel(self) -> QWidget:
        """Создание панели информации"""
        panel = QGroupBox("Информация о аудиофайле")
        layout = QVBoxLayout(panel)
        
        # Название файла и композиции
        self.lbl_filename = QLabel("Файл: Не загружено")
        self.lbl_filename.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_filename.setStyleSheet("color: #3498db;")
        layout.addWidget(self.lbl_filename)
        
        self.lbl_title = QLabel("Название: Неизвестно")
        self.lbl_title.setFont(QFont("Arial", 11))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        # Исполнитель и альбом
        artist_layout = QHBoxLayout()
        self.lbl_artist = QLabel("Исполнитель: Неизвестно")
        self.lbl_artist.setFont(QFont("Arial", 11))
        artist_layout.addWidget(self.lbl_artist)
        
        self.lbl_album = QLabel("Альбом: Неизвестно")
        self.lbl_album.setFont(QFont("Arial", 11))
        artist_layout.addWidget(self.lbl_album)
        
        layout.addLayout(artist_layout)
        
        # Детальная информация - два столбца
        info_group = QGroupBox("Техническая информация")
        info_layout = QHBoxLayout(info_group)
        
        # Левый столбец
        left_column = QFormLayout()
        self.lbl_duration = QLabel("00:00")
        self.lbl_file_size = QLabel("0 B")
        self.lbl_format = QLabel("Неизвестно")
        self.lbl_sample_rate = QLabel("0 Hz")
        
        left_column.addRow("Продолжительность:", self.lbl_duration)
        left_column.addRow("Размер файла:", self.lbl_file_size)
        left_column.addRow("Формат файла:", self.lbl_format)
        left_column.addRow("Частота дискретизации:", self.lbl_sample_rate)
        
        # Правый столбец
        right_column = QFormLayout()
        self.lbl_channels = QLabel("0")
        self.lbl_bitrate = QLabel("0 kbps")
        self.lbl_file_extension = QLabel("Неизвестно")
        self.lbl_stem = QLabel("Неизвестно")
        
        right_column.addRow("Количество каналов:", self.lbl_channels)
        right_column.addRow("Битрейт:", self.lbl_bitrate)
        right_column.addRow("Расширение:", self.lbl_file_extension)
        right_column.addRow("Имя файла (без расширения):", self.lbl_stem)
        
        info_layout.addLayout(left_column)
        info_layout.addLayout(right_column)
        layout.addWidget(info_group)
        
        # Путь к файлу
        self.txt_file_path = QTextEdit()
        self.txt_file_path.setMaximumHeight(80)
        self.txt_file_path.setReadOnly(True)
        self.txt_file_path.setText("Путь к файлу: Не загружено")
        self.txt_file_path.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 5px;
            }
        """)
        layout.addWidget(self.txt_file_path)
        
        # Метаданные (если есть)
        self.lbl_metadata = QLabel("Метаданные: нет")
        self.lbl_metadata.setFont(QFont("Arial", 10))
        self.lbl_metadata.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_metadata)
        
        return panel
    
    def create_player_panel(self) -> QWidget:
        """Создание панели управления воспроизведением"""
        panel = QGroupBox("Воспроизведение")
        layout = QVBoxLayout(panel)
        
        # Виджет волны
        self.waveform_widget = WaveformWidget()
        layout.addWidget(self.waveform_widget)
        
        # Прогресс бар
        self.progress_bar = QSlider(Qt.Orientation.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1000)
        self.progress_bar.valueChanged.connect(self.seek_audio)
        layout.addWidget(self.progress_bar)
        
        # Время
        time_layout = QHBoxLayout()
        self.lbl_current_time = QLabel("00:00")
        self.lbl_total_time = QLabel("00:00")
        time_layout.addWidget(self.lbl_current_time)
        time_layout.addStretch()
        time_layout.addWidget(self.lbl_total_time)
        layout.addLayout(time_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.btn_previous = QPushButton("◀◀ Назад")
        self.btn_previous.clicked.connect(self.previous_audio)
        self.btn_previous.setMinimumWidth(100)
        self.btn_previous.setEnabled(False)
        
        self.btn_play_pause = QPushButton("▶ Воспроизвести")
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_play_pause.setMinimumWidth(120)
        self.btn_play_pause.setEnabled(False)
        
        self.btn_stop = QPushButton("⏹ Стоп")
        self.btn_stop.clicked.connect(self.stop_audio)
        self.btn_stop.setMinimumWidth(80)
        self.btn_stop.setEnabled(False)
        
        self.btn_next = QPushButton("Вперед ▶▶")
        self.btn_next.clicked.connect(self.next_audio)
        self.btn_next.setMinimumWidth(100)
        self.btn_next.setEnabled(False)
        
        button_layout.addWidget(self.btn_previous)
        button_layout.addWidget(self.btn_play_pause)
        button_layout.addWidget(self.btn_stop)
        button_layout.addWidget(self.btn_next)
        
        layout.addLayout(button_layout)
        
        # Информация о позиции в датасете
        position_layout = QHBoxLayout()
        position_layout.addStretch()
        self.lbl_position = QLabel("Позиция: 0 / 0")
        self.lbl_position.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_position.setStyleSheet("color: #2c3e50;")
        position_layout.addWidget(self.lbl_position)
        position_layout.addStretch()
        layout.addLayout(position_layout)
        
        return panel
    
    def connect_signals(self):
        """Подключение сигналов медиаплеера"""
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.errorOccurred.connect(self.on_player_error)
    
    def load_annotation(self):
        """Загрузка датасета из файла аннотации"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл аннотации (CSV)", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                self.dataset_iterator = AudioDatasetIterator(
                    annotation_path=Path(file_path)
                )
                
                if len(self.dataset_iterator) == 0:
                    QMessageBox.warning(self, "Внимание", "Аннотационный файл пуст или не содержит валидных данных")
                    self.lbl_dataset_info.setText("Датасет пуст")
                    return
                
                self.status_bar.showMessage(f"Загружено {len(self.dataset_iterator)} аудиофайлов")
                self.lbl_dataset_info.setText(f"Загружено: {len(self.dataset_iterator)} файлов")
                self.enable_player_controls(True)
                self.load_first_audio()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить аннотацию: {e}")
    
    def load_folder(self):
        """Загрузка датасета из папки"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку с аудиофайлами", 
            ""
        )
        
        if folder_path:
            try:
                self.dataset_iterator = AudioDatasetIterator(
                    dataset_dir=Path(folder_path)
                )
                
                if len(self.dataset_iterator) == 0:
                    QMessageBox.warning(self, "Внимание", "Папка не содержит аудиофайлов")
                    self.lbl_dataset_info.setText("Папка пуста")
                    return
                
                self.status_bar.showMessage(f"Загружено {len(self.dataset_iterator)} аудиофайлов")
                self.lbl_dataset_info.setText(f"Загружено: {len(self.dataset_iterator)} файлов")
                self.enable_player_controls(True)
                self.load_first_audio()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить папку: {e}")
    
    def load_first_audio(self):
        """Загрузка первого аудиофайла"""
        if self.dataset_iterator and len(self.dataset_iterator) > 0:
            try:
                self.dataset_iterator.reset()
                self.load_current_audio()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить первый файл: {e}")
    
    def load_current_audio(self):
        """Загрузка текущего аудиофайла"""
        if not self.dataset_iterator:
            return
        
        # Останавливаем текущее воспроизведение
        self.stop_audio()
        
        # Получаем текущий аудиофайл
        try:
            result = self.dataset_iterator.get_current()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить текущий файл: {e}")
            return
        
        # Исправленная проверка: избегаем булевой проверки массивов
        if result is None:
            self.show_empty_audio_info()
            return
        
        # Проверяем тип результата
        try:
            audio_path, metadata = result
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректный формат данных: {e}")
            return
        
        # Проверяем существование файла
        if not Path(audio_path).exists():
            QMessageBox.warning(self, "Ошибка", f"Файл не найден: {audio_path}")
            self.show_empty_audio_info()
            return
        
        # Проверяем, что файл не пустой
        if Path(audio_path).stat().st_size == 0:
            QMessageBox.warning(self, "Внимание", f"Файл пуст: {audio_path}")
            self.show_empty_audio_info()
            return
        
        try:
            # Загружаем информацию об аудио с безопасной версией
            try:
                self.current_audio_info = AudioInfoExtractor.get_audio_info(str(audio_path))
            except AudioExtractionError as e:
                QMessageBox.warning(self, "Внимание", f"Не удалось получить полную информацию об аудио: {e}")
                # Используем безопасную версию
                self.current_audio_info = AudioInfoExtractor.get_audio_info_safe(str(audio_path))
            
            # Получаем данные для волны с безопасной версией
            try:
                self.waveform_data = AudioInfoExtractor.get_waveform_data(str(audio_path), 200)
            except Exception:
                self.waveform_data = AudioInfoExtractor.get_waveform_data_safe(str(audio_path), 200)
            
            self.waveform_widget.set_waveform_data(self.waveform_data)
            
            # Устанавливаем аудио в медиаплеер
            self.media_player.setSource(QUrl.fromLocalFile(str(audio_path)))
            
            # Обновляем информацию в интерфейсе
            self.update_audio_info(metadata)
            
            # Обновляем позицию
            self.update_position_info()
            
            self.status_bar.showMessage(f"Загружен: {Path(audio_path).name}")
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить аудиофайл: {e}")
            self.show_empty_audio_info()
    
    def show_empty_audio_info(self):
        """Показать информацию о пустом/недоступном файле"""
        self.current_audio_info = None
        self.waveform_data = np.array([])
        self.waveform_widget.set_waveform_data([])
        
        # Сбрасываем информацию в интерфейсе
        self.lbl_filename.setText("Файл: Не удалось загрузить")
        self.lbl_title.setText("Название: Ошибка загрузки")
        self.lbl_artist.setText("Исполнитель: Неизвестно")
        self.lbl_album.setText("Альбом: Неизвестно")
        self.lbl_stem.setText("Неизвестно")
        self.lbl_format.setText("Неизвестно")
        self.lbl_file_extension.setText("Неизвестно")
        self.lbl_duration.setText("00:00")
        self.lbl_file_size.setText("0 B")
        self.lbl_sample_rate.setText("0 Hz")
        self.lbl_channels.setText("0")
        self.lbl_bitrate.setText("0 kbps")
        self.txt_file_path.setText("Путь к файлу: Неизвестно")
        self.lbl_metadata.setText("Метаданные: нет")
        self.lbl_total_time.setText("00:00")
        
        # Сбрасываем плеер
        self.media_player.setSource(QUrl())
    
    def update_audio_info(self, metadata):
        """Обновление информации об аудио"""
        if not self.current_audio_info:
            return
        
        # Основная информация о файле
        filename = self.current_audio_info.get('filename', 'Неизвестно')
        title = self.current_audio_info.get('title', filename)
        artist = self.current_audio_info.get('artist', 'Неизвестно')
        album = self.current_audio_info.get('album', 'Неизвестно')
        stem = self.current_audio_info.get('stem', 'Неизвестно')
        file_format = self.current_audio_info.get('file_format', 'Неизвестно')
        file_extension = Path(self.current_audio_info.get('path', '')).suffix or 'Неизвестно'
        
        self.lbl_filename.setText(f"Файл: {filename}")
        self.lbl_title.setText(f"Название: {title}")
        self.lbl_artist.setText(f"Исполнитель: {artist}")
        self.lbl_album.setText(f"Альбом: {album}")
        self.lbl_stem.setText(stem)
        self.lbl_format.setText(file_format)
        self.lbl_file_extension.setText(file_extension)
        
        # Техническая информация
        self.lbl_duration.setText(self.current_audio_info.get('duration_formatted', '00:00'))
        self.lbl_file_size.setText(self.current_audio_info.get('file_size_formatted', '0 B'))
        self.lbl_sample_rate.setText(f"{self.current_audio_info.get('sample_rate', 0)} Hz")
        self.lbl_channels.setText(str(self.current_audio_info.get('channels', 0)))
        
        bitrate = self.current_audio_info.get('bitrate', 0)
        self.lbl_bitrate.setText(f"{bitrate} kbps" if bitrate > 0 else "Неизвестно")
        
        # Путь к файлу
        file_path = self.current_audio_info.get('path', 'Неизвестно')
        self.txt_file_path.setText(f"Полный путь:\n{file_path}")
        
        # Метаданные из датасета
        if metadata:
            metadata_text = "Метаданные из датасета: "
            metadata_items = []
            for key, value in metadata.items():
                if key != 'audio_path':  # Пропускаем путь к аудио, он уже отображается
                    metadata_items.append(f"{key}: {value}")
            
            if metadata_items:
                self.lbl_metadata.setText(metadata_text + "; ".join(metadata_items))
            else:
                self.lbl_metadata.setText("Метаданные из датасета: нет")
        else:
            self.lbl_metadata.setText("Метаданные из датасета: нет")
        
        # Общее время для прогресс бара
        self.lbl_total_time.setText(self.current_audio_info.get('duration_formatted', '00:00'))
    
    def update_position_info(self):
        """Обновление информации о позиции"""
        if self.dataset_iterator:
            try:
                current_idx = self.dataset_iterator.current_index
                total = len(self.dataset_iterator)
                self.lbl_position.setText(f"Позиция: {current_idx + 1} / {total}")
            except:
                self.lbl_position.setText("Позиция: ? / ?")
    
    def next_audio(self):
        """Загрузка следующего аудиофайла"""
        if not self.dataset_iterator:
            return
        
        # Получаем следующий элемент
        try:
            result = self.dataset_iterator.next()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить следующий файл: {e}")
            return
        
        # Исправленная проверка: избегаем булевой проверки массивов
        if result is None:
            QMessageBox.information(self, "Информация", "Вы достигли конца датасета")
            return
        
        try:
            audio_path, metadata = result
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректный формат данных: {e}")
            return
        
        # Проверяем существование файла
        if not Path(audio_path).exists():
            QMessageBox.warning(self, "Ошибка", f"Файл не найден: {audio_path}")
            return
        
        try:
            self.stop_audio()
            self.current_audio_info = AudioInfoExtractor.get_audio_info(str(audio_path))
            self.waveform_data = AudioInfoExtractor.get_waveform_data(str(audio_path), 200)
            self.waveform_widget.set_waveform_data(self.waveform_data)
            self.media_player.setSource(QUrl.fromLocalFile(str(audio_path)))
            self.update_audio_info(metadata)
            self.update_position_info()
            self.status_bar.showMessage(f"Загружен следующий файл: {Path(audio_path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить следующий файл: {e}")
    
    def previous_audio(self):
        """Загрузка предыдущего аудиофайла"""
        if not self.dataset_iterator:
            return
        
        # Получаем предыдущий элемент
        try:
            result = self.dataset_iterator.previous()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить предыдущий файл: {e}")
            return
        
        # Исправленная проверка: избегаем булевой проверки массивов
        if result is None:
            QMessageBox.information(self, "Информация", "Вы достигли начала датасета")
            return
        
        try:
            audio_path, metadata = result
        except (ValueError, TypeError) as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректный формат данных: {e}")
            return
        
        # Проверяем существование файла
        if not Path(audio_path).exists():
            QMessageBox.warning(self, "Ошибка", f"Файл не найден: {audio_path}")
            return
        
        try:
            self.stop_audio()
            self.current_audio_info = AudioInfoExtractor.get_audio_info(str(audio_path))
            self.waveform_data = AudioInfoExtractor.get_waveform_data(str(audio_path), 200)
            self.waveform_widget.set_waveform_data(self.waveform_data)
            self.media_player.setSource(QUrl.fromLocalFile(str(audio_path)))
            self.update_audio_info(metadata)
            self.update_position_info()
            self.status_bar.showMessage(f"Загружен предыдущий файл: {Path(audio_path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить предыдущий файл: {e}")
    
    def toggle_play_pause(self):
        """Переключение воспроизведения/паузы"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            self.progress_timer.start(100)  # Обновление каждые 100 мс
    
    def stop_audio(self):
        """Остановка воспроизведения"""
        self.media_player.stop()
        self.progress_timer.stop()
        self.update_progress_bar(0)
        self.waveform_widget.set_position(0)
        self.lbl_current_time.setText("00:00")
    
    def seek_audio(self, value):
        """Перемотка аудио"""
        if self.media_player.isSeekable():
            duration = self.media_player.duration()
            if duration > 0:
                position = int(value / 1000.0 * duration)
                self.media_player.setPosition(position)
    
    def update_progress(self):
        """Обновление прогресса воспроизведения"""
        if self.media_player.duration() > 0:
            position = self.media_player.position()
            duration = self.media_player.duration()
            
            # Прогресс бар
            progress = int((position / duration) * 1000) if duration > 0 else 0
            self.update_progress_bar(progress)
            
            # Время
            self.lbl_current_time.setText(self.format_time(position))
            
            # Позиция на волне
            if duration > 0:
                self.waveform_widget.set_position(position / duration)
            else:
                self.waveform_widget.set_position(0)
    
    def update_progress_bar(self, value):
        """Обновление прогресс бара без генерации сигнала"""
        self.progress_bar.blockSignals(True)
        self.progress_bar.setValue(value)
        self.progress_bar.blockSignals(False)
    
    def format_time(self, milliseconds):
        """Форматирование времени в ММ:СС"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def enable_player_controls(self, enabled):
        """Включение/отключение элементов управления"""
        self.btn_previous.setEnabled(enabled)
        self.btn_play_pause.setEnabled(enabled)
        self.btn_stop.setEnabled(enabled)
        self.btn_next.setEnabled(enabled)
    
    def on_playback_state_changed(self, state):
        """Обработка изменения состояния воспроизведения"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.btn_play_pause.setText("⏸ Пауза")
            if self.current_audio_info:
                title = self.current_audio_info.get('title', self.current_audio_info.get('filename', 'Неизвестно'))
                self.status_bar.showMessage(f"Воспроизведение: {title}")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.btn_play_pause.setText("▶ Воспроизвести")
            self.status_bar.showMessage("Пауза")
        else:  # StoppedState
            self.btn_play_pause.setText("▶ Воспроизвести")
            self.status_bar.showMessage("Остановлено")
    
    def on_media_status_changed(self, status):
        """Обработка изменения статуса медиа"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            if self.current_audio_info:
                filename = self.current_audio_info.get('filename', 'Неизвестно')
                self.status_bar.showMessage(f"Аудио загружено: {filename}")
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_bar.showMessage("Воспроизведение завершено")
    
    def on_player_error(self, error, error_string):
        """Обработка ошибок медиаплеера"""
        QMessageBox.warning(self, "Ошибка воспроизведения", error_string)
        self.status_bar.showMessage(f"Ошибка: {error_string}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.stop_audio()
        event.accept()


def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)
    
    # Установка стиля
    app.setStyle('Fusion')
    
    # Создание и отображение главного окна
    window = AudioPlayerWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()