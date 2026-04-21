#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

from src.logger import logger


class AutoStarter:
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    REGISTRY_KEY_NAME = "TimeManager"

    @staticmethod
    def is_autostart_enabled():
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutoStarter.REGISTRY_PATH, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, AutoStarter.REGISTRY_KEY_NAME)
                winreg.CloseKey(key)
                return True
            except WindowsError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            logger.error(f"检查开机自启失败: {e}")
            return False

    @staticmethod
    def set_autostart(enabled, exe_path=None):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutoStarter.REGISTRY_PATH, 0, winreg.KEY_SET_VALUE)

            if enabled:
                if exe_path is None:
                    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
                    
                    if getattr(sys, 'frozen', False):
                        exe_path = sys.executable
                        command = f'"{exe_path}"'
                    else:
                        python_exe = sys.executable
                        command = f'"{python_exe}" "{script_path}"'
                else:
                    command = f'"{exe_path}"'

                winreg.SetValueEx(key, AutoStarter.REGISTRY_KEY_NAME, 0, winreg.REG_SZ, command)
                logger.info(f"开机自启已启用: {command}")
            else:
                try:
                    winreg.DeleteValue(key, AutoStarter.REGISTRY_KEY_NAME)
                    logger.info("开机自启已禁用")
                except WindowsError:
                    pass

            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"设置开机自启失败: {e}")
            return False