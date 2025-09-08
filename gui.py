import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 正确配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 假设 main.py 提供这些函数
from main import boom, load_urls_from_file, load_needCheat_from_file
import reptile


def resource_path(relative_path):
    """ 获取资源文件的绝对路径，兼容 PyInstaller 打包 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(".").absolute()
    return Path(base_path) / relative_path


def get_user_data_dir():
    """ 获取用户数据目录，用于保存可修改文件 """
    app_name = "MessageBombingTool"  # 自定义应用名
    user_dir = Path(os.getenv('LOCALAPPDATA')) / app_name
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_file_path(filename):
    """ 获取用户目录下的文件路径，首次运行时从默认资源复制 """
    user_file = get_user_data_dir() / filename
    if not user_file.exists():
        default_file = resource_path(filename)
        if default_file.exists():
            import shutil
            shutil.copy2(default_file, user_file)
            logger.info(f"✅ 首次运行，已复制默认文件: {filename}")
    return user_file


class BoomGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化轰炸工具")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.chrome_path = tk.StringVar()
        self.phone = tk.StringVar()
        self.max_workers = tk.IntVar(value=5)

        self.stop_event = threading.Event()
        self.task_running = False
        self.updating = False
        self.stop_update_event = threading.Event()
        self.timer = None

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        # --- 手机号输入 ---
        ttk.Label(frame, text="手机号:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(frame, textvariable=self.phone, width=1).grid(
            row=0, column=1, padx=(10, 5), pady=5, sticky="ew", columnspan=2
        )

        # --- 最大线程数 ---
        ttk.Label(frame, text="最大线程数:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Spinbox(frame, from_=1, to=20, textvariable=self.max_workers, width=10).grid(
            row=1, column=1, padx=(10, 5), pady=5, sticky="w"
        )

        # --- Chrome路径选择 ---
        ttk.Label(frame, text="Chrome路径:").grid(row=2, column=0, sticky="w", pady=5)
        entry = ttk.Entry(frame, textvariable=self.chrome_path, state="readonly", width=1)
        entry.grid(row=2, column=1, padx=(10, 5), pady=5, sticky="ew")
        btn = ttk.Button(frame, text="选择...", command=self.select_chrome)
        btn.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        # --- 按钮区域 ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=20)

        self.upapi_button = ttk.Button(btn_frame, text="API表更新", command=self.update_api)
        self.upapi_button.pack(side="left", padx=10)
        ttk.Button(btn_frame, text="API表还原", command=self.reduction_api).pack(side="left", padx=10)

        self.start_button = ttk.Button(btn_frame, text="开始任务", command=self.start_task)
        self.start_button.pack(side="left", padx=10)

        self.stop_button = ttk.Button(btn_frame, text="结束任务", state="disabled", command=self.stop_task)
        self.stop_button.pack(side="left", padx=10)

        # --- 进度条 ---
        ttk.Label(frame, text="任务进度:").grid(row=4, column=0, sticky="w", pady=5)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, length=400)
        self.progress_bar.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.progress_label = ttk.Label(frame, text="执行 0 / 共 0")
        self.progress_label.grid(row=6, column=0, columnspan=3, pady=10)

    def select_chrome(self):
        if os.name == 'nt':
            filetypes = [("Chrome", "chrome.exe"), ("所有文件", "*")]
        else:
            filetypes = [("所有文件", "*")]
        path = filedialog.askopenfilename(title="选择 Chrome", filetypes=filetypes)
        if path:
            self.chrome_path.set(path)

    def start_progress_timer(self):
        """启动定时器，每5秒检查一次 api.txt 的行数并更新进度"""
        def update_progress():
            if not self.updating:
                return

            try:
                user_api_path = get_user_file_path('api.txt')
                num_lines = sum(1 for _ in open(user_api_path, 'r', encoding='utf-8'))
                self.root.after(0, lambda: self.progress_label.config(text=f"已获取 {num_lines} 个地址"))
            except (FileNotFoundError, IOError):
                self.root.after(0, lambda: self.progress_label.config(text="正在获取地址..."))

            if self.updating:
                self.timer = threading.Timer(5.0, update_progress)
                self.timer.daemon = True
                self.timer.start()

        update_progress()

    def update_api(self):
        """开始或结束 API 表更新"""
        if self.updating:
            self.stop_update_event.set()
            if self.timer:
                self.timer.cancel()
            self.updating = False
            self.upapi_button.config(text="API表更新")
            logger.info("🛑 已停止 API 表更新。")
        else:
            self.stop_update_event.clear()
            self.updating = True
            self.upapi_button.config(text="结束更新")

            # 写入路径改为用户目录
            user_api_path = get_user_data_dir() / 'api.txt'
            threading.Thread(
                target=reptile.star_get_putian_url,
                kwargs={'stop_event': self.stop_update_event, 'output_file': user_api_path},
                daemon=True
            ).start()

            self.start_progress_timer()

    def reduction_api(self):
        """还原 API 表（从备份恢复）"""
        try:
            backup_path = resource_path('api_copy.txt')
            user_api_path = get_user_file_path('api.txt')  # 用户目录下的 api.txt

            with open(backup_path, 'r', encoding='utf-8') as f:
                urls = f.readlines()

            with open(user_api_path, 'w', encoding='utf-8') as f:
                f.writelines(urls)

            self.root.after(0, lambda: messagebox.showinfo("成功", "API 表已还原！"))
            logger.info("✅ API 表已从备份还原。")
        except Exception as e:
            logger.error(f"还原失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"还原失败: {e}"))

    def start_task(self):
        chrome = self.chrome_path.get()
        phone = self.phone.get().strip()
        workers = self.max_workers.get()

        if not chrome or not os.path.exists(chrome):
            messagebox.showwarning("警告", "请正确选择 Chrome 路径！")
            return
        if not phone:
            messagebox.showwarning("警告", "请输入手机号！")
            return

        user_api_path = get_user_file_path('api.txt')
        if not user_api_path.exists():
            messagebox.showwarning("警告", "请先更新 API 表！")
            return

        threading.Thread(target=self.run_boom_task, args=(chrome, phone, workers), daemon=True).start()

    def stop_task(self):
        if self.task_running:
            self.stop_event.set()
            logger.info("🛑 用户请求停止任务...")
            self.stop_button.config(state="disabled")
            self.start_button.config(state="normal")

    def run_boom_task(self, chrome_path, phone, max_workers):
        try:
            from main import visit_website
            import random

            # ✅ 使用用户目录下的 api.txt
            urls = load_urls_from_file(get_user_file_path('api.txt'))
            random.shuffle(urls)
            total = len(urls)

            self.progress_var.set(0)
            self.update_progress(0, total)

            success_count = [0]
            failed_count = [0]
            self.task_running = True
            self.stop_event.clear()

            self.root.after(0, lambda: self.start_button.config(state="disabled"))
            self.root.after(0, lambda: self.stop_button.config(state="normal"))

            def visit_with_counter(chrome_path, phone, url, need_cheat):
                if self.stop_event.is_set():
                    return False
                result = visit_website(chrome_path, phone, url, need_cheat)
                if result:
                    success_count[0] += 1
                else:
                    failed_count[0] += 1
                completed = success_count[0] + failed_count[0]
                self.root.after(0, lambda: self.update_progress(completed, total))
                return result

            import main
            original_func = main.visit_website
            main.visit_website = visit_with_counter

            logger.info(f"🚀 开始执行任务，共 {total} 个链接...")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(visit_with_counter, chrome_path, phone, url, load_needCheat_from_file()): url
                    for url in urls
                }
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        logger.info("⏸️ 正在等待当前请求完成...")
                        continue
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"任务异常: {e}")

            logger.info("✅ 任务已结束。")

        except Exception as e:
            if not self.stop_event.is_set():
                logger.error(f"💣 任务执行出错: {e}")
        finally:
            self.task_running = False
            self.root.after(0, lambda: self.start_button.config(state="normal"))
            self.root.after(0, lambda: self.stop_button.config(state="disabled"))

    def update_progress(self, current, total):
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_var.set(progress)
            self.update_progress_label(current, total)

    def update_progress_label(self, current, total):
        self.progress_label.config(text=f"执行 {current} / 共 {total}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BoomGUI(root)
    root.mainloop()