"""
Script for automated form submissions with the following features:
- Reads emails from email.txt (one email per line)
- Reads proxies from proxies.txt (one proxy per line)
- Uses random user agents for each request
- Supports proxy rotation for each request
- Submits forms asynchronously for maximum performance
- Assigns dedicated proxies to each worker
- Shows colored logs
- Saves failed submissions to failed.txt

Usage:
1. Make sure email.txt exists with email addresses (one per line)
2. Make sure proxies.txt exists with proxies (one per line)
   Format for proxies: "http://user:pass@ip:port" or "http://ip:port"
3. Run the script: python test.py
"""

import aiohttp
import asyncio
import random
import time
import json
import os
from fake_useragent import UserAgent
from datetime import datetime
import argparse
from faker import Faker
import sys
import inquirer
from inquirer.themes import GreenPassion
from art import text2art
from colorama import Fore
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ORANGE = '\033[38;5;208m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

url = "https://webflow.com/api/v1/form/67d0b0a8a52ef03e7caca863"

# Generate random user agent
ua = UserAgent()

# List of proxies will be loaded from file
proxies_list = []

# Set to True to use proxies, False to use direct connection if no proxies available
USE_PROXIES = True

# Lock for writing to files
file_lock = asyncio.Lock()

# Инициализация Faker с английской локализацией
fake_en = Faker("en_US")

# Remove global rate limit and its functions
# Instead track rate limited workers
rate_limited_workers = {}

# Set of processed emails to avoid duplicates
processed_emails = set()

def generate_random_name():
    
    return fake_en.first_name()

def generate_random_last_name():
    
    return fake_en.last_name()

async def get_form(email, name, last_name, user_agent, proxy, session):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.codex.xyz",
        "Referer": "https://www.codex.xyz/",
        "User-Agent": user_agent,
    }
    
    payload = {
        "name": "Contact 11 Form",
        "pageId": "67e9a27f8336152373dcfccb",
        "elementId": "17e22948-4cba-360d-8f70-66e920d49528",
        "domain": "www.codex.xyz",
        "source": "https://www.codex.xyz/contact",
        "test": "false",
        "fields[Contact Email]": email,
        "fields[Contact Name]": name,
        "fields[Contact Last name]": last_name
    }

    try:
        async with session.post(url, headers=headers, data=payload, proxy=proxy, timeout=10) as response:
            result = await response.json()
            return result
    except Exception as e:
        return {"error": str(e), "code": 500}

def read_emails_from_file(filename="data/email.txt"):
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Colors.RED}File {filename} not found{Colors.ENDC}")
        return []

