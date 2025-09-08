import requests
import time
import random
import re
import traceback
import os
import sys
from pathlib import Path

# 伪装浏览器请求头（建议不要硬编码 Cookie，长期可能失效）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.baidu.com",
    # 注意：Cookie 会过期，建议后期改为自动登录或去 Cookie
    "Cookie": "BIDUPSID=203BB116BAD7A21452D9A8AFCF9C36F2; PSTM=1665389661; BD_UPN=123253; BDUSS=lpQTF1OFlKZmpJZEZmQ3pHdkpqMnhzRElNUk1kU35VWFFuaEpsUVpaZWtpR3hqRVFBQUFBJCQAAAAAAAAAAAEAAABNtRgKc29sb19tc2sAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKT7RGOk-0Rjfm; BDUSS_BFESS=lpQTF1OFlKZmpJZEZmQ3pHdkpqMnhzRElNUk1kU35VWFFuaEpsUVpaZWtpR3hqRVFBQUFBJCQAAAAAAAAAAAEAAABNtRgKc29sb19tc2sAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKT7RGOk-0Rjfm; BAIDUID=1088EDF2D03D0FA6EC2D052921641828:FG=1; MCITY=-:; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; BA_HECTOR=002la48g8l0k258g8185087v1hnjr451f; ZFY=R:BX3g8nr3kFWuFJs0zZHFQAmnd8jgw:BJUmyeTbQuQHU:C; BAIDUID_BFESS=1088EDF2D03D0FA6EC2D052921641828:FG=1; BD_HOME=1; sugstore=0; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; BD_CK_SAM=1; PSINO=2; delPer=0; baikeVisitId=f3893191-471e-4462-a8dc-d1569ec1182d; H_PS_PSSID=36548_37557_37513_37684_37768_37778_37797_37539_37714_37741_26350_37789; H_PS_645EC=f126ZpPGPo4WkGeVRredI8zb2MdUoY1SWbcuKHKZLJ9PNN0gGSrKV4sXAlv3yU9gf7Sa; BDSVRTM=199; WWW_ST=1668936275987"
}


def resource_path(relative_path):
    """ 获取资源文件的绝对路径，兼容 PyInstaller 打包 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(".").absolute()
    return Path(base_path) / relative_path


def get_user_data_dir():
    """ 获取用户数据目录，用于保存可修改文件 """
    app_name = "MessageBombingTool"
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
            print(f"✅ 首次运行，已复制默认文件: {filename}")
    return user_file


# 读取配置文件（从资源或用户目录）
citys_path = resource_path('citys.txt')
needs_path = resource_path('needs.txt')

try:
    with open(citys_path, encoding='utf-8') as f:
        citys = [line.strip() for line in f.readlines() if line.strip()]
except Exception as e:
    print(f"❌ 读取 citys.txt 失败: {e}")
    citys = []

try:
    with open(needs_path, encoding='utf-8') as f:
        needs = [line.strip() for line in f.readlines() if line.strip()]
except Exception as e:
    print(f"❌ 读取 needs.txt 失败: {e}")
    needs = []


def baidu_search(v_keyword, v_max_page, output_file):
    """
    爬取百度搜索结果并追加写入文件
    :param v_keyword: 搜索关键词
    :param v_max_page: 爬取页数
    :param output_file: 输出文件路径（Path 对象）
    :return: None
    """
    for page in range(v_max_page):
        print(f'开始爬取第 {page + 1} 页')
        wait_seconds = random.uniform(1, 2)
        print(f'等待 {wait_seconds:.2f} 秒')
        time.sleep(wait_seconds)

        url = f'https://www.baidu.com/s?wd={v_keyword}&pn={page * 10}'
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            html = r.text

            # 提取 ada.baidu.com/site/ 开头的链接
            # 注意：正则需根据实际 HTML 调整，当前正则可能不准确
            links = re.findall(r'https://ada\.baidu\.com/site/[^\s"<>]+', html)
            valid_links = []
            for link in links:
                # 过滤 xyl.imid 开头的
                path_parts = link.split('/')
                if len(path_parts) >= 6 and not path_parts[5].startswith('xyl'):
                    valid_links.append(link)

            # 写入用户文件
            with open(output_file, 'a', encoding='utf-8') as f:
                for link in valid_links:
                    print(link)
                    f.write(link.strip() + '\n')

        except requests.RequestException as e:
            print(f"请求失败: {e}")
        except Exception as e:
            traceback.print_exc()


def star_get_putian_url(stop_event=None, output_file=None):
    """
    主函数：爬取莆田系医院链接
    :param stop_event: threading.Event() 用于停止
    :param output_file: 输出文件路径，可选
    """
    if output_file is None:
        output_file = get_user_file_path('api.txt')

    # 清空文件（首次）
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            pass
        print(f"✅ 已清空输出文件: {output_file}")
    except Exception as e:
        print(f"❌ 无法清空文件: {e}")
        return

    for city in citys:
        for need in needs:
            if stop_event and stop_event.is_set():
                print("🛑 用户请求停止爬取。")
                return

            search_keyword = f"{city}{need}"
            print(f"🔍 搜索关键词: {search_keyword}")
            try:
                baidu_search(v_keyword=search_keyword, v_max_page=1, output_file=output_file)
            except Exception as e:
                print(f"❌ 搜索出错: {search_keyword}, 错误: {e}")
                traceback.print_exc()
                time.sleep(60)  # 避免频繁请求


if __name__ == '__main__':
    star_get_putian_url()