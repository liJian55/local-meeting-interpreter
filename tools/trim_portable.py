from __future__ import annotations

from pathlib import Path
import shutil


def trim(package: Path) -> None:
    site = package / "runtime" / "Lib" / "site-packages"
    qt = site / "PySide6"
    for name in ("qml", "resources", "scripts", "support", "glue", "include", "lib", "doc", "metatypes", "QtAsyncio"):
        shutil.rmtree(qt / name, ignore_errors=True)
    keep_plugins = {"platforms", "styles", "imageformats", "iconengines", "generic", "platforminputcontexts"}
    for child in (qt / "plugins").iterdir():
        if child.name not in keep_plugins:
            shutil.rmtree(child)
    keep_dlls = {
        "Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll", "Qt6Network.dll", "Qt6OpenGL.dll",
        "Qt6OpenGLWidgets.dll", "Qt6PrintSupport.dll", "Qt6Svg.dll", "Qt6SvgWidgets.dll",
        "opengl32sw.dll", "d3dcompiler_47.dll", "libGLESv2.dll", "libEGL.dll",
    }
    for pattern in ("Qt6*.dll", "*.exe"):
        for file in qt.glob(pattern):
            if file.name not in keep_dlls:
                file.unlink()
    keep_bindings = {"QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtOpenGL", "QtOpenGLWidgets", "QtPrintSupport", "QtSvg", "QtSvgWidgets"}
    for file in qt.glob("Qt*.pyd"):
        if file.stem not in keep_bindings:
            file.unlink()
    for file in qt.glob("Qt*.pyi"):
        if file.stem not in keep_bindings:
            file.unlink()
    for directory in site.glob("pyside6_addons*.dist-info"):
        shutil.rmtree(directory)
    for directory in site.glob("pyside6_webengine*.dist-info"):
        shutil.rmtree(directory)


if __name__ == "__main__":
    import sys

    trim(Path(sys.argv[1]))
