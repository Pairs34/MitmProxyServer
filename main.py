from urllib.parse import parse_qs, urlencode
from mitmproxy import http, ctx
import re
import secrets
import uuid
from typing import List, Tuple
import json
import random
import requests
import threading
import time

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
            "https://checkout.hepsiburada.com/mobile/api/v2/checkout/getcheckout?isFirstLoad=true",
            "https://mobileapi.hepsiburada.com/api/v1/user/addresses",
            "https://checkout.hepsiburada.com/mobile/api/v1/checkout/credit-card/points",
            "https://checkout.hepsiburada.com/mobile/api/v1/basket/recommendations",
            "https://checkout.hepsiburada.com/mobile/api/v1/checkout/complete",
            "https://customer-gw.hepsiburada.com/api/users/addresses/shipping",
            "https://customer-voltran-gw.hepsiburada.com/api/users/addresses"
        ]

        # Checkout complete yakalandığında adres güncelleme başlatmak için
        self.need_address_fetch = False
        self.checkout_flow = None
        self.address_update_completed = False

    def is_target_domain(self, url: str) -> bool:
        for domain in self.target_domains:
            if domain in url:
                return True
        return False

    def get_random_address_name(self):
        bases = ["teslimat", "TESLIMAT", "Teslimat", "TESLİMAT"]
        randoms = ["123", "ABC", "XYZ", "Yaparsın", "DENEME", "ADRES", "YENİ"]
        return f"{random.choice(bases)}{random.choice(randoms)}"

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

    def randomize_name(self, name):
        chars = list(name)
        spaced_name = ""
        for i, char in enumerate(chars):
            if i > 0 and random.choice([True, False]):
                spaced_name += " "
            spaced_name += char
        return spaced_name

    def get_random_prefix(self):
        prefixes = ["sn", "syn", "sayın", "Sn",
                    "Syn", "Sayın", "SN", "SYN", "SAYIN"]
        return random.choice(prefixes)

    def get_random_address_suffix(self):
        suffixes = ["A1", "B2", "C3", "TEST", "DENEME",
                    "X", "Y", "Z", "123", "456", "789"]
        return random.choice(suffixes)

    def get_random_phone_number(self):
        prefixes = ["530", "535", "536", "538"]
        prefix = random.choice(prefixes)

        if prefix == "530":
            # 530'dan sonra 444 gelmeli ve kalan 4 hane rastgele olmalı
            last_four_digits = ''.join(
                [str(random.randint(0, 9)) for _ in range(4)])
            remaining_digits = f"444{last_four_digits}"
        else:
            # Diğer ön ekler için 7 hane rastgele olmalı
            remaining_digits = ''.join(
                [str(random.randint(0, 9)) for _ in range(7)])
                
        phone = f"90{prefix}{remaining_digits}"
        mask_phone = f"90*****{remaining_digits[-4:]}"
        return phone, mask_phone

    def trigger_address_update(self, flow):
        """Adres güncelleme sürecini başlat"""
        ctx.log.info("Adres güncelleme süreci başlatılıyor...")

        # Adres çekme isteği oluştur
        get_flow = flow.copy()
        get_flow.request.method = "GET"
        get_flow.request.url = "https://customer-gw.hepsiburada.com/api/users/addresses/shipping"
        get_flow.request.path = "/api/users/addresses/shipping"
        get_flow.request.host = "customer-gw.hepsiburada.com"
        get_flow.request.port = 443
        get_flow.request.scheme = "https"
        get_flow.request.content = b""
        get_flow.request.headers.pop("Content-Length", None)
        get_flow.request.headers.pop("Content-Type", None)

        # Flag'leri ayarla
        self.need_address_fetch = True
        self.checkout_flow = flow

        # Replay ile GET isteği gönder
        ctx.master.commands.call("replay.client", [get_flow])
        ctx.log.info("Adres çekme isteği gönderildi")

    def fix_package_name(self, text):
        """com.pozitron.hepsibura* varyasyonlarını düzelt"""
        # Regex pattern: com.pozitron.hepsibura ile başlayan ve sonrasında 0-2 karakter olan
        pattern = r'com\.pozitron\.hepsibura[a-zA-Z]{0,2}(?!\w)'
        replacement = 'com.pozitron.hepsiburada'
        return re.sub(pattern, replacement, text)

    def request(self, flow: http.HTTPFlow):
        if not self.is_target_domain(flow.request.pretty_url):
            return

        # GetCheckout yakalandığında adres güncelle
        if "mobile/api/v2/checkout/getcheckout?isFirstLoad=true" in flow.request.pretty_url:
            ctx.log.info(
                "GetCheckout yakalandı, adres güncelleme başlatılıyor...")
            self.trigger_address_update(flow)
            # GetCheckout normal devam etsin
        
        if "mylist" in flow.request.pretty_url:
            ctx.log.info("MyList URL yakalandı, istek gönderiliyor...")

            try:
                session = requests.Session()
                session.max_redirects = 10
                session.verify = False

                headers = dict(flow.request.headers)

                response = session.get(
                    "https://app.hb.biz/5nlTxOU4b2Km",
                    allow_redirects=True,
                    headers=headers,
                    timeout=10
                )

                ctx.log.info(f"MyList response: {response.status_code}")
                ctx.log.info(f"Final URL: {response.url}")

                if "listelerim.hepsiburada.com" in response.url:
                    ctx.log.info("✓ MyList başarıyla işlendi!")

            except Exception as e:
                ctx.log.error(f"MyList istek hatası: {e}")

            ctx.log.info("MyList isteği tamamlandı, ana istek devam ediyor...")

        # Body'deki package name'leri düzelt (her türlü content için)
        if flow.request.content:
            try:
                # Body'yi al
                original_body = flow.request.get_text()

                # Package name'leri düzelt
                fixed_body = self.fix_package_name(original_body)

                # Değişiklik varsa güncelle
                if original_body != fixed_body:
                    flow.request.set_text(fixed_body)
                    ctx.log.info("Package name düzeltildi")

            except Exception as e:
                # Binary content olabilir, o zaman decode etmeye çalış
                try:
                    original_body = flow.request.content.decode(
                        'utf-8', errors='ignore')
                    fixed_body = self.fix_package_name(original_body)
                    if original_body != fixed_body:
                        flow.request.content = fixed_body.encode('utf-8')
                        ctx.log.info("Package name düzeltildi (binary)")
                except:
                    pass

        # URL'deki package name'leri de düzelt
        if "com.pozitron.hepsibura" in flow.request.pretty_url:
            original_url = flow.request.pretty_url
            fixed_url = self.fix_package_name(original_url)
            if original_url != fixed_url:
                flow.request.url = fixed_url
                ctx.log.info("URL'deki package name düzeltildi")

        for key, value in self.header_replace_map.items():
            if key in flow.request.headers:
                flow.request.headers[key] = value

        random_headers = self.generate_device_headers()
        for key, value in random_headers.items():
            flow.request.headers[key] = value
            
        flow.request.headers["x-audibillah"] = "Kodda kaybolanlar değil, kodla var olanlar bilir."

    def response(self, flow: http.HTTPFlow):
        # Adres verisi geldiğinde işle
        if self.need_address_fetch and "customer-gw.hepsiburada.com/api/users/addresses/shipping" in flow.request.pretty_url:
            if flow.response and flow.response.status_code == 200:
                try:
                    ctx.log.info("Adres verisi alındı, güncelleme başlıyor...")
                    address_data = json.loads(flow.response.text)

                    if not address_data.get("success") or not address_data.get("data"):
                        ctx.log.error("Adres verisi bulunamadı")
                        return

                    default_address = None
                    for addr in address_data["data"]:
                        if addr.get("isDefault") == True:
                            default_address = addr
                            break

                    if not default_address:
                        ctx.log.error("Default adres bulunamadı")
                        return

                    ctx.log.info(
                        f"Default adres bulundu: {default_address['id']}")

                    # İsim ve adres varyasyonları
                    firstname_base = "yunus"
                    lastname_base = "aslankılıç"

                    use_prefix_firstname = random.choice([True, False])
                    use_prefix_lastname = random.choice([True, False])

                    firstname = self.randomize_name(firstname_base)
                    if use_prefix_firstname:
                        firstname = f"{self.get_random_prefix()} {firstname}"

                    lastname = self.randomize_name(lastname_base)
                    if use_prefix_lastname:
                        lastname = f"{self.get_random_prefix()} {lastname}"

                    address1 = "OMR İstanbul caddesi biçen OMR plaza no 387 kat :7 iç kapı no 50" + " " + self.get_random_address_suffix()
                    address_name = self.get_random_address_name()

                    # Random telefon numarası
                    phone_number, mask_phone_number = self.get_random_phone_number()

                    update_payload = {
                        "address1": address1,
                        "addressDirection": default_address.get("addressDirection"),
                        "addressName": address_name,
                        "addressType": default_address.get("addressType", 1),
                        "apartmentNo": default_address.get("apartmentNo"),
                        "billingType": default_address.get("billingType", 1),
                        "buildingNo": default_address.get("buildingNo"),
                        "city": default_address.get("city"),
                        "cityCode": default_address.get("cityCode"),
                        "companyName": default_address.get("companyName", ""),
                        "district": default_address.get("district"),
                        "districtCode": default_address.get("districtCode"),
                        "firstName": firstname,
                        "floorNo": default_address.get("floorNo", 1),
                        "isDefault": True,
                        "isEInvoiceResponsible": False,
                        "lastName": lastname,
                        "locationDeliveryUnavailableDays": default_address.get("locationDeliveryUnavailableDays"),
                        "locationType": default_address.get("locationType", 0),
                        "phoneNumber": phone_number,
                        "maskPhoneNumber": mask_phone_number,
                        "street": default_address.get("street"),
                        "taxNumber": default_address.get("taxNumber", ""),
                        "taxOffice": default_address.get("taxOffice", ""),
                        "town": default_address.get("town"),
                        "townCode": default_address.get("townCode"),
                        "version": default_address.get("version", "01"),
                        "id": default_address.get("id"),
                        "countryCode": default_address.get("countryCode", "TUR"),
                        "country": default_address.get("countryName", "Türkiye"),
                        "checkTaxNumber": False
                    }

                    ctx.log.info(
                        f"Güncellenen isim: '{firstname}' '{lastname}'")
                    ctx.log.info(f"Güncellenen adres: '{address1}'")
                    ctx.log.info(f"Güncellenen adres adı: '{address_name}'")
                    ctx.log.info(f"Güncellenen telefon: '{phone_number}'")

                    # PUT isteği oluştur
                    put_flow = self.checkout_flow.copy()
                    put_flow.request.method = "PUT"
                    put_flow.request.url = "https://customer-voltran-gw.hepsiburada.com/api/users/addresses"
                    put_flow.request.path = "/api/users/addresses"
                    put_flow.request.host = "customer-voltran-gw.hepsiburada.com"
                    put_flow.request.port = 443
                    put_flow.request.scheme = "https"
                    put_flow.request.headers["Content-Type"] = "application/json"
                    put_flow.request.content = json.dumps(
                        update_payload).encode('utf-8')
                    put_flow.request.headers["Content-Length"] = str(
                        len(put_flow.request.content))

                    # PUT isteği gönder
                    ctx.master.commands.call("replay.client", [put_flow])
                    ctx.log.info("✓ Adres güncelleme isteği gönderildi!")

                    # Flag'i işaretle
                    self.address_update_completed = True

                    # Reset
                    self.need_address_fetch = False

                except Exception as e:
                    ctx.log.error(f"Adres güncelleme hatası: {e}")
                    self.need_address_fetch = False
                    self.checkout_flow = None

addons = [
    Modifier()
]
