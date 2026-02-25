import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
load_dotenv()

# --- KONFIGURACJA PRODUKTÓW ---
PRODUCTS = [
    {"name": "Ascended Heroes - Elite Trainer Box",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-elite-trainer-box-dragonite-2028962.html?srsltid=AfmBOoq1CnEJp7pPQD2BBE12MH_Eozj72HtLIVgNvIuvkHQ0MFSsWRDz"},
    {"name": "Pokémon TCG: Poké Ball Tin",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-poke-ball-tin-2024308.html"},
    {"name": "Pokémon TCG: Mega Zygarde ex Premium Collection",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-zygarde-ex-premium-collection-2029283.html"},
    {"name": "Pokémon TCG: Mega Evolution - Ascended Heroes - Mega Feraligatr ex Box",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-mega-feraligatr-ex-box-2029280.html"},
    {"name": "Pokémon TCG: Mega Evolution - Ascended Heroes - Mega Emboar ex Box",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-mega-emboar-ex-box-2029279.html"},
    {"name": "Ascended Heroes - Booster Bundle",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-booster-bundle-2029282.html"},
    {"name": "Pokémon TCG: Mega Evolution - Ascended Heroes - Mega Meganium ex Box",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-mega-meganium-ex-box-2029278.html"},
    {"name": "Pokémon TCG: Mega Evolution - Perfect Order - Premium Checklane Blister Display (12)",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-mega-evolution-perfect-order-premium-checklane-blister-display-12-2029155.html"},
    {"name": "Pokémon TCG: Mega Evolution - Perfect Order - Elite Trainer Box",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-mega-evolution-perfect-order-elite-trainer-box-2029153.html"},
    {"name": "Pokémon TCG: Mega Evolution - Perfect Order - Booster Display (36)",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-mega-evolution-perfect-order-booster-display-36-2029149.html"},
    {"name": "Ascended Heroes - Trainer's 2-pack Blister",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-mega-evolution-ascended-heroes-trainer-s-2-pack-blister-larry-s-komola-2028771.html"},
    {"name": "Ascended Heroes - Trainer's 2-pack Blister",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-trainer-s-2-pack-blister-erika-s-tangela-2028770.html"},
    {"name": "Ascended Heroes - Deluxe Pin Collection - First Partners",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-deluxe-pin-collection-first-partners-2029138.html"},
    {"name": "Pokémon TCG: First Partner - Illustration Collection - Series 1",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-first-partner-illustration-collection-series-1-2029139.html"},
    {"name": "Ascended Heroes - Premium Poster Collection - Mega Gardevoir",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-premium-poster-collection-mega-gardevoir-2029016.html"},
    {"name": "Ascended Heroes - Premium Poster Collection - Mega Lucario",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-ascended-heroes-premium-poster-collection-mega-lucario-2029014.html"},
    {"name": "Phantasmal Flames - Elite Trainer Box",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-phantasmal-flames-elite-trainer-box-2027908.html"},
    {"name": "Phantasmal Flames - Booster Display (36)",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-phantasmal-flames-booster-display-36-2027904.html"},
    {"name": "Pokémon TCG: Mega Charizard X ex - Ultra-Premium Collection",
     "url": "https://www.rebel.pl/karcianki/pokemon-tcg-mega-charizard-x-ex-ultra-premium-collection-2027901.html"},
    {"name": "Mega Evolution - Elite Trainer Box - Gardevoir",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-elite-trainer-box-gardevoir-2027532.html"},
    {"name": "Mega Evolution - Elite Trainer Box - Lucario",
     "url": "https://www.rebel.pl/pokemon/pokemon-tcg-mega-evolution-elite-trainer-box-lucario-2027531.html"},
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    print(res.text)


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
            time.sleep(3)

            try:
                btn = driver.find_element(By.CSS_SELECTOR, ".product--details .add-to-cart__btn")

                if btn:
                    found_items.append(product)
            except:
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