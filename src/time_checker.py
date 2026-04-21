#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta
from src.config.config_manager import ConfigManager
from src.logger import logger


class TimeChecker:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        logger.debug("TimeChecker 已初始化")

    def get_current_day_name(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
        return days[datetime.now().weekday()]

    def parse_time(self, time_str):
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            logger.error(f"解析时间字符串失败: {time_str}")
            return time(hour=0, minute=0)

    def is_locked_time(self):
        current_day = self.get_current_day_name()
        schedules = self.config_manager.get_day_schedule(current_day)

        if not schedules or len(schedules) == 0:
            logger.debug(f"{current_day} 没有可用时间段，需要锁定")
            return True

        now = datetime.now().time()

        for schedule in schedules:
            start_time = self.parse_time(schedule.get("start", "00:00"))
            end_time = self.parse_time(schedule.get("end", "23:59"))

            if start_time <= end_time:
                if start_time <= now <= end_time:
                    logger.debug(f"当前时间 {now} 在时间段 {start_time}-{end_time} 内，不需要锁定")
                    return False
            else:
                if now >= start_time or now <= end_time:
                    logger.debug(f"当前时间 {now} 在跨天时间段 {start_time}-{end_time} 内，不需要锁定")
                    return False

        logger.debug(f"当前时间 {now} 不在任何可用时间段内，需要锁定")
        return True

    def get_next_unlock_time(self):
        current_day = self.get_current_day_name()
        schedules = self.config_manager.get_day_schedule(current_day)

        if not schedules or len(schedules) == 0:
            return None

        now = datetime.now()

        future_times = []
        for schedule in schedules:
            start_time = self.parse_time(schedule.get("start", "08:00"))
            end_time = self.parse_time(schedule.get("end", "22:00"))

            if start_time <= now.time() <= end_time:
                return None

            if now.time() < start_time:
                future_times.append(datetime.combine(now.date(), start_time))

        if future_times:
            next_unlock = min(future_times)
            logger.debug(f"下次解锁时间: {next_unlock}")
            return next_unlock

        next_day = now + timedelta(days=1)
        next_day_name = ["Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday", "Sunday"][next_day.weekday()]
        next_schedules = self.config_manager.get_day_schedule(next_day_name)

        if next_schedules and len(next_schedules) > 0:
            earliest_start = None
            for schedule in next_schedules:
                start_time = self.parse_time(schedule.get("start", "08:00"))
                if earliest_start is None or start_time < earliest_start:
                    earliest_start = start_time
            if earliest_start:
                next_unlock = datetime.combine(next_day.date(), earliest_start)
                logger.debug(f"下次解锁时间（明天）: {next_unlock}")
                return next_unlock
        
        return None

    def get_next_lock_time(self):
        current_day = self.get_current_day_name()
        schedules = self.config_manager.get_day_schedule(current_day)

        if not schedules or len(schedules) == 0:
            return None

        now = datetime.now()

        for schedule in schedules:
            start_time = self.parse_time(schedule.get("start", "00:00"))
            end_time = self.parse_time(schedule.get("end", "23:59"))

            if start_time <= end_time:
                if start_time <= now.time() <= end_time:
                    return datetime.combine(now.date(), end_time)
            else:
                if now.time() >= start_time or now.time() <= end_time:
                    if now.time() >= start_time:
                        return datetime.combine(now.date(), end_time)
                    else:
                        return datetime.combine(now.date() + timedelta(days=1), end_time)

        future_starts = []
        for schedule in schedules:
            start_time = self.parse_time(schedule.get("start", "00:00"))
            if now.time() < start_time:
                future_starts.append(datetime.combine(now.date(), start_time))

        if future_starts:
            return min(future_starts)

        next_day = now + timedelta(days=1)
        next_day_name = ["Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday", "Sunday"][next_day.weekday()]
        next_schedules = self.config_manager.get_day_schedule(next_day_name)

        if next_schedules and len(next_schedules) > 0:
            earliest_start = None
            for schedule in next_schedules:
                start_time = self.parse_time(schedule.get("start", "08:00"))
                if earliest_start is None or start_time < earliest_start:
                    earliest_start = start_time
            if earliest_start:
                return datetime.combine(next_day.date(), earliest_start)

        return None
