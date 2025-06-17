from mitmproxy.tools.main import mitmweb

def run_mitm_script():
    proxy_host = "154.194.35.243"
    proxy_port = 7885
    proxy_user = "bCAfsgFwDf"
    proxy_pass = "I5QD2zZp01"

    mitmweb([
        "-s", "main.py",        
        "--listen-port", "8888",
        "--web-port", "8081",
        # "--mode", f"upstream:http://{proxy_host}:{proxy_port}",
        # "--set", f"upstream_auth={proxy_user}:{proxy_pass}"
    ])

if __name__ == '__main__':
    run_mitm_script()