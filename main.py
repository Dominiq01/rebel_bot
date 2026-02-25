import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURACJA PRODUKTÓW ---
# Dodaj tutaj wszystkie linki, które chcesz śledzić
PRODUCTS = [
    {"name": "151 Ultra Premium Collection",
     "url": "https://www.rebel.pl/produkty/pokemon-tcg-scarlet-violet-151-ultra-premium-collection-202379.html"},
    {"name": "151 Booster Bundle",
     "url": "https://www.rebel.pl/produkty/pokemon-tcg-scarlet-violet-151-booster-bundle-202377.html"},
    {"name": "Prismatic Evolutions ETB",
     "url": "https://www.rebel.pl/produkty/pokemon-tcg-sv8.5-prismatic-evolutions-elite-trainer-box-210134.html"},
    # Możesz dopisać kolejne produkty w tym samym formacie
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})


def check_availability():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    found_items = []

    try:
        for product in PRODUCTS:
            print(f"Sprawdzam: {product['name']}...")
            driver.get(product['url'])
            time.sleep(3)  # Krótka przerwa na załadowanie

            try:
                # Rebel używa klasy .product-cart-submit dla przycisku zakupu
                btn = driver.find_element(By.CSS_SELECTOR, ".product-cart-submit")

                # Jeśli przycisk istnieje i jest widoczny/klikalny
                if btn.is_displayed() and btn.is_enabled():
                    # Dodatkowy check tekstu na przycisku dla pewności
                    if "koszyk" in btn.text.lower():
                        found_items.append(product)
            except:
                # Jeśli nie ma przycisku, produkt prawdopodobnie niedostępny
                continue

    finally:
        driver.quit()

    return found_items


if __name__ == "__main__":
    available_now = check_availability()

    if available_now:
        message = "🚨 *Dostępne produkty Pokemon!*\n\n"
        for item in available_now:
            message += f"✅ {item['name']}\n🔗 [Kup teraz]({item['url']})\n\n"

        send_telegram(message)
        print(f"Znaleziono: {len(available_now)} szt.")
    else:
        print("Wszystko wyprzedane.")