#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import time

from src.logger import logger

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil 模块未安装，进程保护功能不可用")


class ProcessProtector:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.running = True
        self.monitor_thread = None
        self.lock_screen_window = None

    def start_monitoring(self):
        if HAS_PSUTIL:
            self.monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            self.monitor_thread.start()
            logger.info("进程保护已启动")
        else:
            logger.warning("进程保护功能需要安装 psutil")

    def set_lock_screen_window(self, window):
        self.lock_screen_window = window

    def _monitor_process(self):
        while self.running:
            time.sleep(3)
            self._check_lock_screen_status()

    def _check_lock_screen_status(self):
        try:
            from src.time_checker import TimeChecker
            time_checker = TimeChecker(self.config_manager)
            
            if time_checker.is_locked_time():
                if self.lock_screen_window is None or not self._is_window_alive():
                    logger.warning("检测到锁定屏幕已关闭，重新显示")
                    self._restart_lock_screen()
        except Exception as e:
            logger.error(f"检查锁定屏幕状态失败: {e}")

    def _is_window_alive(self):
        try:
            if self.lock_screen_window and hasattr(self.lock_screen_window, 'winfo_exists'):
                return self.lock_screen_window.winfo_exists()
            return False
        except Exception:
            return False

    def _restart_lock_screen(self):
        try:
            logger.info("尝试重新显示锁定屏幕")
            if hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.immediate_lock()
        except Exception as e:
            logger.error(f"重新显示锁定屏幕失败: {e}")

    def stop_monitoring(self):
        self.running = False
        logger.info("进程保护已停止")