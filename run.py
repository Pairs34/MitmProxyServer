from mitmproxy.tools.main import mitmweb

def run_mitm_script():
    mitmweb([
        "-s", "main.py",           # senin scriptin
        # "--mode", "socks5",        # SOCKS5 proxy modu
        "--listen-port", "8888",   # proxy portu
        "--web-port", "8081",      # web arayüz portu (default 8081)
        "--set", "web_open_browser=true"  # tarayıcıyı otomatik açmak istersen
    ])

run_mitm_script()
