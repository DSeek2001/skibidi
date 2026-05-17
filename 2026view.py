#devnvios liên hệ tele nếu gặp lỗi @iosnea
import requests, threading, os, time, ctypes, random, re
from colorama import Fore, init, Style
import pyfiglet

init(autoreset=True)

class iosnea_Tools:
    def __init__(self):
        self.url = ""
        self.video_id = ""
        self.proxies = []
        self.sent = 0
        self.total = 0
        self.lock = threading.Lock()
        self.colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]

    def _get_px(self):
        try:
            r = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
            if r.status_code == 200:
                self.proxies = r.text.splitlines()
        except: pass

    def _check(self, u):
        m = re.search(r'video/(\d+)', u)
        if m:
            self.video_id = m.group(1)
            return True
        return False

    def _ui(self):
        try:
            while True:
                ctypes.windll.kernel32.SetConsoleTitleW(f"@iosnea | SUCCESS: {self.total} | SESSION: {self.sent}/500")
                time.sleep(0.1)
        except: pass

    def _worker(self):
        while self.sent < 500:
            try:
                p = random.choice(self.proxies)
                h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                res = requests.post(
                    "https://api.tiktokv.com/aweme/v1/commit/item/view/",
                    params={"device_id": random.randint(1000000000, 9999999999), "item_id": self.video_id},
                    proxies={"http": f"http://{p}", "https": f"http://{p}"},
                    headers=h,
                    timeout=5
                )
                if res.status_code == 200:
                    with self.lock:
                        if self.sent < 500:
                            self.sent += 1
                            self.total += 1
                            print(f"{random.choice(self.colors)}[+] @iosnea | SUCCESS | TOTAL: {self.total}")
                            print(f"{Fore.YELLOW}NẾU KHÔNG LÊN VIEW BẠN HÃY THỬ BÊN WINDOW NHÉ.")
            except: continue

    def start(self):
        os.system("cls" if os.name == "nt" else "clear")
        while True:
            banner = pyfiglet.figlet_format("@iosnea")
            print(Fore.MAGENTA + banner)
            self.url = input(f"{Fore.YELLOW}LINK TIKTOK: ")
            if self._check(self.url): break
            os.system("cls" if os.name == "nt" else "clear")
        
        threading.Thread(target=self._ui, daemon=True).start()
        
        while True:
            self.sent = 0
            self._get_px()
            ths = []
            for _ in range(250):
                t = threading.Thread(target=self._worker)
                t.start()
                ths.append(t)
            for t in ths: t.join()
            
            for i in range(30, 0, -1):
                os.system("cls" if os.name == "nt" else "clear")
                f = pyfiglet.figlet_format("2026")
                c = random.choice(self.colors)
                print(c + f)
                print(f"{Fore.MAGENTA}{'='*60}")
                print(f"{Fore.WHITE}VUI LÒNG ĐỢI {Fore.RED}{i}{Fore.WHITE} GIÂY ĐỂ TIẾP TỤC BUFF LƯỢT TIẾP THEO...")
                print(f"{Fore.MAGENTA}CONTACT: @iosnea")
                print(f"{Fore.MAGENTA}{'='*60}")
                time.sleep(1)

if __name__ == "__main__":
    iosnea_Tools().start()
    