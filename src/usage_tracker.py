#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from src.logger import logger


class UsageTracker:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.start_time = None
        self.is_tracking = False
        logger.debug("UsageTracker 已初始化")

    def start_tracking(self):
        self.start_time = datetime.now()
        self.is_tracking = True
        logger.debug(f"开始使用跟踪: {self.start_time}")

    def stop_tracking(self):
        if self.is_tracking and self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() / 60
            date_key = self.start_time.strftime("%Y-%m-%d")
            self.config_manager.update_usage_stats(date_key, duration)
            self.start_time = None
            self.is_tracking = False
            logger.debug(f"停止使用跟踪，本次时长: {duration:.2f} 分钟")
            return duration
        return 0

    def get_current_session_duration(self):
        if self.is_tracking and self.start_time:
            return (datetime.now() - self.start_time).total_seconds() / 60
        return 0

    def get_total_usage(self):
        stats = self.config_manager.get_usage_stats()
        return sum(stats.values())
