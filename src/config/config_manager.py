#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import hashlib
import uuid
from pathlib import Path
from datetime import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64
import appdirs

from src.logger import logger


class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_file=None):
        if self._initialized:
            return
        
        self._initialized = True
        
        if config_file is None:
            config_dir = Path(appdirs.user_data_dir("TimeManager", "TimeManager"))
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = config_dir / "st.pt"
            logger.info(f"配置文件路径: {self.config_file}")
        else:
            self.config_file = Path(config_file)
        
        self.config = self._load_config()

    def _get_machine_identifier(self):
        try:
            if os.name == 'nt':
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                return value
            else:
                return hashlib.md5(uuid.getnode().to_bytes(8, 'big')).hexdigest()
        except Exception as e:
            logger.warning(f"获取机器标识符失败: {e}")
            return str(uuid.getnode())

    def _get_file_encryption_key(self):
        user_id = os.getlogin() if hasattr(os, 'getlogin') else "default"
        machine_id = self._get_machine_identifier()
        key_material = f"TimeManager_File_Key_{user_id}_{machine_id}_2024".encode('utf-8')
        salt = b"TimeManager_File_Salt_2024_16B"
        return PBKDF2(key_material, salt, dkLen=32, count=100000)

    def _encrypt_config(self, config_data):
        try:
            key = self._get_file_encryption_key()
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded = pad(config_data.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded)
            return b'TM_ENCRYPTED' + iv + encrypted
        except Exception as e:
            logger.error(f"加密配置文件失败: {e}")
            return config_data.encode('utf-8')

    def _decrypt_config(self, encrypted_data):
        try:
            key = self._get_file_encryption_key()
            iv = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            logger.error(f"解密配置文件失败: {e}")
            raise

    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'rb') as f:
                    data = f.read()
                
                if data.startswith(b'TM_ENCRYPTED'):
                    config = self._decrypt_config(data[12:])
                else:
                    config = json.loads(data.decode('utf-8'))
                    logger.warning("检测到未加密的配置文件，建议重新保存")
                
                self._validate_config(config)
                return config
            except json.JSONDecodeError as e:
                logger.error(f"配置文件格式错误，将使用默认配置: {e}")
                self._backup_bad_config()
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
        
        default_config = self._get_default_config().copy()
        try:
            self.config = default_config
            self.save_config()
            logger.info("已创建默认配置文件")
        except Exception as e:
            logger.error(f"无法创建默认配置文件: {e}")
        
        return default_config

    def _validate_config(self, config):
        required_keys = ['admin_password', 'temp_password', 'weekly_schedule', 'emergency_question', 'emergency_answer']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件缺少必要字段: {key}")
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule = config.get('weekly_schedule', {})
        for day in days:
            if day not in schedule:
                logger.warning(f"缺少{day}的时间计划，使用默认值")
                schedule[day] = [{"start": "08:00", "end": "22:00"}]

    def _backup_bad_config(self):
        try:
            backup_path = str(self.config_file) + ".backup"
            import shutil
            shutil.copy(str(self.config_file), backup_path)
            logger.info(f"已备份损坏的配置文件到: {backup_path}")
        except Exception as e:
            logger.error(f"备份损坏配置文件失败: {e}")

    def _get_default_config(self):
        return {
            "admin_password": None,
            "temp_password": None,
            "weekly_schedule": {
                "Monday": [{"start": "08:00", "end": "22:00"}],
                "Tuesday": [{"start": "08:00", "end": "22:00"}],
                "Wednesday": [{"start": "08:00", "end": "22:00"}],
                "Thursday": [{"start": "08:00", "end": "22:00"}],
                "Friday": [{"start": "08:00", "end": "22:00"}],
                "Saturday": [{"start": "09:00", "end": "23:00"}],
                "Sunday": [{"start": "09:00", "end": "22:00"}]
            },
            "temp_unlock_duration": 30,
            "warning_before_lock": 5,
            "whitelist_apps": [],
            "emergency_question": "你的出生年份是？",
            "emergency_answer": None,
            "usage_stats": {},
            "hotkeys": {
                "show_window": "ctrl+alt+a",
                "hide_window": "ctrl+alt+h",
                "immediate_lock": "ctrl+alt+l",
                "quit_program": "ctrl+alt+e"
            },
            "autostart_enabled": False,
            "encryption_version": "v3"
        }

    def save_config(self):
        try:
            config_data = json.dumps(self.config, ensure_ascii=False, indent=2)
            encrypted_data = self._encrypt_config(config_data)
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            logger.debug("配置文件已保存（加密）")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def _get_password_encryption_key(self):
        user_id = os.getlogin() if hasattr(os, 'getlogin') else "default"
        machine_id = self._get_machine_identifier()
        key_material = f"TimeManager_Pwd_Key_{user_id}_{machine_id}_Secure_2024".encode('utf-8')
        salt = b"TimeManager_Pwd_Salt_2024_32B"
        return PBKDF2(key_material, salt, dkLen=32, count=200000)

    def _encrypt_password(self, password):
        try:
            key = self._get_password_encryption_key()
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded = pad(password.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded)
            return base64.b64encode(iv + encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"加密密码失败: {e}")
            return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password, encrypted_data):
        try:
            if len(encrypted_data) == 64:
                return hashlib.sha256(password.encode()).hexdigest() == encrypted_data
            
            key = self._get_password_encryption_key()
            data = base64.b64decode(encrypted_data)
            iv = data[:16]
            encrypted = data[16:]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
            return decrypted.decode('utf-8') == password
        except Exception as e:
            logger.error(f"验证密码失败: {e}")
            return False

    def set_admin_password(self, password):
        self.config["admin_password"] = self._encrypt_password(password)
        self.config["encryption_version"] = "v3"
        self.save_config()
        logger.info("管理员密码已更新")

    def set_temp_password(self, password):
        self.config["temp_password"] = self._encrypt_password(password)
        self.config["encryption_version"] = "v3"
        self.save_config()
        logger.info("临时密码已更新")

    def verify_admin_password(self, password):
        stored = self.config.get("admin_password")
        if not stored:
            logger.warning("管理员密码未设置")
            return False
        
        result = self._verify_password(password, stored)
        logger.debug(f"管理员密码验证: {'成功' if result else '失败'}")
        return result

    def verify_temp_password(self, password):
        stored = self.config.get("temp_password")
        if not stored:
            logger.warning("临时密码未设置")
            return False
        
        result = self._verify_password(password, stored)
        logger.debug(f"临时密码验证: {'成功' if result else '失败'}")
        return result

    def get_weekly_schedule(self):
        return self.config.get("weekly_schedule", {})

    def set_weekly_schedule(self, schedule):
        self.config["weekly_schedule"] = schedule
        self.save_config()
        logger.info("时间计划已更新")

    def get_day_schedule(self, day_name):
        schedule = self.config.get("weekly_schedule", {}).get(day_name, [])
        if isinstance(schedule, dict):
            return [schedule]
        return schedule

    def is_passwords_configured(self):
        return bool(self.config.get("admin_password"))

    def is_temp_password_configured(self):
        return bool(self.config.get("temp_password"))

    def get_temp_unlock_duration(self):
        return self.config.get("temp_unlock_duration", 30)

    def set_temp_unlock_duration(self, duration):
        self.config["temp_unlock_duration"] = duration
        self.save_config()
        logger.info(f"临时解锁时长已设置为 {duration} 分钟")

    def get_warning_before_lock(self):
        return self.config.get("warning_before_lock", 5)

    def set_warning_before_lock(self, minutes):
        self.config["warning_before_lock"] = minutes
        self.save_config()
        logger.info(f"锁定前提醒时间已设置为 {minutes} 分钟")

    def get_whitelist_apps(self):
        return self.config.get("whitelist_apps", [])

    def set_whitelist_apps(self, apps):
        self.config["whitelist_apps"] = apps
        self.save_config()
        logger.info(f"白名单应用已更新，共 {len(apps)} 个")

    def get_emergency_question(self):
        return self.config.get("emergency_question", "你的出生年份是？")

    def set_emergency_question(self, question):
        self.config["emergency_question"] = question
        self.save_config()
        logger.info("安全问题已更新")

    def get_emergency_answer(self):
        return self.config.get("emergency_answer")

    def set_emergency_answer(self, answer):
        self.config["emergency_answer"] = self._encrypt_password(answer)
        self.save_config()
        logger.info("安全答案已更新")

    def verify_emergency_answer(self, answer):
        stored = self.config.get("emergency_answer")
        if not stored:
            return False
        return self._verify_password(answer, stored)

    def get_usage_stats(self):
        return self.config.get("usage_stats", {})

    def update_usage_stats(self, date_key, duration):
        if "usage_stats" not in self.config:
            self.config["usage_stats"] = {}

        if date_key not in self.config["usage_stats"]:
            self.config["usage_stats"][date_key] = 0

        self.config["usage_stats"][date_key] += duration
        self.save_config()

    def clear_usage_stats(self):
        self.config["usage_stats"] = {}
        self.save_config()
        logger.info("使用统计已清除")

    def get_autostart_enabled(self):
        return self.config.get("autostart_enabled", False)

    def set_autostart_enabled(self, enabled):
        self.config["autostart_enabled"] = enabled
        self.save_config()
        logger.info(f"开机自启已{'启用' if enabled else '禁用'}")

    def verify_old_admin_password(self, old_password):
        stored = self.config.get("admin_password")
        if not stored:
            return False
        return self._verify_password(old_password, stored)

    def get_hotkeys(self):
        return self.config.get("hotkeys", {
            "show_window": "ctrl+alt+a",
            "hide_window": "ctrl+alt+h",
            "immediate_lock": "ctrl+alt+l",
            "quit_program": "ctrl+alt+q"
        })

    def set_hotkey(self, action, hotkey):
        if "hotkeys" not in self.config:
            self.config["hotkeys"] = {}
        self.config["hotkeys"][action] = hotkey
        self.save_config()
        logger.info(f"快捷键 {action} 已设置为 {hotkey}")

    def get_config_path(self):
        return str(self.config_file)