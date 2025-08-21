#!/usr/bin/python3

import argparse
import json
import os
import pickle
import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import sys
from datetime import datetime, timedelta
import csv
from urllib.parse import urljoin

# ===================== 基础配置 =====================
CONFIG_FILE = os.path.expanduser("~/.hmv_config.json")
SESSION_FILE = os.path.expanduser("~/.hmv_session.pkl")
WRITEUP_FILE = os.path.expanduser("~/.hmv_writeups.csv")
WRITEUP_CACHE_TIMEOUT = timedelta(hours=24)  # writeup 缓存24小时

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

LEVEL_CHOICES = ['easy', 'medium', 'hard', 'windows', 'linux', 'size', 'hacked', 'all']
TAG_CHOICES = [
    'bruteforce', 'suid', 'wordpress', 'cron', 'smb', 'docker', 'sudo', 'web',
    'fileupload', 'pathhijacking', 'stego', 'binary', 'capabilities', 'cve',
    'commandinjection', 'portknocking', 'ssti', 'libraryhijack', 'sqli', 'lfi',
    'rce', 'logpoisoning', 'nfs', 'xxe'
]

# ===================== 配置管理 =====================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[!] Error reading config file.")
        return None

def save_config(username, password):
    config = {"username": username, "password": password}
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print("[+] Configuration saved successfully.")
    except Exception as e:
        print(f"[!] Error saving config: {e}")
        sys.exit(1)

def configure_credentials():
    print("[*] Configuring HackMyVM credentials...")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    if not username or not password:
        print("[!] Username and password cannot be empty.")
        sys.exit(1)
    save_config(username, password)

# ===================== Session 管理 =====================
def save_session(session):
    try:
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump({"session": session, "timestamp": datetime.now()}, f)
        print("[+] Session saved.")
    except Exception as e:
        print(f"[!] Error saving session: {e}")

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, 'rb') as f:
            data = pickle.load(f)
            session = data["session"]
            # 移除过期校验，直接返回session
            return session
    except Exception as e:
        print(f"[!] Error loading session: {e}")
        return None

def login(session, username, password):
    login_url = "https://hackmyvm.eu/login/auth.php"
    data = {"admin": username, "password_usuario": password}
    try:
        response = session.post(login_url, data, allow_redirects=True, timeout=10)
        response.raise_for_status()
        if "Logout" not in response.text:
            print("[!] Login failed: Invalid credentials.")
            return False
        print("[+] Login successful.")
        save_session(session)
        return True
    except requests.RequestException as e:
        print(f"[!] Login error: {e}")
        return False

def get_authenticated_session():
    config = load_config()
    if not config:
        print("[!] No configuration found. Please run 'config' command first.")
        print("    Usage: python3 hmv.py config")
        sys.exit(1)

    session = load_session()
    if session:
        try:
            response = session.get("https://hackmyvm.eu/machines/", timeout=10)
            response.raise_for_status()
            if "Logout" in response.text:
                print("[+] Using saved session.")
                return session
        except requests.RequestException:
            print("[!] Saved session invalid, re-authenticating...")

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    if not login(session, config["username"], config["password"]):
        sys.exit(1)
    return session

