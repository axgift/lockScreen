#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小灵控制屏幕保护程序
主入口文件
"""

import sys
import os
import time as time_module
from pathlib import Path

from src.logger import logger
from src.main_window import MainWindow


def check_single_instance():
    lock_file = Path(__file__).parent / ".lock"
    try:
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                if is_process_running(pid):
                    logger.warning("程序已在运行中")
                    return False
                else:
                    logger.info(f"发现残留的锁文件，进程 {pid} 已不存在，将清理")
            except (ValueError, IOError):
                lock_time = lock_file.stat().st_mtime
                if (time_module.time() - lock_time) < 60:
                    logger.warning("程序已在运行中")
                    return False

        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.error(f"检查单实例失败: {e}")
        return True


def is_process_running(pid):
    try:
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x100000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle != 0:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ValueError):
        return False


def cleanup_lock():
    lock_file = Path(__file__).parent / ".lock"
    try:
        if lock_file.exists():
            lock_file.unlink()
            logger.info("锁文件已清理")
        else:
            logger.debug("锁文件不存在，无需清理")
    except Exception as e:
        logger.error(f"清理锁文件失败: {e}")


def main():
    logger.info("开始主程序...")
    
    if not check_single_instance():
        logger.info("检测到其他实例，退出")
        sys.exit(1)

    try:
        logger.info("创建主窗口...")
        app = MainWindow()
        logger.info("主窗口创建成功")
        logger.info("开始运行...")
        app.run()
        logger.info("程序运行结束")
    except Exception as e:
        logger.critical(f"程序运行出错: {e}", exc_info=True)
    finally:
        logger.info("清理锁文件...")
        cleanup_lock()


if __name__ == "__main__":
    main()
