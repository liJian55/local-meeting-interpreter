from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DesktopSubtitles(QWidget):
    hidden = Signal()

    def __init__(self) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("桌面译文")
        self.resize(860, 82)
        self.setMinimumSize(300, 82)
        self.drag_position: QPoint | None = None
        self.pending: deque[str] = deque()
        self.displayed_text = ""
        self.translation_history = ""
        self.resize_position: QPoint | None = None
        self.setStyleSheet(
            "QWidget#panel { background: rgba(28, 34, 50, 232); border: 1px solid #52617d; border-radius: 16px; }"
            "QLabel { color: #edf1f7; background: transparent; }"
            "QPushButton { color: #b8c4d9; background: transparent; border: none; font-size: 21px; padding: 4px 10px; }"
            "QPushButton:hover { color: white; background: #414b61; border-radius: 10px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        panel = QWidget(objectName="panel")
        layout.addWidget(panel)
        row = QHBoxLayout(panel)
        row.setContentsMargins(22, 12, 10, 12)
        self.text = QLabel("译文将在这里显示", alignment=Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setFont(QFont("Microsoft YaHei UI", 22, QFont.DemiBold))
        row.addWidget(self.text, 1)
        close = QPushButton("×", clicked=self.hide_subtitles)
        close.setToolTip("隐藏桌面译文")
        row.addWidget(close, 0, Qt.AlignTop)
        resize_handle = QLabel("⋮⋮", cursor=Qt.SizeHorCursor)
        resize_handle.setToolTip("拖动调整字幕宽度")
        resize_handle.mousePressEvent = self._start_resize
        resize_handle.mouseMoveEvent = self._resize_width
        row.addWidget(resize_handle, 0, Qt.AlignVCenter)
        self.timer = QTimer(self, interval=90, timeout=self._next_character)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - self.width() // 2, screen.bottom() - self.height() - 32)

    def show_translation(self, translation: str) -> None:
        self.pending.extend(translation)
        self.translation_history += translation
        if not self.timer.isActive():
            self.timer.start()

    def _next_character(self) -> None:
        if not self.pending:
            self.timer.stop()
            return
        self.displayed_text += self.pending.popleft()
        self.displayed_text = self._fit_text(self.displayed_text)
        self.text.setText(self.displayed_text)

    def _fit_text(self, text: str) -> str:
        self.text.setWordWrap(True)
        if self.text.fontMetrics().horizontalAdvance(text) <= self.text.width():
            return text
        self.text.setWordWrap(False)
        available = max(1, self.text.width())
        for start in range(len(text)):
            candidate = text[start:]
            if self.text.fontMetrics().horizontalAdvance(candidate) <= available:
                return candidate
        return text[-1:]

    def _refresh_text(self) -> None:
        self.displayed_text = self._fit_text(self.translation_history)
        self.text.setText(self.displayed_text)

    def _start_resize(self, event: QMouseEvent) -> None:
        self.resize_position = event.globalPosition().toPoint()

    def _resize_width(self, event: QMouseEvent) -> None:
        if self.resize_position is not None:
            delta = event.globalPosition().toPoint().x() - self.resize_position.x()
            self.resize(max(self.minimumWidth(), self.width() + delta), self.height())
            self.resize_position = event.globalPosition().toPoint()

    def set_font_size(self, size: int) -> None:
        self.text.setFont(QFont("Microsoft YaHei UI", size, QFont.DemiBold))
        self._refresh_text()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "translation_history"):
            self._refresh_text()

    def toggle(self) -> bool:
        self.setVisible(not self.isVisible())
        return self.isVisible()

    def hide_subtitles(self) -> None:
        self.hide()
        self.hidden.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.drag_position is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:
        self.drag_position = None

    def mouseDoubleClickEvent(self, _event: QMouseEvent) -> None:
        self.hide_subtitles()