# ===================== 搜索模块 =====================
def get_total_pages(session, level=None, search=None, tag=None):
    if level:
        return 1
    try:
        params = {}
        if search:
            params['v'] = search
        if tag:
            params['t'] = tag
        response = session.get("https://hackmyvm.eu/machines/", params=params, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_element = soup.select_one("body > div.container-xxl > div > div.col-10 > div > div > div.container > nav > ul > li:nth-child(5) > a")
        if not page_element or not page_element.text:
            return 1
        page_text = page_element.text.strip()
        total_pages = int(page_text.split('/')[1]) if '/' in page_text else 1
        return total_pages
    except (requests.RequestException, ValueError, IndexError) as e:
        print(f"[!] Error fetching total pages: {e}")
        return 1

def color_level(level):
    if level.lower() == "easy":
        return bcolors.OKGREEN + level + bcolors.ENDC
    elif level.lower() == "medium":
        return bcolors.WARNING + level + bcolors.ENDC
    elif level.lower() == "hard":
        return bcolors.FAIL + level + bcolors.ENDC
    return level

def list_machines(level=None, search=None, tag=None, filter_level=None, page=1):
    color_map = {'#28a745': 'easy', '#ffc107': 'medium', '#dc3545': 'hard'}
    machines_tab = PrettyTable(["Machine Name", "Level", "Status", "Creator", "Link"])
    session = get_authenticated_session()
    params = {}
    if level: params['l'] = level
    if page > 1 and not level: params['p'] = page
    if search: params['v'] = search
    if tag: params['t'] = tag

    try:
        response = session.get("https://hackmyvm.eu/machines/", params=params, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("table.mt-1.table.table-striped.table-dark tbody tr")
        total_pages = get_total_pages(session, level, search, tag)
        if not level and (page < 1 or page > total_pages):
            print(f"[!] Invalid page number. Must be between 1 and {total_pages}.")
            sys.exit(1)

        machines = []
        for row in rows:
            try:
                name = row.find('h4', class_='vmname').text.strip()
                color_style = row.find('div', style=lambda s: s and 'border-top' in s)['style']
                color = color_style.split('solid')[-1].strip().rstrip(';')
                level_found = color_map.get(color.lower(), 'unknown')
                level_colored = color_level(level_found)
                status_tag = row.find('span', class_='badge')
                status_text = status_tag.text.strip() if status_tag else "?"
                creator = row.find_all('td')[1].text.strip()
                link = f"https://hackmyvm.eu/machines/machine.php?vm={name}"
                if filter_level and level_found.lower() != filter_level.lower():
                    continue
                status_colored = bcolors.WARNING + status_text + bcolors.ENDC if "TO HACK" in status_text else bcolors.OKGREEN + status_text + bcolors.ENDC
                machines.append([name, level_colored, status_colored, creator, link])
            except Exception as e:
                print(f"[!] Error processing machine: {e}")
                continue

        if not machines:
            print("[!] No machines found.")
            sys.exit(1)

        for machine in machines:
            machines_tab.add_row(machine)

        print(machines_tab)
        
        # 显示分页信息
        if not level and total_pages > 1:
            print(f"\n[*] Page {page} of {total_pages}")
    except requests.RequestException as e:
        print(f"[!] Error fetching machines: {e}")
        sys.exit(1)

# ===================== Writeup 模块 =====================
def needs_writeup_update():
    """检查是否需要更新 writeup 缓存"""
    if not os.path.exists(WRITEUP_FILE):
        return True
    try:
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(WRITEUP_FILE))
        return datetime.now() - file_mod_time > WRITEUP_CACHE_TIMEOUT
    except Exception:
        return True

def extract_writeups_from_html(html_content):
    """从HTML内容中提取WriteUp信息"""
    soup = BeautifulSoup(html_content, 'html.parser')
    writeups = []
    
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) < 4:
            continue
            
        try:
            # 提取靶机信息
            machine_cell = cells[0]
            machine_link = machine_cell.find('a')
            machine_name = machine_link.get_text(strip=True) if machine_link else machine_cell.get_text(strip=True)
            if not machine_name or machine_name in ['Machine', 'machine']:
                continue
            machine_url = urljoin("https://hackmyvm.eu", machine_link.get('href', '')) if machine_link else ''
            
            # 提取作者信息
            author_cell = cells[1]
            author_link = author_cell.find('a')
            author_name = author_link.get_text(strip=True) if author_link else author_cell.get_text(strip=True)
            author_url = urljoin("https://hackmyvm.eu", author_link.get('href', '')) if author_link else ''
            
            # 提取头像和国家标志
            avatar_imgs = author_cell.find_all('img')
            avatar_url = urljoin("https://hackmyvm.eu", avatar_imgs[0].get('src', '')) if avatar_imgs else ''
            country_flag = urljoin("https://hackmyvm.eu", avatar_imgs[1].get('src', '')) if len(avatar_imgs) > 1 else ''
            
            # 提取语言和WriteUp链接
            language = cells[2].get_text(strip=True)
            writeup_cell = cells[3]
            writeup_link = writeup_cell.find('a')
            writeup_url = writeup_link.get('href', '') if writeup_link else ''
            if writeup_url and not writeup_url.startswith('http') and not writeup_url.startswith('//'):
                writeup_url = urljoin("https://hackmyvm.eu", writeup_url)
            
            writeups.append({
                'vmname': machine_name,
                'machine_url': machine_url,
                'author': author_name,
                'author_url': author_url,
                'avatar_url': avatar_url,
                'country_flag': country_flag,
                'language': language,
                'writeup': writeup_url
            })
            
        except Exception as e:
            print(f"[!] 解析行时出错: {e}")
            continue
    
    return writeups

