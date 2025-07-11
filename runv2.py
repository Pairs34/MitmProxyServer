from mitmproxy.tools.main import mitmweb


def run_mitm_script():
    proxy_host = "154.194.35.243"
    proxy_port = 7885
    proxy_user = "bCAfsgFwDf"
    proxy_pass = "I5QD2zZp01"

    mitmweb([
        "-s", "main2.py",
        "--mode", f"upstream:http://{proxy_host}:{proxy_port}",
        "--set", f"upstream_auth={proxy_user}:{proxy_pass}",
        "--listen-host", "0.0.0.0",
        "--listen-port", "8888",
        "--web-host", "0.0.0.0",
        "--web-port", "8081",
        "--set", "block_global=false",
        "--set", "web_password=Yldrm!34",
        "--set", "upstream_cert=false",
        "--set", "connection_strategy=lazy"
    ])


if __name__ == '__main__':
    run_mitm_script()