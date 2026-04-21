#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from src.time_checker import TimeChecker
from src.logger import logger


class LockScreen:
    def __init__(self, config_manager, parent_window, setup_mode=False):
        self.config_manager = config_manager
        self.time_checker = TimeChecker(config_manager)
        self.parent_window = parent_window
        self.setup_mode = setup_mode
        self.window = tk.Toplevel(parent_window.root if parent_window else None)
        self.setup_lock_screen()
        logger.info(f"锁定屏幕已创建 (设置模式: {setup_mode})")

    def setup_lock_screen(self):
        self.window.title("小灵控制 - 已锁定")
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='#1a1a2e')
        self.window.bind('<Escape>', lambda e: None)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        main_frame = tk.Frame(self.window, bg='#1a1a2e')

        if self.setup_mode:
            self._setup_initial_mode(main_frame)
            return

        self._setup_lock_mode(main_frame)

    def _setup_initial_mode(self, main_frame):
        title_label = tk.Label(
            main_frame,
            text="首次设置",
            font=('Arial', 32, 'bold'),
            bg='#1a1a2e',
            fg='#4ecca3'
        )
        title_label.pack(pady=(20, 30))

        message_label = tk.Label(
            main_frame,
            text="请先设置管理员密码和临时退出密码。",
            font=('Arial', 18),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        message_label.pack(pady=(0, 30))

        self.admin_password_var = tk.StringVar()
        self.admin_confirm_var = tk.StringVar()
        self.temp_password_var = tk.StringVar()
        self.temp_confirm_var = tk.StringVar()

        admin_label = tk.Label(
            main_frame,
            text="管理员密码:",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        admin_label.pack(pady=(0, 10))
        admin_entry = tk.Entry(
            main_frame,
            textvariable=self.admin_password_var,
            show='*',
            font=('Arial', 14),
            width=25
        )
        admin_entry.pack(pady=(0, 10))

        admin_confirm_label = tk.Label(
            main_frame,
            text="确认管理员密码:",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        admin_confirm_label.pack(pady=(0, 10))
        admin_confirm_entry = tk.Entry(
            main_frame,
            textvariable=self.admin_confirm_var,
            show='*',
            font=('Arial', 14),
            width=25
        )
        admin_confirm_entry.pack(pady=(0, 10))

        temp_label = tk.Label(
            main_frame,
            text="临时退出密码:",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        temp_label.pack(pady=(0, 10))
        temp_entry = tk.Entry(
            main_frame,
            textvariable=self.temp_password_var,
            show='*',
            font=('Arial', 14),
            width=25
        )
        temp_entry.pack(pady=(0, 10))

        temp_confirm_label = tk.Label(
            main_frame,
            text="确认临时密码:",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        temp_confirm_label.pack(pady=(0, 10))
        temp_confirm_entry = tk.Entry(
            main_frame,
            textvariable=self.temp_confirm_var,
            show='*',
            font=('Arial', 14),
            width=25
        )
        temp_confirm_entry.pack(pady=(0, 20))

        save_btn = tk.Button(
            main_frame,
            text="保存并继续",
            command=self.save_initial_settings,
            font=('Arial', 16, 'bold'),
            bg='#4ecca3',
            fg='#1a1a2e',
            relief='flat',
            width=20,
            height=2
        )
        save_btn.pack(pady=(0, 10))
        main_frame.place(relx=0.5, rely=0.5, anchor='center')

    def _setup_lock_mode(self, main_frame):
        title_label = tk.Label(
            main_frame,
            text="⏰ 小灵控制",
            font=('Arial', 32, 'bold'),
            bg='#1a1a2e',
            fg='#4ecca3'
        )
        title_label.pack(pady=(20, 30))

        message_label = tk.Label(
            main_frame,
            text="当前不在允许使用的时间范围内",
            font=('Arial', 18),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        message_label.pack(pady=(0, 30))

        self.time_label = tk.Label(
            main_frame,
            text="",
            font=('Consolas', 48),
            bg='#1a1a2e',
            fg='#4ecca3'
        )
        self.time_label.pack(pady=(0, 20))

        self.next_unlock_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 12),
            bg='#1a1a2e',
            fg='#a8a8a8'
        )
        self.next_unlock_label.pack(pady=(0, 50))

        password_label = tk.Label(
            main_frame,
            text="输入临时密码解锁:",
            font=('Arial', 14),
            bg='#1a1a2e',
            fg='#ffffff'
        )
        password_label.pack(pady=(0, 10))

        self.password_var = tk.StringVar()
        password_entry = tk.Entry(
            main_frame,
            textvariable=self.password_var,
            show='*',
            font=('Arial', 14),
            width=25
        )
        password_entry.pack(pady=(0, 20))
        password_entry.bind('<Return>', lambda e: self.try_unlock())
        password_entry.focus()

        unlock_btn = tk.Button(
            main_frame,
            text="临时解锁",
            command=self.try_unlock,
            font=('Arial', 16, 'bold'),
            bg='#4ecca3',
            fg='#1a1a2e',
            relief='flat',
            width=20,
            height=2
        )
        unlock_btn.pack(pady=(0, 10))

        btn_frame = tk.Frame(main_frame, bg='#1a1a2e')
        btn_frame.pack(pady=(0, 5))

        emergency_btn = tk.Button(
            btn_frame,
            text="紧急解锁",
            command=self.show_emergency_unlock,
            font=('Arial', 12),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            width=15
        )
        emergency_btn.pack(side='left', padx=(0, 10))

        shutdown_btn = tk.Button(
            btn_frame,
            text="关机",
            command=self.show_shutdown_dialog,
            font=('Arial', 12),
            bg='#6c757d',
            fg='white',
            relief='flat',
            width=15
        )
        shutdown_btn.pack(side='left')

        main_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.update_time_display()
        self.window.after(1000, self.update_time_display)
        self.window.after(5000, self.check_auto_unlock)

    def update_time_display(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)

        next_unlock = self.time_checker.get_next_unlock_time()
        if next_unlock:
            time_diff = next_unlock - datetime.now()
            hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            self.next_unlock_label.config(
                text=f"下次可用时间: {next_unlock.strftime('%H:%M')} (还需等待 {hours}小时{minutes}分钟)"
            )
        else:
            self.next_unlock_label.config(text="当前在允许使用的时间范围内")

        self.window.after(1000, self.update_time_display)

    def check_auto_unlock(self):
        if not self.time_checker.is_locked_time():
            logger.info("时间检查通过，自动解锁")
            self.close()
        else:
            self.window.after(5000, self.check_auto_unlock)

    def try_unlock(self):
        password = self.password_var.get()
        if not password:
            return

        if self.config_manager.verify_temp_password(password):
            self.password_var.set("")
            self.close()
            if self.parent_window:
                self.parent_window.temp_unlock()
            logger.info("临时密码解锁成功")
        elif self.config_manager.verify_admin_password(password):
            self.password_var.set("")
            self.close()
            if self.parent_window:
                self.parent_window.root.deiconify()
            logger.info("管理员密码解锁成功")
        else:
            self.password_var.set("")
            messagebox.showwarning("密码错误", "密码不正确，请重试。")
            logger.warning("密码验证失败")

    def show_emergency_unlock(self):
        emergency_window = tk.Toplevel(self.window)
        emergency_window.title("紧急解锁")
        emergency_window.geometry("400x300")
        emergency_window.attributes('-topmost', True)
        emergency_window.transient(self.window)
        emergency_window.protocol("WM_DELETE_WINDOW", emergency_window.withdraw)

        question_label = tk.Label(
            emergency_window,
            text=f"安全问题: {self.config_manager.get_emergency_question()}",
            font=('Arial', 12),
            wraplength=350
        )
        question_label.pack(pady=20)

        answer_label = tk.Label(emergency_window, text="请输入答案:")
        answer_label.pack(pady=5)

        answer_var = tk.StringVar()
        answer_entry = ttk.Entry(emergency_window, textvariable=answer_var, width=30)
        answer_entry.pack(pady=5)
        answer_entry.focus()

        def check_answer():
            if self.config_manager.verify_emergency_answer(answer_var.get()):
                emergency_window.destroy()
                self.close()
                if self.parent_window:
                    self.parent_window.root.deiconify()
                logger.info("紧急解锁成功")
            else:
                messagebox.showwarning("错误", "答案不正确！")
                logger.warning("紧急解锁答案验证失败")

        btn = ttk.Button(emergency_window, text="解锁", command=check_answer)
        btn.pack(pady=20)

        emergency_window.bind('<Return>', lambda e: check_answer())

    def show_shutdown_dialog(self):
        result = messagebox.askyesno("确认关机", "确定要关闭计算机吗？")
        if result:
            logger.info("用户确认关机")
            try:
                import subprocess
                if os.name == 'nt':
                    subprocess.call(['shutdown', '/s', '/f', '/t', '0'])
                else:
                    subprocess.call(['shutdown', '-h', 'now'])
            except Exception as e:
                logger.error(f"关机失败: {e}")
                messagebox.showerror("错误", "无法执行关机操作")

    def close(self):
        try:
            self.window.destroy()
            logger.info("锁定屏幕已关闭")
        except Exception as e:
            logger.error(f"关闭锁定屏幕失败: {e}")

    def save_initial_settings(self):
        admin_pwd = self.admin_password_var.get().strip()
        admin_confirm = self.admin_confirm_var.get().strip()
        temp_pwd = self.temp_password_var.get().strip()
        temp_confirm = self.temp_confirm_var.get().strip()

        if not admin_pwd or not temp_pwd:
            messagebox.showwarning("错误", "管理员密码和临时密码都不能为空！")
            return

        if admin_pwd != admin_confirm:
            messagebox.showwarning("错误", "管理员密码两次输入不一致！")
            return

        if temp_pwd != temp_confirm:
            messagebox.showwarning("错误", "临时密码两次输入不一致！")
            return

        self.config_manager.set_admin_password(admin_pwd)
        self.config_manager.set_temp_password(temp_pwd)

        messagebox.showinfo("成功", "密码设置已保存！")
        logger.info("初始密码设置完成")

        if self.parent_window:
            try:
                self.parent_window.root.deiconify()
                self.parent_window.root.lift()
                self.parent_window.root.focus_force()
                try:
                    self.parent_window.root.state('normal')
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"恢复主窗口失败: {e}")

        self.close()

    def on_close(self):
        try:
            self.window.withdraw()
        except Exception:
            pass
