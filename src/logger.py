#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from datetime import datetime


class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_level=logging.INFO):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('TimeManager')
        self.logger.setLevel(log_level)
        self.logger.propagate = False
        
        self._setup_handlers()

    def _setup_handlers(self):
        log_dir = Path(self._get_app_data_dir()) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"timemanager_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(
            log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _get_app_data_dir(self):
        if os.name == 'nt':
            return os.path.join(os.environ.get('APPDATA', '.'), 'TimeManager')
        else:
            return os.path.join(os.path.expanduser('~'), '.timemanager')

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


logger = Logger()
