# boom.py - 核心自动化逻辑模块

import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import os
import sys
from pathlib import Path

# 配置日志（由 GUI 控制输出，这里只记录）
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    """ 获取资源文件的绝对路径，兼容 PyInstaller 打包 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(".").absolute()
    return Path(base_path) / relative_path


def get_user_data_dir():
    """ 获取用户数据目录，用于保存可修改的配置文件 """
    app_name = "MessageBombingTool"
    user_dir = Path(os.getenv('LOCALAPPDATA')) / app_name
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_file_path(filename):
    """
    获取用户目录下的文件路径
    首次运行时从默认资源复制
    """
    user_file = get_user_data_dir() / filename
    if not user_file.exists():
        default_file = resource_path(filename)
        if default_file.exists():
            import shutil
            shutil.copy2(default_file, user_file)
            logger.info(f"✅ 首次运行，已复制默认文件: {filename}")
        else:
            raise FileNotFoundError(f"❌ 默认配置文件未找到: {filename}")
    return user_file


def load_urls_from_file(custom_path=None):
    """
    从 api.txt 加载URL列表
    :param custom_path: 可选路径，优先使用
    """
    file_path = Path(custom_path) if custom_path else get_user_file_path('api.txt')

    if not file_path.exists():
        raise FileNotFoundError(f"❌ 缺少 api.txt 文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        raise ValueError("❌ api.txt 文件为空，请添加有效URL。")

    logger.info(f"✅ 已加载 {len(urls)} 个URL")
    return urls


def load_needCheat_from_file(custom_path=None):
    """
    从 need_cheat.txt 加载前缀列表
    :param custom_path: 可选路径
    """
    file_path = Path(custom_path) if custom_path else get_user_file_path('need_cheat.txt')

    if not file_path.exists():
        raise FileNotFoundError(f"❌ 缺少 need_cheat.txt 文件: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        needs = [line.strip() for line in f if line.strip()]

    if not needs:
        raise ValueError("❌ need_cheat.txt 文件为空，请添加有效前缀。")

    logger.info(f"✅ 已加载 {len(needs)} 个前缀")
    return needs


def create_driver(chrome_path):
    """创建带配置的Chrome浏览器实例"""
    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.page_load_strategy = "eager"
    options.add_argument("--headless=new")  # 可选：无头模式
    options.add_argument('--log-level=3')
    return webdriver.Chrome(options=options)


def visit_website(chrome_path, phone, url, need_cheat):
    """
    单个访问任务
    :param chrome_path: Chrome可执行文件路径
    :param phone: 手机号
    :param url: 目标URL
    :param need_cheat: 前缀列表
    :return: 是否成功
    """
    driver = None
    try:
        driver = create_driver(chrome_path)
        wait = WebDriverWait(driver, 10)

        # 先访问百度（防止某些网站拦截）
        driver.get("https://www.baidu.com/")
        time.sleep(0.5)
        driver.get(url)

        # 切换到最新窗口（如果有弹窗）
        handles = driver.window_handles
        if len(handles) > 1:
            driver.switch_to.window(handles[-1])

        # 随机选择前缀 + 手机号
        prefix = random.choice(need_cheat)
        message = prefix + phone

        # 输入并发送
        input_box = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'pc-imlp-component-typebox-input')))
        input_box.clear()
        input_box.send_keys(message)

        send_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'pc-imlp-component-typebox-send')))
        send_btn.click()

        time.sleep(1)  # 可视化延迟
        logger.info(f"✅ 成功发送: {url}")
        return True

    except Exception as e:
        logger.error(f"❌ 访问失败 {url}: {e}")
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass  # 忽略关闭异常


def boom(chrome_path, phone, max_workers=5, url_file=None, cheat_file=None):
    """
    主执行函数
    :param chrome_path: Chrome路径
    :param phone: 手机号
    :param max_workers: 最大并发数
    :param url_file: 自定义 api.txt 路径（可选）
    :param cheat_file: 自定义 need_cheat.txt 路径（可选）
    """
    try:
        # 使用传入路径或默认用户路径
        urls = load_urls_from_file(url_file)
        need_cheat = load_needCheat_from_file(cheat_file)
        total = len(urls)

        logger.info(f"🚀 开始任务：共 {total} 个链接，最大并发数: {max_workers}")

        success_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(visit_website, chrome_path, phone, url, need_cheat): url
                for url in urls
            }

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    if future.result():
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as exc:
                    logger.error(f"任务异常 {url}: {exc}")
                    failed_count += 1

        logger.info(f"🎉 所有任务完成！成功: {success_count} | 失败: {failed_count}")
        return True

    except Exception as e:
        logger.error(f"💣 任务中断: {e}")
        return False