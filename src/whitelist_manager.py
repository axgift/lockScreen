#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.logger import logger

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil 模块未安装，白名单功能受限")


class WhitelistManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def is_app_whitelisted(self, app_name):
        whitelist = self.config_manager.get_whitelist_apps()
        app_name_lower = app_name.lower()
        return any(whitelist_app.lower() in app_name_lower for whitelist_app in whitelist)

    def get_running_apps(self):
        if not HAS_PSUTIL:
            return []
        
        try:
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return list(set(apps))
        except Exception as e:
            logger.error(f"获取运行中应用失败: {e}")
            return []

    def add_app(self, app_name):
        whitelist = self.config_manager.get_whitelist_apps()
        if app_name not in whitelist:
            whitelist.append(app_name)
            self.config_manager.set_whitelist_apps(whitelist)
            logger.info(f"已添加白名单应用: {app_name}")

    def remove_app(self, index):
        whitelist = self.config_manager.get_whitelist_apps()
        if 0 <= index < len(whitelist):
            removed = whitelist.pop(index)
            self.config_manager.set_whitelist_apps(whitelist)
            logger.info(f"已移除白名单应用: {removed}")
            return True
        return False

    def clear_all(self):
        self.config_manager.set_whitelist_apps([])
        logger.info("已清空白名单")
