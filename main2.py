from urllib.parse import parse_qs, urlencode
from mitmproxy import http, ctx
import re
import secrets
import uuid
from typing import List, Tuple


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

        # MyList yönlendirmeleri için depolama
        self.mylist_redirects = {}

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
        if "application/x-www-form-urlencoded" in flow.request.headers.get("Content-Type", ""):
            try:
                body = flow.request.get_text()
                form_data = parse_qs(body)

                if "package_name" in form_data:
                    form_data["package_name"] = ["com.pozitron.hepsiburada"]

                new_body = urlencode(form_data, doseq=True)
                flow.request.set_text(new_body)

            except Exception:
                pass

        for key, value in self.header_replace_map.items():
            if key in flow.request.headers:
                flow.request.headers[key] = value

        random_headers = self.generate_device_headers()
        for key, value in random_headers.items():
            flow.request.headers[key] = value

        flow.request.headers["x-audibillah"] = "Kodda kaybolanlar değil, kodla var olanlar bilir."

    def response(self, flow: http.HTTPFlow):
        flow_id = id(flow)

        if flow_id in self.mylist_redirects:
            if "app.hb.biz" in flow.request.pretty_host and flow.response.status_code in [301, 302, 303, 307, 308]:
                ctx.log.info("app.hb.biz redirect yapıyor, devam ediliyor...")
                return

            if "hepsiburada.com" in flow.request.pretty_host:
                original_url = self.mylist_redirects[flow_id]

                ctx.log.info(f"Orijinal MyList URL'ye yönlendiriliyor: {original_url}")

                flow.response = http.Response.make(
                    302,
                    b"",
                    {"Location": original_url}
                )

                # Temizle
                del self.mylist_redirects[flow_id]


addons = [
    Modifier()
]