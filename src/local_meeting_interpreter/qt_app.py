from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from local_meeting_interpreter.paths import project_root
from local_meeting_interpreter.qt_subtitles import DesktopSubtitles
from PySide6.QtWidgets import QSizePolicy, QAbstractItemView


STYLE = """
QMainWindow, QWidget#root { background: #f3f5fa; color: #273249; }
QWidget#header { background: #202b44; border-radius: 18px; }
QLabel#title { color: #f1f5ff; font-size: 28px; font-weight: 600; }
QLabel#subtitle, QLabel#badge { color: #aebbd4; font-size: 12px; }
QLabel#badge { color: #b8d9d3; background: #2d3c55; padding: 7px 12px; border-radius: 11px; }
QFrame#card { background: white; border: 1px solid #e0e5ef; border-radius: 14px; }
QLabel#section { color: #66738c; font-size: 12px; font-weight: 600; }
QLabel { font-family: 'Microsoft YaHei UI'; font-size: 13px; background: transparent; }
QComboBox, QSpinBox { background: #f7f8fc; border: 1px solid #dbe1ed; border-radius: 8px; padding: 9px 12px; color: #273249; selection-background-color: #e4e8f8; }
QComboBox:focus, QSpinBox:focus { border-color: #8995cc; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView { background: white; border: 1px solid #dbe1ed; selection-background-color: #e6eaf7; selection-color: #273249; padding: 5px; }
QCheckBox { spacing: 9px; color: #34415b; background: transparent; }
QCheckBox::indicator { width: 17px; height: 17px; border-radius: 4px; border: 1px solid #bac3d5; background: white; }
QCheckBox::indicator:checked { background: #6978b5; border-color: #6978b5; }
QPushButton { background: #eef1f8; color: #4b5975; border: 1px solid #dfe4ef; border-radius: 8px; padding: 9px 15px; }
QPushButton:hover { background: #e2e7f4; }
QPushButton#primary { background: #6374b1; color: white; border: none; border-radius: 10px; padding: 13px 25px; font-size: 14px; font-weight: 600; }
QPushButton#primary:hover { background: #53649f; }
QPushButton#primary:disabled { background: #aab2ca; }
QPushButton#stop { background: #a66e85; }
QTableWidget { background: white; alternate-background-color: #f7f8fc; border: 1px solid #e0e5ef; border-radius: 6px; gridline-color: #edf0f6; selection-background-color: #e5e9f6; selection-color: #273249; }
QHeaderView::section { background: #f5f6fa; color: #78839a; border: none; padding: 10px; font-weight: 600; }
QTextEdit { background: #f8f9fc; border: 1px solid #e0e5ef; border-radius: 10px; padding: 10px; color: #485672; }
QLabel#status { color: #64718a; padding: 3px; }
QLabel#privacy { color: #8c95a8; font-size: 11px; }
QScrollBar:vertical { background: transparent; width: 9px; }
QScrollBar::handle:vertical { background: #c9d0df; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""


def card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(objectName="card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 14, 18, 16)
    layout.setSpacing(10)
    label = QLabel(title, objectName="section")
    layout.addWidget(label)
    effect = QGraphicsDropShadowEffect(blurRadius=20, xOffset=0, yOffset=3)
    effect.setColor(QColor(39, 50, 73, 18))
    frame.setGraphicsEffect(effect)
    return frame, layout


class MainWindow(QMainWindow):
    segment_received = Signal(str, str, str)
    status_received = Signal(str)
    error_received = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地会议同传")
        self.setWindowIcon(QIcon(str(project_root() / "assets" / "interpreter.ico")))
        self.resize(940, 720)
        self.setMinimumSize(780, 620)
        self.model_root = project_root() / "models"
        self.interpreter = None
        self.worker: threading.Thread | None = None
        self.running = False
        self.stopping = False
        self.audio_sources = []
        self._build_ui()
        self.subtitles = DesktopSubtitles()
        self.subtitles.hidden.connect(lambda: self.subtitle_button.setText("显示桌面译文"))
        self.subtitles.show()
        self.segment_received.connect(self._append_segment)
        self.status_received.connect(self.status.setText)
        self.error_received.connect(self._show_error)
        self.watch = QTimer(self, interval=100, timeout=self._watch_worker)
        self.watch.start()
        self._load_sources()

    def _build_ui(self) -> None:
        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(13)
        header = QWidget(objectName="header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("本地会议同传", objectName="title"))
        title_row.addStretch()
        title_row.addWidget(QLabel("●  本地离线运行", objectName="badge"))
        header_layout.addLayout(title_row)
        self.status = QLabel("打开飞书会议后，点击“开始同传”。", objectName="subtitle")
        header_layout.addWidget(self.status)
        header_layout.addWidget(QLabel("REAL-TIME INTERPRETER   /   让每一种语言都被理解", objectName="subtitle"))
        layout.addWidget(header)
        source_card, source_layout = card("音频来源")
        self.source_box = QComboBox()
        source_layout.addWidget(self.source_box)
        layout.addWidget(source_card)
        settings_card, settings_layout = card("翻译与桌面字幕")
        row = QHBoxLayout()
        self.english = QCheckBox("英文  →  中文", checked=True)
        self.chinese = QCheckBox("中文  →  英文")
        row.addWidget(self.english)
        row.addWidget(self.chinese)
        row.addStretch()
        row.addWidget(QLabel("字幕字号"))
        self.font_size = QSpinBox(minimum=16, maximum=48, value=24)
        row.addWidget(self.font_size)
        self.subtitle_button = QPushButton("隐藏桌面译文", clicked=self._toggle_subtitles)
        row.addWidget(self.subtitle_button)
        settings_layout.addLayout(row)
        layout.addWidget(settings_card)
        controls = QHBoxLayout()
        self.start_button = QPushButton("开始同传", objectName="primary", clicked=self._toggle)
        controls.addWidget(self.start_button)
        controls.addWidget(QLabel("无需选择文件，播放会议声音即可开始"))
        controls.addStretch()
        layout.addLayout(controls)
        result_card, result_layout = card("实时原文与译文")
        result_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        result_card.setFixedHeight(300)
        self.results = QTableWidget(0, 3)
        self.results.setHorizontalHeaderLabels(["语种", "原文", "译文"])
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results.setColumnWidth(0, 65)
        self.results.verticalHeader().setVisible(False)
        self.results.setAlternatingRowColors(True)
        self.results.setMinimumHeight(0)
        self.results.verticalHeader().setDefaultSectionSize(38)
        self.results.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results.setWordWrap(False)
        self.results.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results.itemClicked.connect(self._show_details)
        self.results.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        result_layout.setContentsMargins(18, 14, 18, 24)
        result_layout.addWidget(self.results)
        layout.addWidget(result_card)
        self.details_popup = None
        layout.addWidget(QLabel("本地模型处理  ·  音频不上传云端  ·  译文仅在桌面显示", objectName="privacy"))
        self.font_size.valueChanged.connect(lambda size: self.subtitles.set_font_size(size) if hasattr(self, "subtitles") else None)

    def _load_sources(self) -> None:
        try:
            from local_meeting_interpreter.audio.devices import available_sources

            self.audio_sources = available_sources()
            for source in self.audio_sources:
                self.source_box.addItem(source.label)
        except Exception as error:
            self.status.setText(str(error))

    def _toggle(self) -> None:
        if self.stopping:
            return
        if self.running:
            self.stopping = True
            self.start_button.setEnabled(False)
            self.status.setText("正在停止同传，软件会保持打开...")
            self.interpreter.stop()
            QTimer.singleShot(3000, self._stopped)
            return
        if not self.english.isChecked() and not self.chinese.isChecked():
            QMessageBox.warning(self, "选择翻译方向", "请至少开启一个翻译方向。")
            return
        if not self.audio_sources:
            QMessageBox.warning(self, "音频来源", "未找到可用的音频采集设备。")
            return
        from local_meeting_interpreter.realtime import RealtimeInterpreter

        self.interpreter = RealtimeInterpreter(
            self.model_root, self.segment_received.emit, self.status_received.emit, self.error_received.emit
        )
        self.running = True
        self.start_button.setText("停止同传")
        self.start_button.setObjectName("stop")
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)
        source = self.audio_sources[self.source_box.currentIndex()]
        self.worker = threading.Thread(
            target=self.interpreter.run,
            args=(self.english.isChecked(), self.chinese.isChecked(), source.device_index, source.feishu_only),
            daemon=True,
        )
        self.worker.start()

    def _watch_worker(self) -> None:
        if self.running and not self.stopping and self.worker and not self.worker.is_alive():
            self._stopped()

    def _stopped(self) -> None:
        self.running = False
        self.stopping = False
        self.start_button.setEnabled(True)
        self.start_button.setText("开始同传")
        self.start_button.setObjectName("primary")
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)
        self.status.setText("同传已停止，软件保持打开。")

    def _append_segment(self, language: str, source: str, translation: str) -> None:
        self.results.insertRow(0)
        for column, text in enumerate(({"en": "英文", "zh": "中文"}.get(language, language), source, translation)):
            item = QTableWidgetItem(text)
            item.setToolTip(text)
            self.results.setItem(0, column, item)
        if translation != "此翻译方向未开启":
            self.subtitles.show_translation(translation)

    def _show_details(self, item: QTableWidgetItem) -> None:
        row = item.row()
        if self.details_popup is not None:
            self.details_popup.close()
            self.details_popup = None
        popup = QFrame(self, Qt.Tool | Qt.FramelessWindowHint)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        popup.destroyed.connect(lambda: setattr(self, "details_popup", None))
        popup.setStyleSheet(
            "QFrame { background: white; border: 1px solid #ccd4e5; border-radius: 12px; }"
            "QLabel { color: #66738c; font-weight: 600; padding-top: 4px; }"
            "QTextEdit { background: #f7f8fc; border: none; border-radius: 8px; padding: 10px; color: #273249; }"
            "QPushButton { padding: 6px 12px; }"
        )
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(16, 12, 16, 14)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("完整原文与译文"))
        title_row.addStretch()
        title_row.addWidget(QPushButton("关闭", clicked=popup.close))
        layout.addLayout(title_row)
        layout.addWidget(QLabel("原文"))
        layout.addWidget(QTextEdit(self.results.item(row, 1).text(), readOnly=True, minimumHeight=100))
        layout.addWidget(QLabel("译文"))
        layout.addWidget(QTextEdit(self.results.item(row, 2).text(), readOnly=True, minimumHeight=100))
        popup.resize(620, 410)
        popup.move(self.frameGeometry().center() - popup.rect().center())
        popup.show()
        popup.raise_()
        popup.activateWindow()
        self.details_popup = popup

    def _show_error(self, error: str) -> None:
        self._stopped()
        QMessageBox.critical(self, "同传错误", error)

    def _toggle_subtitles(self) -> None:
        visible = self.subtitles.toggle()
        self.subtitle_button.setText("隐藏桌面译文" if visible else "显示桌面译文")

    def closeEvent(self, event) -> None:
        if self.interpreter:
            self.interpreter.stop()
        if self.details_popup is not None:
            self.details_popup.close()
            self.details_popup = None
        self.subtitles.close()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (project_root() / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
