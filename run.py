from mitmproxy.tools.main import mitmweb

def run_mitm_script():
    mitmweb([
        "-s", "main.py",
        "--mode", "socks5",
        "--listen-host", "0.0.0.0",
        "--listen-port", "8888",
        "--web-host", "0.0.0.0",
        "--web-port", "8081",
        "--set", "block_global=false",
        "--set", "web_password=Yldrm!34"
    ])

if __name__ == '__main__':
    run_mitm_script()