#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
import time
from PIL import Image, ImageDraw

from src.logger import logger

try:
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False
    logger.warning("pystray 模块未安装，系统托盘功能不可用")


class SystemTrayIcon:
    def __init__(self, main_window):
        self.main_window = main_window
        self.icon = None
        self.last_click_time = 0
        self.double_click_threshold = 0.3
        self.setup_tray()

    def setup_tray(self):
        if HAS_TRAY:
            try:
                logger.info("开始设置系统托盘...")
                image = self.create_icon_image()
                if image is None:
                    logger.error("无法创建托盘图标图像")
                    return

                from pystray import MenuItem as item
                menu = (
                    item('打开设置', lambda i, s: self.show_main_window()),
                    item('隐藏窗口', lambda i, s: self._menu_hide_window()),
                    item('查看状态', lambda i, s: self._menu_show_status()),
                    item('立即锁定', lambda i, s: self._menu_lock()),
                    item('退出程序', lambda i, s: self._menu_quit())
                )

                self.icon = pystray.Icon("TimeManager", image, "小灵控制屏幕保护程序", menu)
                self.icon._menu = menu

                def run_icon():
                    try:
                        logger.info("系统托盘线程启动...")
                        self.icon.run(
                            on_click=lambda icon, event: self._on_icon_click(icon, event)
                        )
                        logger.info("系统托盘线程结束")
                    except Exception as e:
                        logger.error(f"系统托盘运行出错: {e}")

                thread = threading.Thread(target=run_icon, daemon=True)
                thread.start()

                logger.info("系统托盘设置完成")

            except Exception as e:
                logger.error(f"系统托盘设置失败: {e}")
        else:
            logger.warning("系统托盘功能需要安装 pystray 和 Pillow")

    def _on_icon_click(self, icon, event):
        try:
            current_time = time.time()
            time_since_last_click = current_time - self.last_click_time
            
            if time_since_last_click < self.double_click_threshold:
                logger.info("双击托盘图标")
                self.show_main_window()
            else:
                logger.debug("单击托盘图标，显示菜单")
            
            self.last_click_time = current_time
        except Exception as e:
            logger.error(f"处理图标点击失败: {e}")

    def create_icon_image(self):
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'logo.ico')
            icon_path = os.path.abspath(icon_path)
            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                return image
            
            image = Image.new('RGB', (64, 64), color=(78, 204, 163))
            draw = ImageDraw.Draw(image)
            draw.ellipse((10, 10, 54, 54), fill=(26, 26, 46))
            draw.text((18, 20), "T", fill=(255, 255, 255))
            return image
        except Exception as e:
            logger.error(f"创建托盘图标失败: {e}")
            return None

    def show_main_window(self):
        logger.info("显示主窗口...")
        try:
            self.main_window.root.after(0, self._show_main_window_internal)
        except Exception as e:
            logger.error(f"显示窗口失败: {e}")

    def _show_main_window_internal(self):
        try:
            if not self.main_window.config_manager.is_passwords_configured():
                logger.info("未设置密码，允许打开设置")
                self._do_show_main_window()
                return

            password = self.main_window.show_password_dialog("请输入管理员密码打开设置")

            if password is None:
                logger.info("用户取消打开设置")
                return

            if password and self.main_window.config_manager.verify_admin_password(password):
                logger.info("密码验证成功，显示主窗口")
                self._do_show_main_window()
            else:
                logger.warning("密码验证失败")
                self.main_window.show_error_dialog("密码错误", "管理员密码不正确！")
        except Exception as e:
            logger.error(f"显示窗口内部错误: {e}")

    def _do_show_main_window(self):
        try:
            self.main_window.root.deiconify()
            self.main_window.root.lift()
            self.main_window.root.focus_force()
            self.main_window.root.state('normal')
            logger.info("主窗口已显示")
        except Exception as e:
            logger.error(f"显示窗口内部错误: {e}")

    def _menu_hide_window(self):
        try:
            self.main_window.root.after(0, self._menu_hide_window_internal)
        except Exception as e:
            logger.error(f"隐藏窗口失败: {e}")

    def _menu_hide_window_internal(self):
        try:
            self.main_window.root.withdraw()
            logger.info("主窗口已隐藏")
        except Exception as e:
            logger.error(f"隐藏窗口内部错误: {e}")

    def _menu_show_status(self):
        try:
            self.main_window.root.after(0, self._menu_show_status_internal)
        except Exception as e:
            logger.error(f"显示状态失败: {e}")

    def _menu_show_status_internal(self):
        try:
            is_locked = self.main_window.time_checker.is_locked_time()
            status = "当前状态: 已锁定" if is_locked else "当前状态: 可用"
            self.main_window.show_info_dialog("状态", status)
        except Exception as e:
            logger.error(f"显示状态内部错误: {e}")

    def _menu_lock(self):
        try:
            self.main_window.root.after(0, self._menu_lock_internal)
        except Exception as e:
            logger.error(f"立即锁定失败: {e}")

    def _menu_lock_internal(self):
        try:
            self.main_window.immediate_lock(manual=True)
        except Exception as e:
            logger.error(f"立即锁定内部错误: {e}")

    def _menu_quit(self):
        logger.info("从菜单退出程序...")
        try:
            self.main_window.root.after(0, self._menu_quit_internal)
        except Exception as e:
            logger.error(f"退出程序失败: {e}")

    def _menu_quit_internal(self):
        try:
            if not self.main_window.config_manager.is_passwords_configured():
                logger.info("未设置密码，允许退出")
                self.do_exit()
                return

            password = self.main_window.show_password_dialog("请输入管理员密码退出程序")

            if password is None:
                logger.info("用户取消退出")
                return

            if password and self.main_window.config_manager.verify_admin_password(password):
                logger.info("密码验证成功，执行退出")
                self.do_exit()
            else:
                logger.warning("密码验证失败")
                self.main_window.show_error_dialog("密码错误", "管理员密码不正确！")

        except Exception as e:
            logger.error(f"退出程序出错: {e}")

    def do_exit(self):
        try:
            self.main_window.running = False
            if self.icon:
                self.icon.stop()
            self.main_window.safe_exit()
        except Exception as e:
            logger.error(f"执行退出出错: {e}")
            self.main_window.running = False
            self.main_window.safe_exit()