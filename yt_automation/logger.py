import os
import datetime
from colorama import Fore, Style, init

init(autoreset=True)

os.makedirs("output/logs", exist_ok=True)
LOG_FILE = f"output/logs/run_{datetime.date.today()}.log"


def log(msg: str):
    import sys
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(Fore.CYAN + line + Style.RESET_ALL)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'ascii'
        safe_line = line.encode(encoding, errors='replace').decode(encoding)
        print(Fore.CYAN + safe_line + Style.RESET_ALL)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
