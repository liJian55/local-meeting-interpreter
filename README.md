# 本地会议同传

Windows 64 位本地中英会议同传工具。采集飞书会议或本机播放声音，
使用 faster-whisper 离线识别语音，使用 OPUS-MT / CTranslate2 INT8 离线翻译，
在软件列表和桌面字幕中显示原文与译文。

- 无需 API Key，音频不上传云端。
- 默认英文翻译为中文，也可开启中文翻译为英文。
- 停止同传不会关闭软件。
- 当前为实时字幕版，不包含译文语音朗读。

## 开发环境启动

需要 Windows 10/11 64 位和 Python 3.11 或更高版本。

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-cache-dir -e . pytest
.venv\Scripts\python.exe tools\setup_translation.py
.venv\Scripts\python.exe tools\setup_asr.py
.venv\Scripts\python.exe tools\build_launcher.ps1
```

双击项目根目录的 `Interpreter.exe`，或桌面上的 `Meeting Interpreter` 快捷方式。
首次使用请选择实际播放设备；飞书会议通道跟随 Windows 默认播放设备。
模型安装脚本需要联网下载模型；正常使用无需联网。

## 绿色版

绿色版随包提供 Python、依赖和模型，接收者不需要安装或配置。
将整个 `MeetingInterpreter` 文件夹解压到本地磁盘后，双击 `Interpreter.exe`。
不要在 ZIP 内直接运行。

从源码构建绿色版：

```powershell
.venv\Scripts\python.exe tools\build_launcher.ps1
powershell -ExecutionPolicy Bypass -File tools\build_portable.ps1 -UseLocalPackages
```

生成 `dist\MeetingInterpreter\` 和 `dist\MeetingInterpreter-windows-x64.zip`。
SmartScreen 可能因程序没有数字签名而提示发布者未知。若安全软件阻止
当前目录加载 DLL，请移动整个文件夹或将其添加到信任列表。

## 仓库内容与大文件

仓库只保存源码、文档、测试和构建脚本，不提交 `.venv/`、`dist/`、
`portable-build/`、`models/`、`samples/` 和 `reports/`，因此不需要 Git LFS。
绿色版 ZIP 不放入 Git 历史；需要对外分发时，应单独发送 ZIP，
或作为 GitHub Release 附件上传。

## 测试与命令行

```powershell
.venv\Scripts\python.exe -m pytest tests
.venv\Scripts\python.exe tools\benchmark_translation.py
.venv\Scripts\python.exe tools\benchmark_asr.py samples\meeting-en.wav
.venv\Scripts\meeting-interpreter.exe translate "We will discuss the release plan tomorrow." en-zh
.venv\Scripts\meeting-interpreter.exe transcribe samples\meeting-en.wav
.venv\Scripts\meeting-interpreter.exe interpret samples\meeting-en.wav
```

未生成测试音频时，相关测试会跳过。许可证和模型来源见
`THIRD-PARTY-NOTICES.txt`；分发完整绿色版时请保留该文件及依赖许可证。

