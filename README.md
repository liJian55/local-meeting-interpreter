# 本地会议同传

Windows 64 位本地中英会议同传工具。采集飞书会议或本机播放声音，
使用 faster-whisper 离线识别语音，使用 OPUS-MT / CTranslate2 INT8 离线翻译，
在软件列表和桌面字幕中显示原文与译文。

- 无需 API Key，音频不上传云端。
- 默认英文翻译为中文，也可开启中文翻译为英文。
- 停止同传不会关闭软件。
- 当前为实时字幕版，不包含译文语音朗读。

## 开发环境启动

**从 GitHub 克隆源码时，需要按本节准备本地环境；拿到完整绿色版 ZIP
时不需要执行这些步骤。**

需要 Windows 10/11 64 位和 Python 3.11 或更高版本。打开 PowerShell：

```powershell
git clone git@github.com:liJian55/local-meeting-interpreter.git
cd local-meeting-interpreter
python -m venv .venv
.venv\Scripts\python.exe -m pip install --no-cache-dir -e . pytest psutil
.venv\Scripts\python.exe tools\setup_translation.py
.venv\Scripts\python.exe tools\setup_asr.py
.venv\Scripts\python.exe tools\build_launcher.ps1
```

其中模型下载脚本会自动创建 `models/`，分别下载并准备 Whisper small
和两个方向的 OPUS-MT INT8 模型。模型文件较大，下载过程需要联网；
下载完成后的识别和翻译无需联网。

双击项目根目录的 `Interpreter.exe`，或桌面上的 `Meeting Interpreter` 快捷方式。
首次使用请选择实际播放设备；飞书会议通道跟随 Windows 默认播放设备。

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

### 未上传目录如何补齐

**不要从其他电脑直接复制这些目录到仓库，也不要将它们提交到 Git。**
源码使用者根据自己的需求按下表生成：

| 目录 | 是否必须 | 用途与准备方式 |
| --- | --- | --- |
| `.venv/` | 开发运行必需 | 本地 Python 虚拟环境。执行 `python -m venv .venv` 创建，再执行开发环境启动中的 pip 安装命令。每台电脑单独创建，不能跨电脑复用。 |
| `models/` | 开发运行必需 | 离线语音识别和翻译模型。执行 `.venv\Scripts\python.exe tools\setup_translation.py` 和 `.venv\Scripts\python.exe tools\setup_asr.py` 自动下载。 |
| `dist/` | 仅分发时需要 | 完整绿色版目录和 ZIP。完成开发环境准备后，执行绿色版构建命令自动生成。 |
| `portable-build/` | 仅重新打包时需要 | 下载的 Python 嵌入运行时及打包中间文件。执行 `tools\build_portable.ps1` 自动创建；不需要手工准备。 |
| `samples/` | 仅音频测试时需要 | 测试 WAV 文件。执行 `powershell -ExecutionPolicy Bypass -File tools\generate_samples.ps1` 生成；需要 Windows 已安装脚本指定的本地语音。 |
| `reports/` | 仅性能测试时需要 | 性能测试结果。执行 benchmark 脚本自动创建，无需手工准备。 |

最小可运行源码环境只需补齐 `.venv/` 和 `models/`。其他目录都可以在
需要测试、性能分析或分发时再通过脚本生成。

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

