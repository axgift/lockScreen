#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.logger import logger

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    logger.warning("keyboard 模块未安装，快捷键功能不可用")


class HotkeyManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.hotkeys = {}
        if HAS_KEYBOARD:
            self.setup_hotkeys()
        else:
            logger.warning("快捷键功能需要安装 keyboard 包")

    def _check_hotkey_conflict(self, hotkey):
        try:
            all_hotkeys = keyboard._hotkeys
            for existing_hotkey in all_hotkeys:
                if existing_hotkey[0] == hotkey:
                    return True
            return False
        except Exception:
            return False

    def setup_hotkeys(self):
        try:
            hotkey_config = self.main_window.config_manager.get_hotkeys()

            self.clear_hotkeys()

            self.hotkeys['show_window'] = hotkey_config.get('show_window', 'ctrl+alt+a')
            self.hotkeys['hide_window'] = hotkey_config.get('hide_window', 'ctrl+alt+h')
            self.hotkeys['immediate_lock'] = hotkey_config.get('immediate_lock', 'ctrl+alt+l')
            self.hotkeys['quit_program'] = hotkey_config.get('quit_program', 'ctrl+alt+q')

            for action, hotkey in self.hotkeys.items():
                if self._check_hotkey_conflict(hotkey):
                    logger.warning(f"快捷键冲突检测: {hotkey} 已被其他程序占用")
                
                try:
                    keyboard.add_hotkey(hotkey, getattr(self, action))
                except Exception as e:
                    logger.error(f"注册快捷键 {hotkey} 失败: {e}")

            if not self._check_hotkey_conflict('ctrl+alt+shift+q'):
                keyboard.add_hotkey('ctrl+alt+shift+q', self.force_exit)
            else:
                logger.warning("强制退出快捷键 ctrl+alt+shift+q 已被占用")

            logger.info(f"快捷键已设置: {self.hotkeys}")
            logger.info("强制退出快捷键: ctrl+alt+shift+q")
        except Exception as e:
            logger.error(f"设置快捷键失败: {e}")

    def show_window(self):
        logger.info("快捷键触发：显示窗口")
        try:
            self.main_window.root.deiconify()
            self.main_window.root.lift()
            self.main_window.root.focus_force()
            self.main_window.root.state('normal')
        except Exception as e:
            logger.error(f"显示窗口失败: {e}")

    def hide_window(self):
        logger.info("快捷键触发：隐藏窗口")
        try:
            self.main_window.root.withdraw()
        except Exception as e:
            logger.error(f"隐藏窗口失败: {e}")

    def immediate_lock(self):
        logger.info("快捷键触发：立即锁定")
        try:
            self.main_window.immediate_lock(manual=True)
        except Exception as e:
            logger.error(f"立即锁定失败: {e}")

    def quit_program(self):
        logger.info("快捷键触发：退出程序")
        try:
            self.main_window.quit_program_from_hotkey()
        except Exception as e:
            logger.error(f"快捷键退出失败: {e}")

    def do_exit(self):
        try:
            self.main_window.running = False
            self.clear_hotkeys()
            self.main_window.safe_exit()
        except Exception as e:
            logger.error(f"执行退出出错: {e}")
            self.main_window.running = False
            self.main_window.safe_exit()

    def clear_hotkeys(self):
        if not HAS_KEYBOARD:
            return
        try:
            keyboard.unhook_all_hotkeys()
            logger.info("已清除所有快捷键")
        except AttributeError:
            logger.debug("清除快捷键时出现属性错误，可能是还未注册快捷键")
        except Exception as e:
            logger.error(f"清除快捷键失败: {e}")

    def reload_hotkeys(self):
        if HAS_KEYBOARD:
            self.clear_hotkeys()
            self.setup_hotkeys()

    def force_exit(self):
        logger.info("强制退出程序...")
        try:
            self.main_window.running = False
            self.clear_hotkeys()
            self.main_window.safe_exit()
        except Exception as e:
            logger.error(f"强制退出出错: {e}")
            self.main_window.running = False
            self.main_window.safe_exit()