def read_proxies_from_file(filename="data/proxies.txt"):
    try:
        with open(filename, "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
            proxies = ['https://' + proxy if not proxy.startswith('http://') and not proxy.startswith('https://') else proxy for proxy in proxies]
            print(f"{Colors.BLUE}Loaded {len(proxies)} proxies from file{Colors.ENDC}")
            return proxies
    except FileNotFoundError:
        print(f"{Colors.RED}File {filename} not found. No proxies will be used.{Colors.ENDC}")
        return []

async def log_failed_submission(email, result):
    async with file_lock:
        os.makedirs('result', exist_ok=True)
        with open("result/failed.txt", "a") as file:
            file.write(f"{email}\n")
    
        remove_email_from_file(email)

async def log_success_submission(email):
    async with file_lock:
        try:
            os.makedirs('result', exist_ok=True)
            with open("result/success.txt", "a") as file:
                file.write(f"{email}\n")
            processed_emails.add(email)
            
            remove_email_from_file(email)
        except Exception as e:
            print(f"{Colors.RED}Error saving to result/success.txt: {str(e)}{Colors.ENDC}")

def remove_email_from_file(email, filename="data/email.txt"):
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
        lines = [line for line in lines if line.strip() != email]
        with open(filename, "w") as file:
            file.writelines(lines)
        
    except Exception as e:
        print(f"{Colors.RED}Error removing {email} from {filename}: {str(e)}{Colors.ENDC}")

async def submit_form_with_proxy(email, worker_proxy=None, worker_id=0, session=None, index=0):
    user_agent = ua.random

    
    delay = random.uniform(0.1, 0.5) if worker_id == 0 else random.uniform(7, 10)
    await asyncio.sleep(delay)

    name = generate_random_name()
    last_name = generate_random_last_name()

    proxy_used = True
    try:
        result = await get_form(email, name, last_name, user_agent, worker_proxy, session)
    except aiohttp.ClientProxyConnectionError:
        result = await get_form(email, name, last_name, user_agent, None, session)
        proxy_used = False

    is_rate_limited = result.get('code') == 429 and result.get('msg') == "Rate limit hit"
    is_success = result.get('code') == 200 and result.get('msg') == 'ok'

    if is_rate_limited:
        response_color = Colors.YELLOW
        rate_limited_workers[f"worker_{worker_id}"] = time.time() + 15
        await log_failed_submission(email, result)
        status = "Limit"
    elif is_success:
        response_color = Colors.GREEN
        await log_success_submission(email)
        status = "Success"
    else:
        response_color = Colors.RED
        await log_failed_submission(email, result)
        status = "Error"

    
    geo = "Unknown"
    if worker_proxy and '__cr.' in worker_proxy:
        geo_part = worker_proxy.split('__cr.')[1].split(':')[0]
        geo = geo_part if geo_part else "Unknown"

    
    masked_email = email
    if len(email) > 10:
        masked_email = f"{email[:3]}***{email[-7:]}"

    proxy_status = f"{Colors.GREEN}✅{Colors.ENDC}" if proxy_used else f"{Colors.RED}❌{Colors.ENDC}"
    geo_text = f"{Colors.WHITE}{geo}{Colors.ENDC}"
    email_text = f"{Colors.WHITE}{masked_email}{Colors.ENDC}"
    status_text = f"{response_color}{status}{Colors.ENDC}"

    
    counter = f"{Colors.WHITE}| 🔄 {index+1}{Colors.ENDC}"
    log_message = f"|{status_text} |📫 {email_text} |Proxy: {proxy_status} |🌎: {geo_text} |{counter}"
    print(log_message)

    return result, is_success

async def process_emails(emails, proxies):
    successful_submissions = 0
    failed_submissions = 0
    rate_limited_count = 0

    connector = aiohttp.TCPConnector(limit=None, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        proxy_index = 0
        for i, email in enumerate(emails):
            if proxies and USE_PROXIES:
                worker_proxy = proxies[proxy_index]
                proxy_index = (proxy_index + 1) % len(proxies)
            else:
                worker_proxy = None
            
            result, is_success = await submit_form_with_proxy(email, worker_proxy, 1, session, i)
            
            if result.get('code') == 429:
                rate_limited_count += 1
                failed_submissions += 1
            elif is_success and result.get('code') == 200 and result.get('msg') == 'ok':
                successful_submissions += 1
                #fprint(f"{Colors.MAGENTA}SUCCESS COUNT: {successful_submissions}{Colors.ENDC}")
            else:
                failed_submissions += 1
            
        
            await asyncio.sleep(random.uniform(1.0, 5.0))
    
    return successful_submissions, failed_submissions, rate_limited_count

async def main_async():
    os.makedirs('data', exist_ok=True)
    
    parser = argparse.ArgumentParser(description='Form submission automation tool')
    parser.add_argument('--workers', type=int, default=1, help='Number of concurrent workers (default: 1)')
    parser.add_argument('--delay', type=float, default=0.05, help='Delay between batches in seconds (default: 0.05)')
    args = parser.parse_args()
    
    max_workers = args.workers
    
    all_emails = read_emails_from_file()
    if not all_emails:
        print(f"{Colors.RED}No emails found. Please create email.txt file with emails (one per line){Colors.ENDC}")
        return
    
    try:
        os.makedirs('result', exist_ok=True)
        with open("result/success.txt", "r") as f:
            for line in f:
                processed_emails.add(line.strip())
        # print(f"{Colors.BLUE}Loaded {len(processed_emails)} previously successful emails{Colors.ENDC}")
    except FileNotFoundError:
        pass
    
    try:
        os.makedirs('result', exist_ok=True)
        with open("result/failed.txt", "r") as f:
            for line in f:
                processed_emails.add(line.strip())
        
        # print(f"{Colors.BLUE}Loaded {len(processed_emails)} previously failed emails{Colors.ENDC}")
    except FileNotFoundError:
        pass
    
    emails = [email for email in all_emails if email not in processed_emails]
    
    
    # print(f"{Colors.BLUE}Loaded {len(all_emails)} emails from file, {len(emails)} are new{Colors.ENDC}")
    
    if not emails:
        print(f"{Colors.YELLOW}All emails have already been processed. No new emails to submit.{Colors.ENDC}")
        return
    
    global proxies_list
    proxies_list = read_proxies_from_file()
    
    worker_proxies = {}
    if proxies_list and USE_PROXIES:
    
        # print(f"{Colors.YELLOW}Proxies will be used in rotation for each request.{Colors.ENDC}")
        
        for log_file in ["result/success.txt", "result/failed.txt"]:
            try:
                os.makedirs('result', exist_ok=True)
                if not os.path.exists(log_file):
                    open(log_file, 'w').close()
                    
                    # print(f"{Colors.BLUE}Created {log_file}{Colors.ENDC}")
            except Exception as e:
                print(f"{Colors.RED}Error creating {log_file}: {str(e)}{Colors.ENDC}")
    
    
    # print(f"{Colors.MAGENTA}Starting asynchronous submission process with single thread and proxy rotation...{Colors.ENDC}")
    start_time = time.time()
    
    successful_submissions, failed_submissions, rate_limited_count = await process_emails(
        emails, proxies_list
    )
    
    elapsed_time = time.time() - start_time
    
    # print(f"\n{Colors.CYAN}{Colors.BOLD}=== Summary ==={Colors.ENDC}")
    # print(f"{Colors.GREEN}Successful submissions: {successful_submissions} (saved to result/success.txt){Colors.ENDC}")
    # print(f"{Colors.RED}Failed submissions: {failed_submissions} (saved to result/failed.txt){Colors.ENDC}")
    # if rate_limited_count > 0:
    #     print(f"{Colors.YELLOW}Rate limited requests: {rate_limited_count}{Colors.ENDC}")
    # print(f"{Colors.BLUE}Total time elapsed: {elapsed_time:.2f} seconds{Colors.ENDC}")
    
    total_submissions = successful_submissions + failed_submissions
    # if elapsed_time > 0:
    #     rate = total_submissions / elapsed_time
    #     print(f"{Colors.MAGENTA}Submission rate: {rate:.2f} submissions/second{Colors.ENDC}")
    
    # if failed_submissions > 0:
    #     print(f"{Colors.YELLOW}Failed submissions saved to result/failed.txt{Colors.ENDC}")

class Console:
    MODULES = (
        "Start Registration",
        "Exit",
    )
    MODULES_DATA = {
        "Start Registration": "register",
        "Exit": "exit",
    }

    def __init__(self):
        self.rich_console = RichConsole()

    def show_dev_info(self):
        os.system("cls" if os.name == "nt" else "clear")

        title = text2art("AIRDROP", font="BIG")

        balloons = (
            "🔮" * 28 +
            "\n"
        )

        title_with_balloons = f"{title}{balloons}"

        styled_title = Text(title_with_balloons, style="purple")

        version_line = " VERSION: 1.1                https://t.me/serversdrop"
        version_telegram = Text(version_line, style="#FFD700")

        dev_panel = Panel(
            Text.assemble(
                styled_title,
                "\n",
                version_telegram
            ),
            border_style="purple",
            expand=False,
            title="",
            subtitle="[italic]Powered by AirDrop[/italic]",
        )

        self.rich_console.print(dev_panel)
        print()

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        magic_ball_prompt = Fore.LIGHTBLACK_EX + "Select the module:"
        questions = [
            inquirer.List(
                "module",
                message=magic_ball_prompt,
                choices=self.MODULES,
            ),
        ]
        answers = self.prompt(questions)
        return answers.get("module")

    def display_info(self):
        
        try:
            with open("data/email.txt", "r") as file:
                email_count = len([line for line in file if line.strip()])
        except FileNotFoundError:
            email_count = 0

        table = Table(
            title="CODEX Configuration",
            box=box.ROUNDED,
            border_style="#FF4500"
        )
        table.add_column("Parameter", style="#875fd7")
        table.add_column("Value", style="#af5faf")

        table.add_row("Emails to process", str(email_count))
        table.add_row("Threads", "1")
        table.add_row("Delay between requests", "7-10 seconds")

        panel = Panel(
            table,
            expand=False,
            border_style="purple",
            title="[bright_magenta]System Information[/bright_magenta]",
            subtitle="[italic]Use arrow keys to navigate[/italic]",
        )
        self.rich_console.print(panel)

    def build(self) -> None:
        self.show_dev_info()
        self.display_info()

        module = self.get_module()
        selected_module = self.MODULES_DATA[module]

        if selected_module == "exit":
            exit(0)
        elif selected_module == "register":
            print(f"{Fore.GREEN}Starting registration process...{Fore.RESET}")
            asyncio.run(main_async())

if __name__ == "__main__":
    try:
        console = Console()
        console.build()
    except Exception as e:
        print(f"Error: {e}")

