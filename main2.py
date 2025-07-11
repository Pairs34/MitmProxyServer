from urllib.parse import parse_qs, urlencode
from mitmproxy import http
import re
import secrets
import uuid
from typing import List, Tuple
import requests

class Modifier:
    def __init__(self):
        self.header_replace_map = {
            "User-Agent": "Hepsiburada/5.64.1 (com.pozitron.hepsiburada;build:409;Android 28)OkHttp/5.0.0-alpha.2",
        }

        self.target_domains = [
            "https://scorpion.hepsiburada.com/api/v3/appcore/init",
            "https://mobileapi.hepsiburada.com/api/CartItemCount",
            "https://mobileapi.hepsiburada.com/api/AddCartItems",
            "https://app.adjust.com/event",
            "https://checkout.hepsiburada.com/mobile/api/v1/basket/all",
            "https://checkout.hepsiburada.com/mobile/api/v2/checkout/getcheckout?isFirstLoad=true"
        ]

    def is_target_domain(self, url: str) -> bool:
        for domain in self.target_domains:
            if domain in url:
                return True
        return False

    def generate_device_headers(self):
        hex_id = secrets.token_hex(8)
        uuid1 = str(uuid.uuid4())
        uuid2 = str(uuid.uuid4())
        return {
            "x-unique-campaign-id": hex_id,
            "unique-device-id": hex_id,
            "x-device-id": uuid1,
            "x-anonymous-id": uuid2
        }

    def request(self, flow: http.HTTPFlow):
        # if not self.is_target_domain(flow.request.pretty_url):
        #     return
        
        if "mylist" in flow.request.pretty_url:
            print("Skipping request to mylist")
            session = requests.Session()
            session.max_redirects = 10
            response = session.get("https://app.hb.biz/5nlTxOU4b2Km", allow_redirects=True, headers=flow.request.headers)
            print(response.status_code)
            print(response.url)
        
        if "application/x-www-form-urlencoded" in flow.request.headers.get("Content-Type", ""):
            try:
                body = flow.request.get_text()
                form_data = parse_qs(body)

                # 🔧 Örnek değişiklikler
                if "package_name" in form_data:
                    form_data["package_name"] = ["com.pozitron.hepsiburada"]

                # Encode edip tekrar yaz
                new_body = urlencode(form_data, doseq=True)
                flow.request.set_text(new_body)

            except Exception:
                pass

        # Statik header'ları ata
        for key, value in self.header_replace_map.items():
            if key in flow.request.headers:
                flow.request.headers[key] = value

        # Dinamik kimlik header'larını ata
        random_headers = self.generate_device_headers()
        for key, value in random_headers.items():
            flow.request.headers[key] = value
            
        flow.request.headers["x-audibillah"] = "Kodda kaybolanlar değil, kodla var olanlar bilir."

    def response(self, flow: http.HTTPFlow):
        return

addons = [
    Modifier()
]
