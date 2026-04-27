#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta

from src.config.config_manager import ConfigManager
from src.time_checker import TimeChecker
from src.lock_screen import LockScreen
from src.hotkey_manager import HotkeyManager
from src.system_tray import SystemTrayIcon
from src.process_protector import ProcessProtector
from src.usage_tracker import UsageTracker
from src.whitelist_manager import WhitelistManager
from src.auto_starter import AutoStarter
from src.logger import logger


class MainWindow:
    def __init__(self):
        logger.info("初始化主窗口...")
        
        self.config_manager = ConfigManager()
        self.time_checker = TimeChecker(self.config_manager)
        self.lock_screen = None
        self.running = True

        self.temp_unlock_end_time = None
        self.usage_tracker = UsageTracker(self.config_manager)
        self.whitelist_manager = WhitelistManager(self.config_manager)

        self.root = tk.Tk()
        self.root.withdraw()
        self.setup_ui()
        self.setup_hotkeys()
        self.setup_system_tray()
        self.setup_autostart()
        self.setup_process_protection()
        self.check_first_run()
        self.setup_time_check()
        self.setup_usage_tracking()
        self.setup_warning_system()
        
        logger.info("主窗口初始化完成")

    def setup_hotkeys(self):
        try:
            self.hotkey_manager = HotkeyManager(self)
            logger.info("快捷键管理器已初始化")
        except Exception as e:
            logger.error(f"设置快捷键失败: {e}")
            self.hotkey_manager = None

    def setup_ui(self):
        self.root.title("小灵控制屏幕保护程序")
        window_width = 900
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='#f0f0f0')
        
        try:
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'logo.ico')
            else:
                icon_path = os.path.join(os.path.dirname(__file__), '..', 'logo.ico')
            icon_path = os.path.abspath(icon_path)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                logger.warning(f"图标文件不存在: {icon_path}")
        except Exception as e:
            logger.warning(f"加载图标失败: {e}")

        self.time_inputs = {}

        title_label = tk.Label(
            self.root,
            text="小灵控制屏幕保护程序",
            font=('Arial', 18, 'bold'),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=20)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        self.setup_time_tab(notebook)
        self.setup_password_tab(notebook)
        self.setup_stats_tab(notebook)
        self.setup_whitelist_tab(notebook)
        self.setup_system_tab(notebook)
        self.setup_about_tab(notebook)

        bottom_frame = tk.Frame(self.root, bg='#f0f0f0', height=60)
        bottom_frame.pack(fill='x', side='bottom')

        btn_frame = tk.Frame(bottom_frame, bg='#f0f0f0')
        btn_frame.pack(pady=10)

        close_btn = tk.Button(
            btn_frame,
            text="关闭窗口（程序继续运行）",
            command=self.close_main_window,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 11),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        close_btn.pack(side='left', padx=5)

        exit_btn = tk.Button(
            btn_frame,
            text="退出软件",
            command=self.quit_program_from_button,
            bg='#3498db',
            fg='white',
            font=('Arial', 11),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        exit_btn.pack(side='left', padx=5)

    def close_main_window(self):
        logger.info("关闭主窗口，程序继续运行...")
        try:
            self.root.withdraw()
        except Exception as e:
            logger.error(f"隐藏窗口失败: {e}")

    def setup_time_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='时间设置')

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)

        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
        day_names_cn = ["星期一", "星期二", "星期三", "星期四",
                       "星期五", "星期六", "星期日"]

        self.time_inputs = {}

        for idx, (day, day_cn) in enumerate(zip(days, day_names_cn)):
            group = ttk.LabelFrame(
                scrollable_frame,
                text=f"{day} ({day_cn})",
                padding=10
            )
            group.pack(fill='x', padx=10, pady=5)

            schedule = self.config_manager.get_day_schedule(day)
            
            if isinstance(schedule, dict):
                schedules = [schedule]
            else:
                schedules = schedule if isinstance(schedule, list) else []
            
            self.time_inputs[day] = []
            day_frame = ttk.Frame(group)
            day_frame.pack(fill='x')

            for time_slot in schedules:
                self._add_time_slot_row(day_frame, day, time_slot.get("start", "08:00"), time_slot.get("end", "22:00"))

            btn_area = ttk.Frame(group)
            btn_area.pack(fill='x', pady=5)
            
            add_btn = ttk.Button(
                btn_area,
                text="添加时间段",
                command=lambda d=day, df=day_frame: self._add_time_slot_row(df, d, "08:00", "22:00")
            )
            add_btn.pack(side='left', padx=5)

        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill='x', padx=20, pady=10)

        save_btn = ttk.Button(
            btn_frame,
            text="保存时间设置",
            command=self.save_time_schedule
        )
        save_btn.pack(pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _add_time_slot_row(self, parent_frame, day, default_start, default_end):
        row_frame = ttk.Frame(parent_frame)
        row_frame.pack(fill='x', pady=2)

        ttk.Label(row_frame, text="可用开始时间:").pack(side='left', padx=5)
        start_var = tk.StringVar(value=default_start)
        start_entry = ttk.Entry(row_frame, textvariable=start_var, width=10)
        start_entry.pack(side='left', padx=5)

        ttk.Label(row_frame, text="可用结束时间:").pack(side='left', padx=5)
        end_var = tk.StringVar(value=default_end)
        end_entry = ttk.Entry(row_frame, textvariable=end_var, width=10)
        end_entry.pack(side='left', padx=5)

        def remove_slot():
            self.time_inputs[day].remove((start_var, end_var))
            row_frame.destroy()

        remove_btn = ttk.Button(
            row_frame,
            text="删除",
            command=remove_slot
        )
        remove_btn.pack(side='left', padx=5)

        self.time_inputs[day].append((start_var, end_var))

    def setup_password_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='密码设置')

        main_container = ttk.Frame(frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        password_group = ttk.LabelFrame(main_container, text="密码管理", padding=20)
        password_group.pack(fill='x', pady=(0, 10))

        ttk.Label(password_group, text="旧管理员密码:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        self.old_password_entry = ttk.Entry(password_group, show='*', width=30)
        self.old_password_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(password_group, text="新管理员密码:").grid(row=1, column=0, sticky='e', pady=5, padx=5)
        self.admin_password_entry = ttk.Entry(password_group, show='*', width=30)
        self.admin_password_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(password_group, text="确认新密码:").grid(row=2, column=0, sticky='e', pady=5, padx=5)
        self.admin_confirm_entry = ttk.Entry(password_group, show='*', width=30)
        self.admin_confirm_entry.grid(row=2, column=1, pady=5, padx=5)

        ttk.Label(password_group, text="临时退出密码:").grid(row=3, column=0, sticky='e', pady=5, padx=5)
        self.temp_password_entry = ttk.Entry(password_group, show='*', width=30)
        self.temp_password_entry.grid(row=3, column=1, pady=5, padx=5)

        ttk.Label(password_group, text="确认临时密码:").grid(row=4, column=0, sticky='e', pady=5, padx=5)
        self.temp_confirm_entry = ttk.Entry(password_group, show='*', width=30)
        self.temp_confirm_entry.grid(row=4, column=1, pady=5, padx=5)

        emergency_group = ttk.LabelFrame(main_container, text="紧急解锁设置", padding=20)
        emergency_group.pack(fill='x', pady=10)

        ttk.Label(emergency_group, text="安全问题:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        self.emergency_question_entry = ttk.Entry(emergency_group, width=30)
        self.emergency_question_entry.insert(0, self.config_manager.get_emergency_question())
        self.emergency_question_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(emergency_group, text="安全答案:").grid(row=1, column=0, sticky='e', pady=5, padx=5)
        self.emergency_answer_entry = ttk.Entry(emergency_group, show='*', width=30)
        self.emergency_answer_entry.grid(row=1, column=1, pady=5, padx=5)

        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill='x', pady=10)

        save_btn = ttk.Button(
            btn_frame,
            text="保存密码设置",
            command=self.save_passwords
        )
        save_btn.pack(pady=5)

    def setup_system_tray(self):
        self.tray_icon = SystemTrayIcon(self)

    def setup_autostart(self):
        if self.config_manager.get_autostart_enabled():
            AutoStarter.set_autostart(True)
            logger.info("开机自启已启用")

    def setup_process_protection(self):
        self.process_protector = ProcessProtector(self.config_manager)
        self.process_protector.start_monitoring()

    def setup_usage_tracking(self):
        if self.config_manager.is_passwords_configured():
            self.usage_tracker.start_tracking()
            logger.info("使用跟踪已开始")

    def setup_warning_system(self):
        self.warning_shown = False
        self.check_warning()

    def check_warning(self):
        if self.config_manager.is_passwords_configured():
            warning_minutes = self.config_manager.get_warning_before_lock()
            next_lock = self.get_next_lock_time()

            if next_lock:
                time_until_lock = (next_lock - datetime.now()).total_seconds() / 60

                if 0 < time_until_lock <= warning_minutes and not self.warning_shown:
                    self.show_warning_dialog()
                    self.warning_shown = True
                elif time_until_lock > warning_minutes:
                    self.warning_shown = False

        self.root.after(60000, self.check_warning)

    def get_next_lock_time(self):
        return self.time_checker.get_next_lock_time()

    def show_warning_dialog(self):
        warning_window = tk.Toplevel(self.root)
        warning_window.title("锁定提醒")
        
        window_width = 500
        window_height = 300
        screen_width = warning_window.winfo_screenwidth()
        screen_height = warning_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        warning_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        warning_window.attributes('-topmost', True)
        warning_window.configure(bg='#1a1a2e')
        warning_window.protocol("WM_DELETE_WINDOW", warning_window.withdraw)

        main_frame = tk.Frame(warning_window, bg='#1a1a2e')
        main_frame.pack(expand=True)

        warning_label = tk.Label(
            main_frame,
            text="⚠️ 即将锁定",
            font=('Arial', 28, 'bold'),
            fg='red',
            bg='#1a1a2e'
        )
        warning_label.pack(pady=20)

        msg_label = tk.Label(
            main_frame,
            text=f"将在{self.config_manager.get_warning_before_lock()}分钟后锁定屏幕\n请保存您的工作",
            font=('Arial', 14),
            fg='white',
            bg='#1a1a2e'
        )
        msg_label.pack(pady=15)

        btn = tk.Button(
            main_frame,
            text="知道了",
            command=warning_window.destroy,
            font=('Arial', 12, 'bold'),
            bg='#4ecca3',
            fg='#1a1a2e',
            relief='flat',
            width=15,
            height=2
        )
        btn.pack(pady=20)

    def check_first_run(self):
        if not self.config_manager.is_passwords_configured():
            logger.info("首次运行，显示设置窗口")
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.root.state('normal')

    def save_time_schedule(self):
        schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]

        for day in days:
            time_slots = []
            for start_var, end_var in self.time_inputs[day]:
                time_slots.append({
                    "start": start_var.get(),
                    "end": end_var.get()
                })
            schedule[day] = time_slots

        self.config_manager.set_weekly_schedule(schedule)
        messagebox.showinfo("成功", "时间设置已保存！")

    def save_passwords(self):
        old_pwd = self.old_password_entry.get()
        admin_pwd = self.admin_password_entry.get()
        admin_confirm = self.admin_confirm_entry.get()
        temp_pwd = self.temp_password_entry.get()
        temp_confirm = self.temp_confirm_entry.get()
        emergency_question = self.emergency_question_entry.get()
        emergency_answer = self.emergency_answer_entry.get()

        if admin_pwd:
            if old_pwd and not self.config_manager.verify_old_admin_password(old_pwd):
                messagebox.showwarning("错误", "旧密码不正确！")
                return
            if admin_pwd != admin_confirm:
                messagebox.showwarning("错误", "管理员密码两次输入不一致！")
                return
            self.config_manager.set_admin_password(admin_pwd)

        if temp_pwd:
            if temp_pwd != temp_confirm:
                messagebox.showwarning("错误", "临时密码两次输入不一致！")
                return
            self.config_manager.set_temp_password(temp_pwd)

        if emergency_question and emergency_answer:
            self.config_manager.set_emergency_question(emergency_question)
            self.config_manager.set_emergency_answer(emergency_answer)

        self.old_password_entry.delete(0, tk.END)
        self.admin_password_entry.delete(0, tk.END)
        self.admin_confirm_entry.delete(0, tk.END)
        self.temp_password_entry.delete(0, tk.END)
        self.temp_confirm_entry.delete(0, tk.END)
        self.emergency_answer_entry.delete(0, tk.END)

        messagebox.showinfo("成功", "密码设置已保存！")

    def setup_stats_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='使用统计')

        container = ttk.Frame(frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)

        info_label = ttk.Label(container, text="每日使用时间统计（分钟）")
        info_label.pack(pady=(0, 20))

        self.stats_text = tk.Text(container, height=20, width=60, font=('Consolas', 10))
        self.stats_text.pack(fill='both', expand=True)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill='x', pady=10)

        refresh_btn = ttk.Button(btn_frame, text="刷新统计", command=self.refresh_stats)
        refresh_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(btn_frame, text="清除统计", command=self.clear_stats)
        clear_btn.pack(side='left', padx=5)

        self.refresh_stats()

    def refresh_stats(self):
        self.stats_text.delete(1.0, tk.END)
        stats = self.config_manager.get_usage_stats()

        if not stats:
            self.stats_text.insert(tk.END, "暂无使用统计数据")
            return

        self.stats_text.insert(tk.END, "日期\t\t使用时间（分钟）\n")
        self.stats_text.insert(tk.END, "-" * 50 + "\n")

        total_minutes = 0
        for date, minutes in sorted(stats.items()):
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            self.stats_text.insert(tk.END, f"{date}\t{hours}小时{mins}分钟\n")
            total_minutes += minutes

        total_hours = int(total_minutes // 60)
        total_mins = int(total_minutes % 60)
        self.stats_text.insert(tk.END, "-" * 50 + "\n")
        self.stats_text.insert(tk.END, f"总计:\t\t{total_hours}小时{total_mins}分钟\n")

    def clear_stats(self):
        if messagebox.askyesno("确认", "确定要清除所有使用统计数据吗？"):
            self.config_manager.clear_usage_stats()
            self.refresh_stats()

    def setup_whitelist_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='白名单应用')

        container = ttk.Frame(frame)
        container.pack(fill='both', expand=True, padx=20, pady=20)

        info_label = ttk.Label(container, text="白名单应用可以在锁定时间继续使用")
        info_label.pack(pady=(0, 10))

        whitelist_frame = ttk.LabelFrame(container, text="当前白名单", padding=10)
        whitelist_frame.pack(fill='both', expand=True)

        self.whitelist_listbox = tk.Listbox(whitelist_frame, height=10)
        self.whitelist_listbox.pack(fill='both', expand=True, padx=5, pady=5)

        scroll = ttk.Scrollbar(whitelist_frame, orient="vertical", command=self.whitelist_listbox.yview)
        scroll.pack(side='right', fill='y')
        self.whitelist_listbox.config(yscrollcommand=scroll.set)

        add_frame = ttk.Frame(container)
        add_frame.pack(fill='x', pady=10)

        ttk.Label(add_frame, text="应用程序:").pack(side='left', padx=5)
        self.whitelist_entry = ttk.Entry(add_frame, width=40)
        self.whitelist_entry.pack(side='left', padx=5)

        browse_btn = ttk.Button(add_frame, text="浏览...", command=self.browse_app)
        browse_btn.pack(side='left', padx=5)

        add_btn = ttk.Button(add_frame, text="添加", command=self.add_whitelist_app)
        add_btn.pack(side='left', padx=5)

        remove_btn = ttk.Button(add_frame, text="移除选中", command=self.remove_whitelist_app)
        remove_btn.pack(side='left', padx=5)

        self.refresh_whitelist()

    def refresh_whitelist(self):
        self.whitelist_listbox.delete(0, tk.END)
        for app in self.config_manager.get_whitelist_apps():
            self.whitelist_listbox.insert(tk.END, app)

    def add_whitelist_app(self):
        app_name = self.whitelist_entry.get().strip()
        if app_name:
            whitelist = self.config_manager.get_whitelist_apps()
            if app_name not in whitelist:
                whitelist.append(app_name)
                self.config_manager.set_whitelist_apps(whitelist)
                self.refresh_whitelist()
                self.whitelist_entry.delete(0, tk.END)

    def browse_app(self):
        file_path = filedialog.askopenfilename(
            title="选择应用程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if file_path:
            app_name = os.path.basename(file_path)
            self.whitelist_entry.delete(0, tk.END)
            self.whitelist_entry.insert(0, app_name)

    def remove_whitelist_app(self):
        selection = self.whitelist_listbox.curselection()
        if selection:
            index = selection[0]
            whitelist = self.config_manager.get_whitelist_apps()
            del whitelist[index]
            self.config_manager.set_whitelist_apps(whitelist)
            self.refresh_whitelist()

    def setup_system_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='系统设置')

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        autostart_group = ttk.LabelFrame(scrollable_frame, text="开机自启动", padding=20)
        autostart_group.pack(fill='x', pady=(10, 10), padx=20)

        self.autostart_var = tk.BooleanVar(value=self.config_manager.get_autostart_enabled())
        autostart_check = ttk.Checkbutton(
            autostart_group,
            text="启用开机自启动",
            variable=self.autostart_var,
            command=self.toggle_autostart
        )
        autostart_check.pack(anchor='w')

        temp_unlock_group = ttk.LabelFrame(scrollable_frame, text="临时解锁设置", padding=20)
        temp_unlock_group.pack(fill='x', pady=10, padx=20)

        ttk.Label(temp_unlock_group, text="临时解锁持续时间（分钟）:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        self.temp_unlock_var = tk.StringVar(value=str(self.config_manager.get_temp_unlock_duration()))
        temp_unlock_entry = ttk.Entry(temp_unlock_group, textvariable=self.temp_unlock_var, width=10)
        temp_unlock_entry.grid(row=0, column=1, sticky='w', pady=5, padx=5)

        warning_group = ttk.LabelFrame(scrollable_frame, text="锁定前提醒", padding=20)
        warning_group.pack(fill='x', pady=10, padx=20)

        ttk.Label(warning_group, text="锁定前提醒时间（分钟）:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        self.warning_var = tk.StringVar(value=str(self.config_manager.get_warning_before_lock()))
        warning_entry = ttk.Entry(warning_group, textvariable=self.warning_var, width=10)
        warning_entry.grid(row=0, column=1, sticky='w', pady=5, padx=5)

        hotkey_group = ttk.LabelFrame(scrollable_frame, text="快捷键设置", padding=20)
        hotkey_group.pack(fill='x', pady=10, padx=20)

        hotkeys = self.config_manager.get_hotkeys()
        self.hotkey_vars = {}

        ttk.Label(hotkey_group, text="显示窗口:").grid(row=0, column=0, sticky='e', pady=5, padx=5)
        self.hotkey_vars['show_window'] = tk.StringVar(value=hotkeys.get('show_window', 'ctrl+alt+a'))
        hotkey_show_entry = ttk.Entry(hotkey_group, textvariable=self.hotkey_vars['show_window'], width=20)
        hotkey_show_entry.grid(row=0, column=1, sticky='w', pady=5, padx=5)

        ttk.Label(hotkey_group, text="隐藏窗口:").grid(row=1, column=0, sticky='e', pady=5, padx=5)
        self.hotkey_vars['hide_window'] = tk.StringVar(value=hotkeys.get('hide_window', 'ctrl+alt+h'))
        hotkey_hide_entry = ttk.Entry(hotkey_group, textvariable=self.hotkey_vars['hide_window'], width=20)
        hotkey_hide_entry.grid(row=1, column=1, sticky='w', pady=5, padx=5)

        ttk.Label(hotkey_group, text="立即锁定:").grid(row=2, column=0, sticky='e', pady=5, padx=5)
        self.hotkey_vars['immediate_lock'] = tk.StringVar(value=hotkeys.get('immediate_lock', 'ctrl+alt+l'))
        hotkey_lock_entry = ttk.Entry(hotkey_group, textvariable=self.hotkey_vars['immediate_lock'], width=20)
        hotkey_lock_entry.grid(row=2, column=1, sticky='w', pady=5, padx=5)

        ttk.Label(hotkey_group, text="退出程序:").grid(row=3, column=0, sticky='e', pady=5, padx=5)
        self.hotkey_vars['quit_program'] = tk.StringVar(value=hotkeys.get('quit_program', 'ctrl+alt+q'))
        hotkey_quit_entry = ttk.Entry(hotkey_group, textvariable=self.hotkey_vars['quit_program'], width=20)
        hotkey_quit_entry.grid(row=3, column=1, sticky='w', pady=5, padx=5)

        info_label = ttk.Label(hotkey_group, text="快捷键格式: ctrl+alt+字母 (例如: ctrl+alt+a)",
                            font=('Arial', 8), foreground='gray')
        info_label.grid(row=4, column=0, columnspan=2, pady=10)

        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill='x', pady=20, padx=20)

        save_btn = ttk.Button(btn_frame, text="保存系统设置", command=self.save_system_settings)
        save_btn.pack(pady=5)

        info_frame = ttk.LabelFrame(scrollable_frame, text="退出程序说明", padding=20)
        info_frame.pack(fill='x', pady=10, padx=20)

        info_text = """• 关闭窗口：点击右上角X按钮，窗口隐藏但程序继续运行
• 显示窗口：按快捷键 Ctrl+Alt+A 或重新运行程序
• 退出程序：按快捷键 Ctrl+Alt+E 并输入管理员密码
• 强制退出：运行'停止程序.bat' 或按 Ctrl+Alt+Shift+Q"""

        info_label = ttk.Label(info_frame, text=info_text, font=('Arial', 9), justify='left')
        info_label.pack(anchor='w', padx=5, pady=5)

    def toggle_autostart(self):
        enabled = self.autostart_var.get()
        if AutoStarter.set_autostart(enabled):
            self.config_manager.set_autostart_enabled(enabled)
            messagebox.showinfo("成功", f"开机自启动已{'启用' if enabled else '禁用'}")
        else:
            self.autostart_var.set(not enabled)
            messagebox.showerror("错误", "设置开机自启动失败")

    def save_system_settings(self):
        try:
            temp_unlock_duration = int(self.temp_unlock_var.get())
            if temp_unlock_duration < 1:
                messagebox.showwarning("错误", "临时解锁时间至少为1分钟")
                return

            warning_time = int(self.warning_var.get())
            if warning_time < 1:
                messagebox.showwarning("错误", "提醒时间至少为1分钟")
                return

            self.config_manager.set_temp_unlock_duration(temp_unlock_duration)
            self.config_manager.set_warning_before_lock(warning_time)

            for action, var in self.hotkey_vars.items():
                hotkey = var.get().strip().lower()
                if hotkey:
                    self.config_manager.set_hotkey(action, hotkey)

            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.reload_hotkeys()

            messagebox.showinfo("成功", "系统设置已保存！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
        except Exception as e:
            logger.error(f"保存系统设置失败: {e}")
            messagebox.showerror("错误", f"保存设置时出错: {e}")

    def setup_about_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text='关于我')

        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", on_mousewheel)

        def bind_mousewheel_to_widget(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_mousewheel_to_widget(child)

        app_info_group = ttk.LabelFrame(scrollable_frame, text="软件信息", padding=20)
        app_info_group.pack(fill='x', pady=(10, 10), padx=20)

        app_title = tk.Label(app_info_group, text="小灵控制屏幕保护程序", 
                            font=('Arial', 16, 'bold'), bg='#f0f0f0')
        app_title.pack(pady=(0, 10))

        version_label = tk.Label(app_info_group, text="版本: 1.0", 
                               font=('Arial', 12), bg='#f0f0f0')
        version_label.pack(pady=5)

        desc_label = tk.Label(app_info_group, 
                            text="一个基于 Python 的智能时间管理桌面应用，\n用于管理和限制电脑使用时间，帮助用户养成健康的使用习惯。",
                            font=('Arial', 11), bg='#f0f0f0', justify='left')
        desc_label.pack(pady=10)

        features_group = ttk.LabelFrame(scrollable_frame, text="主要功能", padding=20)
        features_group.pack(fill='x', pady=10, padx=20)

        features_text = """• 📅 灵活的时间设置：为周一至周日分别设置可用时间段
• ⏰ 实时监控：后台自动检查时间并执行锁定
• 🔐 双重密码保护：管理员密码和临时退出密码
• 🚀 开机自启动：随Windows自动启动
• ⏳ 临时解锁：可设置临时解锁时间限制
• ⚠️ 锁定前提醒：锁定前弹出警告
• 🆘 紧急解锁：安全问题/答案验证解锁
• 📊 使用统计：记录每日使用时间
• ✅ 白名单应用：锁定时间仍可使用指定应用"""

        features_label = tk.Label(features_group, text=features_text,
                                font=('Arial', 11), bg='#f0f0f0', justify='left')
        features_label.pack(anchor='w')

        shortcuts_group = ttk.LabelFrame(scrollable_frame, text="快捷键", padding=20)
        shortcuts_group.pack(fill='x', pady=10, padx=20)

        shortcuts_text = """• Ctrl+Alt+A - 显示/打开设置窗口
• Ctrl+Alt+H - 隐藏窗口
• Ctrl+Alt+L - 立即锁定屏幕
• Ctrl+Alt+E - 退出程序（需要密码）
• Ctrl+Alt+Shift+Q - 强制退出"""

        shortcuts_label = tk.Label(shortcuts_group, text=shortcuts_text,
                                font=('Arial', 11), bg='#f0f0f0', justify='left')
        shortcuts_label.pack(anchor='w')

        dev_group = ttk.LabelFrame(scrollable_frame, text="开发团队", padding=20)
        dev_group.pack(fill='x', pady=10, padx=20)

        dev_text = """开发网站：https://autolist.top
        
商务自动化助手 - 自动化软件销售平台

我们提供专业的电商自动化工具、咨询服务和培训课程，帮助企业提升效率，降低成本，实现业务增长。

核心服务：
• 🌍 国际贸易自动化工具
• 🔄 n8n工作流服务  
• 🎨 电商美工自动化工具

核心优势：
• ⚡ 高效自动化
• 🎯 精准定制
• 🔒 安全可靠
• 📈 业务增长"""

        dev_label = tk.Label(dev_group, text=dev_text,
                            font=('Arial', 11), bg='#f0f0f0', justify='left')
        dev_label.pack(anchor='w')

        copyright_group = ttk.LabelFrame(scrollable_frame, text="版权信息", padding=20)
        copyright_group.pack(fill='x', pady=10, padx=20)

        copyright_text = """© 2024 商务自动化助手
        
许可证：MIT License

技术支持：如有问题，请查看控制台输出的调试信息或检查配置文件是否正常。"""

        copyright_label = tk.Label(copyright_group, text=copyright_text,
                                font=('Arial', 11), bg='#f0f0f0', justify='left')
        copyright_label.pack(anchor='w')

        bind_mousewheel_to_widget(scrollable_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def setup_time_check(self):
        self.check_and_lock()
        self.root.after(10000, self.setup_time_check)

    def check_and_lock(self):
        if self.config_manager.is_passwords_configured():
            current_day = self.time_checker.get_current_day_name()
            current_time = datetime.now().time()
            is_locked = self.time_checker.is_locked_time()
            logger.debug(f"时间检查: {current_day}, {current_time}, 锁定状态: {is_locked}")
            
            if self.temp_unlock_end_time:
                if datetime.now() >= self.temp_unlock_end_time:
                    self.temp_unlock_end_time = None
                    self.usage_tracker.stop_tracking()
                    logger.info("临时解锁时间结束")

            if not self.temp_unlock_end_time and is_locked:
                self.immediate_lock()
            elif not self.time_checker.is_locked_time() and not self.temp_unlock_end_time and not getattr(self, 'manual_lock', False):
                if hasattr(self, 'lock_screen') and self.lock_screen:
                    try:
                        self.lock_screen.close()
                        self.lock_screen = None
                    except Exception as e:
                        logger.error(f"关闭锁定屏幕失败: {e}")

    def immediate_lock(self, manual=False):
        if manual:
            self.manual_lock = True
        else:
            self.manual_lock = False
            
        if not self.lock_screen or not hasattr(self.lock_screen, 'window') or not self.lock_screen.window.winfo_exists():
            logger.info("显示锁定屏幕")
            self.root.withdraw()
            self.lock_screen = LockScreen(self.config_manager, self)
        else:
            try:
                if self.lock_screen.window.state() == 'withdrawn':
                    self.lock_screen.window.deiconify()
            except Exception:
                pass

    def temp_unlock(self):
        duration = self.config_manager.get_temp_unlock_duration()
        self.temp_unlock_end_time = datetime.now() + timedelta(minutes=duration)
        self.usage_tracker.start_tracking()
        logger.info(f"临时解锁 {duration} 分钟")

        try:
            if hasattr(self, 'lock_screen') and self.lock_screen:
                try:
                    self.lock_screen.close()
                except Exception:
                    pass
                self.lock_screen = None
        except Exception as e:
            logger.error(f"关闭锁定窗口失败: {e}")

        messagebox.showinfo("临时解锁", f"已临时解锁 {duration} 分钟")

    def show_password_dialog(self, prompt):
        result = [None]
        dialog = None

        def create_dialog():
            nonlocal dialog
            dialog = tk.Toplevel()
            dialog.title("密码验证")
            dialog.geometry("400x200")
            dialog.attributes('-topmost', True)
            
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'logo.ico')
            if os.path.exists(icon_path):
                try:
                    dialog.iconbitmap(icon_path)
                except Exception as e:
                    logger.debug(f"设置对话框图标失败: {e}")

            def center_window(window):
                window.update_idletasks()
                width = window.winfo_width()
                height = window.winfo_height()
                x = (window.winfo_screenwidth() // 2) - (width // 2)
                y = (window.winfo_screenheight() // 2) - (height // 2)
                window.geometry(f"+{x}+{y}")

            center_window(dialog)

            label = tk.Label(dialog, text=prompt, font=('Arial', 12))
            label.pack(pady=20)

            password_var = tk.StringVar()
            password_entry = ttk.Entry(dialog, textvariable=password_var, show='*', width=25, font=('Arial', 12))
            password_entry.pack(pady=10)
            password_entry.focus()

            def on_ok():
                result[0] = password_var.get()
                dialog.destroy()

            def on_cancel():
                result[0] = None
                dialog.destroy()

            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=10)

            ok_btn = ttk.Button(btn_frame, text="确定", command=on_ok)
            ok_btn.pack(side='left', padx=5)

            cancel_btn = ttk.Button(btn_frame, text="取消", command=on_cancel)
            cancel_btn.pack(side='left', padx=5)

            password_entry.bind('<Return>', lambda e: on_ok())
            dialog.bind('<Escape>', lambda e: on_cancel())
            dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        try:
            from tkinter import _default_root
            if _default_root is None:
                create_dialog()
                dialog.mainloop()
            else:
                create_dialog()
                _default_root.wait_window(dialog)
        except Exception:
            create_dialog()
            dialog.mainloop()
        
        return result[0]

    def show_error_dialog(self, title, message):
        messagebox.showerror(title, message)

    def show_info_dialog(self, title, message):
        messagebox.showinfo(title, message)

    def quit_program_from_hotkey(self):
        try:
            if not self.config_manager.is_passwords_configured():
                logger.info("未设置密码，允许退出")
                self.safe_exit()
                return

            password = self.show_password_dialog("请输入管理员密码退出程序")

            if password is None:
                logger.info("用户取消退出")
                return

            if password and self.config_manager.verify_admin_password(password):
                logger.info("密码验证成功，执行退出")
                self.safe_exit()
            else:
                logger.warning("密码验证失败")
                self.show_error_dialog("密码错误", "管理员密码不正确！")

        except Exception as e:
            logger.error(f"退出程序出错: {e}")

    def quit_program_from_button(self):
        self.quit_program_from_hotkey()

    def safe_exit(self):
        logger.info("开始安全退出...")

        try:
            if hasattr(self, 'usage_tracker'):
                self.usage_tracker.stop_tracking()
        except Exception as e:
            logger.error(f"停止使用跟踪失败: {e}")

        try:
            if hasattr(self, 'process_protector'):
                self.process_protector.stop_monitoring()
        except Exception as e:
            logger.error(f"停止进程保护失败: {e}")

        self.running = False

        try:
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.clear_hotkeys()
        except Exception as e:
            logger.error(f"清除快捷键失败: {e}")

        try:
            if hasattr(self, 'tray_icon') and self.tray_icon and hasattr(self.tray_icon, 'icon') and self.tray_icon.icon:
                self.tray_icon.icon.stop()
        except Exception as e:
            logger.error(f"停止托盘图标失败: {e}")

        try:
            if hasattr(self, 'lock_screen') and self.lock_screen:
                self.lock_screen.close()
        except Exception as e:
            logger.error(f"关闭锁定屏幕失败: {e}")

        try:
            self.root.destroy()
        except Exception as e:
            logger.error(f"销毁主窗口失败: {e}")

        logger.info("程序已退出")

    def run(self):
        logger.info("进入主循环...")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        logger.info("主循环结束")

    def on_closing(self):
        try:
            logger.info("关闭主窗口，程序继续运行...")
            self.root.withdraw()
        except Exception as e:
            logger.error(f"隐藏窗口出错: {e}")
