from __future__ import annotations

import tkinter as tk
from collections import deque


class DesktopSubtitles:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title("桌面译文")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.93)
        self.window.configure(background="#68768b", padx=1, pady=1)
        self.panel = tk.Frame(self.window, background="#282e3e", padx=24, pady=14)
        self.panel.pack()
        self.text = tk.Label(
            self.window,
            text="译文将在这里显示",
            font=("Microsoft YaHei UI", 24, "bold"),
            foreground="#e4e3ed",
            background="#282e3e",
            justify=tk.CENTER,
            wraplength=1000,
        )
        self.text.pack(in_=self.panel)
        self.close_button = tk.Label(
            self.window,
            text="×",
            font=("Microsoft YaHei UI", 15, "bold"),
            foreground="#c7b2ce",
            background="#282e3e",
            cursor="hand2",
        )
        self.close_button.place(relx=1.0, x=-8, y=0, anchor=tk.NE)
        self.close_button.bind("<Button-1>", lambda _event: self.hide())
        self.visible = True
        self.pending_characters: deque[str] = deque()
        self.displayed_text = ""
        self.animation_job: str | None = None
        self.drag_start: tuple[int, int] | None = None
        for widget in (self.window, self.panel, self.text):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<Double-Button-1>", lambda _event: self.hide())
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        self._place_at_bottom()

    def _place_at_bottom(self) -> None:
        self.window.update_idletasks()
        width = min(1100, self.root.winfo_screenwidth() - 80)
        height = self.window.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = self.root.winfo_screenheight() - height - 100
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _start_drag(self, event: tk.Event) -> None:
        self.drag_start = (event.x_root - self.window.winfo_x(), event.y_root - self.window.winfo_y())

    def _drag(self, event: tk.Event) -> None:
        if self.drag_start:
            x = event.x_root - self.drag_start[0]
            y = event.y_root - self.drag_start[1]
            self.window.geometry(f"+{x}+{y}")

    def show_translation(self, translation: str) -> None:
        self.pending_characters.extend(translation)
        if self.animation_job is None:
            self._animate_next_character()

    def _animate_next_character(self) -> None:
        if not self.pending_characters:
            self.animation_job = None
            return
        self.displayed_text = (self.displayed_text + self.pending_characters.popleft())[-20:]
        self.text.configure(text=self.displayed_text)
        self.animation_job = self.window.after(90, self._animate_next_character)

    def set_font_size(self, size: int) -> None:
        self.text.configure(font=("Microsoft YaHei UI", size, "bold"))
        self.window.update_idletasks()
        self.window.geometry(f"{self.window.winfo_width()}x{self.window.winfo_reqheight()}")

    def toggle(self) -> bool:
        if self.visible:
            self.hide()
        else:
            self.visible = True
            self.window.deiconify()
            self.window.attributes("-topmost", True)
        return self.visible

    def hide(self) -> None:
        self.visible = False
        self.window.withdraw()
        self.root.event_generate("<<SubtitlesHidden>>", when="tail")

    def close(self) -> None:
        if self.animation_job is not None:
            self.window.after_cancel(self.animation_job)
        self.window.destroy()
