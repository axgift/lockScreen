from cx_Freeze import setup, Executable
import sys

base = "Win32GUI" if sys.platform == "win32" else None

include_files = [
    "logo.ico"
]

packages = [
    "keyboard",
    "pystray",
    "Pillow",
    "psutil",
    "Crypto",
    "appdirs"
]

executables = [
    Executable(
        "main.py",
        base=base,
        target_name="小灵控制屏幕保护程序.exe",
        icon="logo.ico"
    )
]

setup(
    name="TimeManager",
    version="1.0",
    description="时间管理屏幕保护程序",
    options={
        "build_exe": {
            "packages": packages,
            "include_files": include_files,
            "include_msvcr": True,
            "optimize": 2
        }
    },
    executables=executables
)