def fetch_and_update_writeups():
    """从服务器获取 writeup 数据并保存到本地"""
    session = get_authenticated_session()
    writeup_url = "https://hackmyvm.eu/hmv/writeupz.php"
    
    try:
        print("[*] Fetching writeup data from server...")
        response = session.get(writeup_url, timeout=15)
        response.raise_for_status()
        
        # 解析HTML内容
        writeups = extract_writeups_from_html(response.text)
        
        if not writeups:
            print("[!] No writeup data found.")
            return False
        
        # 保存CSV数据到本地文件
        fieldnames = ['vmname', 'machine_url', 'author', 'author_url', 'avatar_url', 'country_flag', 'language', 'writeup']
        
        with open(WRITEUP_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(writeups)
        
        print(f"[+] Writeup data updated successfully. ({len(writeups)} records)")
        return True
    except requests.RequestException as e:
        print(f"[!] Error fetching writeup data: {e}")
        return False
    except Exception as e:
        print(f"[!] Error processing writeup data: {e}")
        return False

def load_writeups():
    """加载 writeup 数据"""
    # 检查是否需要更新缓存
    if needs_writeup_update():
        print("[*] Writeup cache expired or missing, updating...")
        if not fetch_and_update_writeups():
            if os.path.exists(WRITEUP_FILE):
                print("[*] Using cached writeup data (might be outdated).")
            else:
                print("[!] No writeup data available.")
                return []
    
    # 读取本地 CSV 文件
    writeups = []
    try:
        with open(WRITEUP_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                writeups.append(row)
        return writeups
    except Exception as e:
        print(f"[!] Error reading writeup data: {e}")
        return []

def search_writeups(machine_name):
    """搜索指定机器的 writeup"""
    writeups = load_writeups()
    
    if not writeups:
        print("[!] No writeup data available.")
        return
    
    # 搜索匹配的机器名（模糊匹配）
    matching_writeups = []
    for writeup in writeups:
        if machine_name.lower() in writeup.get('vmname', '').lower():
            matching_writeups.append(writeup)
    
    if not matching_writeups:
        print(f"[!] No writeups found for machine: {machine_name}")
        return
    
    # 创建表格显示结果
    writeup_table = PrettyTable(["Machine", "Author", "Language", "Writeup Link"])
    writeup_table.align = "l"
    writeup_table.max_width["Writeup Link"] = 50
    
    for writeup in matching_writeups:
        machine = writeup.get('vmname', 'N/A')
        author = writeup.get('author', 'N/A')
        language = writeup.get('language', 'N/A')
        link = writeup.get('writeup', 'N/A')
        
        # 为语言添加颜色
        if language.lower() in ['english', 'en']:
            language_colored = bcolors.OKGREEN + language + bcolors.ENDC
        elif language.lower() in ['spanish', 'español', 'es']:
            language_colored = bcolors.WARNING + language + bcolors.ENDC
        elif language.lower() in ['chinese', 'zh', '中文']:
            language_colored = bcolors.FAIL + language + bcolors.ENDC
        else:
            language_colored = language
        
        writeup_table.add_row([machine, author, language_colored, link])
    
    print(f"\n[*] Found {len(matching_writeups)} writeup(s) for '{machine_name}':")
    print(writeup_table)

# ===================== 下载模块 =====================
def download_machine(machine_name):
    filename = f"{machine_name.lower()}.zip"
    url = f"https://downloads.hackmyvm.eu/{filename}"
    try:
        print(f"[+] Downloading {filename} from HackMyVM...")
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[✓] {machine_name} downloaded successfully.")
    except requests.exceptions.HTTPError:
        print(f"[!] Machine '{machine_name}' not found.")
    except requests.RequestException as e:
        print(f"[!] Download error: {e}")

# ===================== 提交 Flag 模块 =====================
def submit_flag(flag, vm):
    session = get_authenticated_session()
    url_flag = "https://hackmyvm.eu/machines/checkflag.php"
    data_flag = {"flag": flag, "vm": vm}
    try:
        response = session.post(url_flag, data_flag, timeout=10)
        response.raise_for_status()
        if "wrong" in response.text.lower():
            print("[!] The flag is incorrect.")
        elif "correct" in response.text.lower():
            print("[+] The flag is CORRECT!")
        else:
            print("[!] Unknown response from server.")
    except requests.RequestException as e:
        print(f"[!] Error submitting flag: {e}")

# ===================== 帮助信息格式化 =====================
def format_choices(choices, per_line=6):
    """格式化选项列表，每行显示指定数量"""
    formatted_lines = []
    for i in range(0, len(choices), per_line):
        line_choices = choices[i:i+per_line]
        formatted_lines.append(', '.join(line_choices))
    return '\n    '.join(formatted_lines)

# ===================== CLI =====================
def main():
    parser = argparse.ArgumentParser(
        description="HackMyVM CLI Tool - Search, download and manage HackMyVM machines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s config                           # Configure credentials
  %(prog)s search                           # List first page of all machines
  %(prog)s search -n todd                   # Search machines containing 'todd'
  %(prog)s search -l easy                   # List all easy machines
  %(prog)s search -t web                    # List machines tagged 'web'
  %(prog)s search -f medium -p 3            # Filter medium difficulty, page 3
  %(prog)s writeup Todd                     # Search writeups for 'Todd' machine
  %(prog)s flag -i "flag{...}" -vm todd     # Submit flag for 'todd'
  %(prog)s download todd                    # Download machine named 'todd'

Note: Options -n, -l, and -t cannot be combined with -p.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help="Available commands")

    # Config command
    parser_config = subparsers.add_parser(
        "config",
        help="Configure HackMyVM credentials"
    )

    # Search command
    parser_search = subparsers.add_parser(
        "search",
        help="Search or list machines (without options, shows first page of all machines)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Level choices formatted
    level_help = f"Filter by machine level/category:\n    {format_choices(LEVEL_CHOICES, 4)}"
    parser_search.add_argument("-l", "--level", choices=LEVEL_CHOICES, help=level_help, metavar="")
    
    # Tag choices formatted
    tag_help = f"Filter by tag:\n    {format_choices(TAG_CHOICES, 5)}"
    parser_search.add_argument("-t", "--tag", choices=TAG_CHOICES, help=tag_help, metavar="")
    
    parser_search.add_argument("-n", "--name", help="Search by machine name (partial match)")
    parser_search.add_argument("-f", "--filter-level", choices=['easy','medium','hard'],
                             help="Client-side filter by difficulty level")
    parser_search.add_argument("-p", "--page", type=int, default=1,
                             help="Page number for results (default: 1)")

    # Writeup command
    parser_writeup = subparsers.add_parser(
        "writeup",
        help="Search writeups for a specific machine"
    )
    parser_writeup.add_argument("machine_name", help="Name of the machine to search writeups for")

    # Download command
    parser_download = subparsers.add_parser(
        "download",
        help="Download a machine ZIP file"
    )
    parser_download.add_argument("machine_name", help="Name of the machine to download")

    # Flag command
    parser_flag = subparsers.add_parser(
        "flag",
        help="Submit a flag for a machine"
    )
    parser_flag.add_argument("-i", "--input", required=True, help="Flag to submit")
    parser_flag.add_argument("-vm", "--vm", required=True, help="Machine name for flag submission")

    args = parser.parse_args()

    if args.command == "config":
        configure_credentials()
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            print("[+] Cleared previous session.")
    elif args.command == "search":
        list_machines(level=args.level, search=args.name, tag=args.tag,
                      filter_level=args.filter_level, page=args.page)
    elif args.command == "writeup":
        search_writeups(args.machine_name)
    elif args.command == "download":
        download_machine(args.machine_name)
    elif args.command == "flag":
        submit_flag(args.input, args.vm)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()