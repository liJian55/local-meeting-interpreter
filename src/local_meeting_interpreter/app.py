from __future__ import annotations

import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import messagebox, ttk

from local_meeting_interpreter.paths import project_root
from local_meeting_interpreter.desktop_subtitles import DesktopSubtitles
from local_meeting_interpreter.theme import apply_cyberpunk, PANEL, CYAN, TEXT


class InterpreterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("本地会议同传")
        self.root.geometry("960x700")
        self.root.minsize(720, 520)
        self.model_root = project_root() / "models"
        self.events: queue.Queue[tuple] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.interpreter = None
        self.running = False
        self.stopping = False
        self.english_to_chinese = tk.BooleanVar(value=True)
        self.chinese_to_english = tk.BooleanVar(value=False)
        self.status_text = tk.StringVar(value="打开飞书会议后，点击“开始同传”。")
        self.audio_sources = []
        self._build_style()
        self._build_ui()
        self.subtitles = DesktopSubtitles(root)
        self.root.bind("<<SubtitlesHidden>>", lambda _event: self.subtitle_button.configure(text="显示桌面译文"))
        self.root.after(100, self._poll_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_style(self) -> None:
        apply_cyberpunk(self.root)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=28)
        outer.pack(fill=tk.BOTH, expand=True)
        ttk.Label(outer, text="本地会议同传", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(outer, text="NEURAL INTERPRETER  /  飞书与本机音频实时翻译", style="Subtitle.TLabel").pack(
            anchor=tk.W, pady=(4, 22)
        )
        tk.Frame(outer, background=CYAN, height=2).pack(fill=tk.X, pady=(0, 20))
        source_frame = ttk.LabelFrame(outer, text="01  音频来源", padding=14)
        source_frame.pack(fill=tk.X, pady=(0, 14))
        self.source_box = ttk.Combobox(source_frame, state="readonly")
        self.source_box.pack(fill=tk.X)
        self._refresh_sources()
        settings = ttk.LabelFrame(outer, text="02  翻译与桌面字幕", padding=14)
        settings.pack(fill=tk.X)
        ttk.Checkbutton(settings, text="英文 → 中文", variable=self.english_to_chinese).pack(side=tk.LEFT)
        ttk.Checkbutton(settings, text="中文 → 英文", variable=self.chinese_to_english).pack(
            side=tk.LEFT, padx=(30, 0)
        )
        self.subtitle_button = ttk.Button(settings, text="隐藏桌面译文", command=self._toggle_subtitles)
        self.subtitle_button.pack(side=tk.RIGHT)
        ttk.Label(settings, text="字号").pack(side=tk.RIGHT, padx=(16, 4))
        self.font_size = tk.IntVar(value=24)
        ttk.Spinbox(
            settings, from_=16, to=48, width=3, textvariable=self.font_size,
            command=lambda: self.subtitles.set_font_size(self.font_size.get()),
        ).pack(side=tk.RIGHT)
        controls = ttk.Frame(outer)
        controls.pack(fill=tk.X, pady=16)
        self.start_button = ttk.Button(controls, text="开始同传", style="Accent.TButton", command=self._toggle)
        self.start_button.pack(side=tk.LEFT)
        ttk.Label(
            controls, text="无需选择文件；请保持会议声音通过本机扬声器或耳机播放。", style="Status.TLabel"
        ).pack(side=tk.LEFT, padx=20)
        result_frame = ttk.LabelFrame(outer, text="03  实时原文与译文", padding=8)
        result_frame.pack(fill=tk.BOTH, expand=True)
        self.results = ttk.Treeview(result_frame, columns=("language", "source", "translation"), show="headings")
        self.results.heading("language", text="语种")
        self.results.heading("source", text="原文")
        self.results.heading("translation", text="译文")
        self.results.column("language", width=70, stretch=False, anchor=tk.CENTER)
        self.results.column("source", width=350)
        self.results.column("translation", width=350)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.results.yview)
        self.results.configure(yscrollcommand=scrollbar.set)
        self.results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results.tag_configure("odd", background="#2b3142")
        self.results.bind("<<TreeviewSelect>>", self._show_details)
        self.details = tk.Text(
            outer, height=5, wrap=tk.WORD, font=("Microsoft YaHei UI", 10),
            relief=tk.FLAT, background=PANEL, foreground=TEXT,
            insertbackground=CYAN, highlightthickness=1, highlightbackground="#454a60",
            padx=12, pady=8,
        )
        self.details.pack(fill=tk.X, pady=(10, 0))
        self.details.insert(tk.END, "选择一段文字可查看全文。")
        self.details.configure(state=tk.DISABLED)
        ttk.Label(outer, textvariable=self.status_text, style="Status.TLabel", wraplength=820).pack(
            anchor=tk.W, pady=(14, 0)
        )
        ttk.Label(
            outer, text="当前版本显示实时字幕，暂不朗读译文；音频不会发送到云端。", style="Status.TLabel"
        ).pack(anchor=tk.W, pady=(4, 0))

    def _toggle(self) -> None:
        if self.stopping:
            return
        if self.running:
            self.stopping = True
            self.status_text.set("正在停止同传，软件会保持打开...")
            self.start_button.configure(state=tk.DISABLED)
            if self.interpreter:
                self.interpreter.stop()
            self.root.after(3000, self._finish_stopping)
            return
        if not self.english_to_chinese.get() and not self.chinese_to_english.get():
            messagebox.showwarning("选择翻译方向", "请至少开启一个翻译方向。")
            return
        from local_meeting_interpreter.realtime import RealtimeInterpreter

        self.interpreter = RealtimeInterpreter(
            self.model_root,
            lambda language, text, translation: self.events.put(("segment", language, text, translation)),
            lambda status: self.events.put(("status", status)),
            lambda error: self.events.put(("error", error)),
        )
        self.running = True
        self.start_button.configure(text="停止同传")
        self.status_text.set("正在启动本地模型...")
        self.worker = threading.Thread(
            target=self.interpreter.run,
            args=(
                self.english_to_chinese.get(), self.chinese_to_english.get(),
                self.audio_sources[self.source_box.current()].device_index,
                self.audio_sources[self.source_box.current()].feishu_only,
            ),
            daemon=True,
        )
        self.worker.start()
        self.root.after(100, self._watch_worker)

    def _finish_stopping(self) -> None:
        if self.stopping:
            self._stopped()

    def _watch_worker(self) -> None:
        if not self.running or self.stopping:
            return
        if self.worker and not self.worker.is_alive():
            self._stopped()
            return
        self.root.after(100, self._watch_worker)

    def _refresh_sources(self) -> None:
        try:
            from local_meeting_interpreter.audio.devices import available_sources

            self.audio_sources = available_sources()
            self.source_box.configure(values=[source.label for source in self.audio_sources])
            self.source_box.current(0)
        except Exception as error:
            self.source_box.configure(values=["音频设备读取失败"])
            self.source_box.current(0)
            self.status_text.set(str(error))

    def _show_details(self, _event=None) -> None:
        selected = self.results.selection()
        if not selected:
            return
        values = self.results.item(selected[0], "values")
        self.details.configure(state=tk.NORMAL)
        self.details.delete("1.0", tk.END)
        self.details.insert(tk.END, f"{values[1]}\n\n{values[2]}")
        self.details.configure(state=tk.DISABLED)

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "status":
                    self.status_text.set(event[1])
                elif event[0] == "segment":
                    language = {"en": "英文", "zh": "中文"}.get(event[1], event[1])
                    self.results.insert("", 0, values=(language, event[2], event[3]))
                    if event[3] != "此翻译方向未开启":
                        self.subtitles.show_translation(event[3])
                elif event[0] == "error":
                    self._stopped()
                    messagebox.showerror("同传错误", event[1])
                elif event[0] == "close":
                    self.root.destroy()
                    return
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _stopped(self) -> None:
        self.running = False
        self.stopping = False
        self.start_button.configure(state=tk.NORMAL, text="开始同传")
        self.status_text.set("同传已停止，软件保持打开。")

    def _on_close(self) -> None:
        if self.interpreter and self.running:
            self.stopping = True
            self.start_button.configure(state=tk.DISABLED)
            self.status_text.set("正在停止同传，请稍候...")
            threading.Thread(target=self._close_when_stopped, daemon=True).start()
            return
        self.root.destroy()

    def _toggle_subtitles(self) -> None:
        visible = self.subtitles.toggle()
        self.subtitle_button.configure(text="隐藏桌面译文" if visible else "显示桌面译文")

    def _close_when_stopped(self) -> None:
        if self.interpreter:
            self.interpreter.stop()
        self.events.put(("close",))


def main() -> None:
    root = tk.Tk()
    icon_path = project_root() / "assets" / "interpreter.ico"
    if icon_path.is_file():
        root.iconbitmap(default=str(icon_path))
    InterpreterApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        from pathlib import Path

        Path(project_root() / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        messagebox.showerror("启动失败", traceback.format_exc(limit=2))
        sys.exit(1)
