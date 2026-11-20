from __future__ import annotations

import tkinter as tk
from tkinter import ttk


BG = "#1b1e2b"
PANEL = "#252a3a"
PANEL_ALT = "#30374a"
CYAN = "#a6c8d8"
TEXT = "#e4e3ed"
MUTED = "#a5a8ba"


def apply_cyberpunk(root: tk.Tk) -> ttk.Style:
    root.configure(background=BG)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=PANEL, foreground=TEXT, fieldbackground=PANEL_ALT)
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Microsoft YaHei UI", 10))
    style.configure("Panel.TLabel", background=PANEL, foreground=TEXT)
    style.configure("Title.TLabel", background=BG, foreground=CYAN, font=("Microsoft YaHei UI", 27, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 10))
    style.configure("Status.TLabel", background=BG, foreground=MUTED, font=("Microsoft YaHei UI", 9))
    style.configure("PanelMuted.TLabel", background=PANEL, foreground=MUTED)
    style.configure("TLabelframe", background=BG, bordercolor="#454a60", relief=tk.SOLID, borderwidth=1)
    style.configure("TLabelframe.Label", background=BG, foreground=CYAN, font=("Microsoft YaHei UI", 10, "bold"))
    style.configure("TButton", background=PANEL_ALT, foreground=CYAN, bordercolor="#515b72", padding=(14, 9))
    style.map("TButton", background=[("active", "#414b60"), ("pressed", "#4d566b")])
    style.configure("Accent.TButton", background="#819da9", foreground="#18222b", bordercolor="#a6c8d8", padding=(20, 12), font=("Microsoft YaHei UI", 11, "bold"))
    style.map("Accent.TButton", background=[("active", "#b0cad5"), ("disabled", "#535c68")])
    style.configure("TCheckbutton", background=PANEL, foreground=TEXT, font=("Microsoft YaHei UI", 10))
    style.map("TCheckbutton", background=[("active", PANEL)], foreground=[("active", CYAN)])
    style.configure("TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT, foreground=TEXT, arrowcolor=CYAN, bordercolor="#515b72", padding=8)
    style.map("TCombobox", fieldbackground=[("readonly", PANEL_ALT)], foreground=[("readonly", TEXT)])
    style.configure("TSpinbox", fieldbackground=PANEL_ALT, foreground=CYAN, arrowcolor=CYAN, insertcolor=CYAN)
    style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, bordercolor="#454a60", rowheight=36)
    style.configure("Treeview.Heading", background=PANEL_ALT, foreground=CYAN, relief=tk.FLAT, padding=8)
    style.map("Treeview", background=[("selected", "#46546b")], foreground=[("selected", TEXT)])
    style.configure("TScrollbar", background=PANEL_ALT, troughcolor=BG, bordercolor=BG, arrowcolor=CYAN)
    root.option_add("*TCombobox*Listbox.background", PANEL_ALT)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", "#46546b")
    return style
