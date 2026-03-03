import os
import sys
import random
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

load_dotenv()

# --- CONFIGURATION ---
WAIT_TIME = 5
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ACCOUNT_PASS = os.getenv("REBEL_ACCOUNT_PASS")
ACCOUNT_EMAIL = os.getenv("REBEL_ACCOUNT_EMAIL")
STREET = os.getenv("STREET")
CITY = os.getenv("CITY")
ZIP = os.getenv("ZIP")
PHONE = os.getenv("PHONE")

ACCOUNT_LINK = "https://www.rebel.pl/account"
COLLECTION_LINK = "https://www.rebel.pl/account/collections/show/27583"
CHECKOUT_LINK = "https://www.rebel.pl/shopping/checkout"
MAIN_LINK = "https://www.rebel.pl"
CLEAR_CART_LINK = "https://www.rebel.pl/shopping/cart/truncate"

chrome_options = Options()
chrome_options.add_argument("--headless=new")
# chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
# chrome_options.add_argument(
#     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

stealth(driver,
        languages=['en-US', "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

def login():
    driver.get(ACCOUNT_LINK)
    email_input = driver.find_element(By.NAME, "login[login]")
    email_input.send_keys(ACCOUNT_EMAIL)
    pass_input = driver.find_element(By.NAME, "login[password]")
    pass_input.send_keys(ACCOUNT_PASS)
    login_btn = driver.find_element(By.ID, "login_submit")
    login_btn.click()


def handle_cookies(driver):
    """Automatically clicks the 'Agree' button on the Didomi cookie banner."""
    try:
        cookie_btn = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        cookie_btn.click()
        print("✅ Cookies accepted.")
    except:
        print("ℹ️ Cookie banner did not appear (skipping).")


def wait_and_type(driver, selector, text, timeout=WAIT_TIME):
    """Waits for element to be clickable, scrolls into view, clears, and types."""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(selector)
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    element.clear()
    element.send_keys(text)
    return element


def wait_and_click(driver, selector, timeout=WAIT_TIME):
    """Waits for element to be clickable, scrolls into view, and clicks."""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(selector)
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    element.click()
    return element


def fill_billing_address():
    # Fill Street
    wait_and_type(driver, (By.NAME, "billingaddress[street]"), STREET)

    # Fill ZIP
    wait_and_type(driver, (By.NAME, "billingaddress[zip]"), ZIP)

    # Fill City
    wait_and_type(driver, (By.NAME, "billingaddress[city]"), CITY)

    # Fill Phone
    wait_and_type(driver, (By.NAME, "billingaddress[phone]"), PHONE)

    # Click Submit
    wait_and_click(driver, (By.ID, "billingaddress_submit"))


# --- TELEGRAM INTERACTION ---
def send_telegram_with_buttons(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Buy Now", "callback_data": "approve"},
            {"text": "❌ Cancel", "callback_data": "cancel"}
        ]]
    }
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "reply_markup": keyboard}
    return requests.post(url, json=payload).json()

def send_telegram_screenshot(caption="Bot Screenshot"):
    """Takes a screenshot and sends it to Telegram."""
    path = "screen.png"
    driver.save_screenshot(path)
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(path, "rb") as photo:
        requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})

def wait_for_telegram_decision():
    # 1. First, "Drain" old updates to ignore previous clicks
    print("🧹 Clearing old Telegram messages...")
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    last_update = requests.get(url, params={"offset": -1}).json()

    if last_update.get("ok") and last_update["result"]:
        # Setting offset to the latest update + 1 tells Telegram we've seen everything
        new_offset = last_update["result"][0]["update_id"] + 1
    else:
        new_offset = None

    print("⏳ Waiting for FRESH Telegram approval...")
    while True:
        params = {"timeout": 30, "offset": new_offset}  # Use long polling (30s)
        try:
            response = requests.get(url, params=params).json()
            if response.get("ok"):
                for update in response["result"]:
                    new_offset = update["update_id"] + 1
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        # Tell Telegram we received the click so the "spinning" stops
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery",
                                      json={"callback_query_id": callback["id"]})

                        decision = callback["data"]
                        return decision == "approve"
        except Exception as e:
            print(f"Telegram error: {e}")
            time.sleep(2)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})


def scrape_cart_summary():
    """Scrapes product names and prices from the checkout summary."""
    try:
        # Wait for the summary container to exist
        summary_container = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "checkout__summary--items"))
        )

        items = summary_container.find_elements(By.CLASS_NAME, "media-body")
        product_list = []

        for item in items:
            name = item.find_element(By.TAG_NAME, "h6").text.strip()
            # Clean up the price/quantity text (removes extra spaces/newlines)
            details = item.find_element(By.TAG_NAME, "p").text.strip().replace('\n', '')
            product_list.append(f"  • {name}\n  └ {details}")

        return "\n".join(product_list) if product_list else "No items found."
    except Exception as e:
        print(f"Error scraping summary: {e}")
        return "Could not retrieve item list."



def start_monitor():
    while True:
        driver.get(MAIN_LINK)
        time.sleep(2)
        try:
            print(f"\n🔍 [{time.strftime('%H:%M:%S')}] Starting restock scan...")
            driver.get(COLLECTION_LINK)

            # 1. Get buyable products
            products = driver.find_elements(By.CLASS_NAME, "account__collection-item")
            to_buy = []

            for p in products:
                classes = p.get_attribute("class")
                if "in-cart" not in classes and "unavailable" not in classes:
                    try:
                        btn = p.find_element(By.CLASS_NAME, "add-to-cart__btn")
                        if btn.is_enabled() and btn.get_attribute("disabled") != "true":
                            to_buy.append(p.get_attribute("data-product_id"))
                    except:
                        continue

            # 2. DECISION: Buy or Wait?
            if len(to_buy) > 0:
                print(f"🔥 RESTOCK DETECTED! Found {len(to_buy)} items.")
                send_telegram(f"🔥 *Restock Detected!* Attempting to buy {len(to_buy)} items...")
                return to_buy  # Exit loop and proceed to purchase logic

            # 3. No items found? Wait and try again.
            wait_seconds = random.randint(45, 90)  # Randomize wait between 45-90 seconds
            print(f"😴 Nothing found. Sleeping for {wait_seconds}s...")
            time.sleep(wait_seconds)

        except Exception as e:
            print(f"⚠️ Monitor Error: {e}")
            time.sleep(10)  # Short wait before retry on crash


login()
handle_cookies(driver)

while True:
    try:
        items_to_buy = start_monitor()

        # Add item one by one without re-scanning the whole DOM
        for p_id in items_to_buy:
            try:
                driver.get(COLLECTION_LINK)
                # Target the specific product by its ID
                product_element = driver.find_element(By.CSS_SELECTOR, f'[data-product_id="{p_id}"]')
                buy_btn = product_element.find_element(By.CLASS_NAME, "add-to-cart__btn")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", buy_btn)
                buy_btn.click()

                print(f"✅ Added Product ID {p_id}")


            except Exception as e:
                print(f"⚠️ Failed to add {p_id}: {e}")
                continue

        print("🚀 Proceeding to checkout...")
        driver.get(CHECKOUT_LINK)
        try:
            payment_label = WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='paymentMethodContent']/ul/li[3]/label"))
            )
            payment_label.click()
            fill_billing_address()
        except:
            print("❌ Could not find checkout elements. Is cart empty?")
            continue

        try:
            total_price = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.ID, "summary-total"))
            ).text
        except:
            total_price = "Unknown"

        cart_items_text = scrape_cart_summary()

        # Remote Approval via Telegram
        msg = (
            f"*‼️REBEL RESTOCK ALERT‼️*\n\n"
            f"*🛒 Your Cart:*\n{cart_items_text}\n\n"
            f"💰 *Total:* {total_price}\n\n"
            f"Approve purchase?"
        )
        send_telegram_screenshot("Checking Checkout Page")
        send_telegram_with_buttons(msg)

        if wait_for_telegram_decision():
            print("✅ Purchase Approved!")

            accept_rules = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.NAME, "edit_checkout[accept_rules]"))
            )
            driver.execute_script("arguments[0].click();", accept_rules)

            # BE CAREFUL! Uncomment the line below to actually place the order
            wait_and_click(driver, (By.ID, "edit_checkout_submit"))
            send_telegram("🚀 Order complete! Restarting bot in 3 mins...")
            send_telegram("🚀 Order has been placed successfully!")
        else:
            print("❌ Order Cancelled.")
            send_telegram("❌ Order cancelled. Restarting bot...")
            driver.get(CLEAR_CART_LINK)
            driver.get(COLLECTION_LINK)

        print("🔄 Reactivating bot...")
        time.sleep(180)

    except Exception as e:
        print(f"💥 Critical Failure: {e}")
        send_telegram(f"⚠️ *Bot Crashed!* Error: {e}. Attempting auto-restart...")
        send_telegram_screenshot("Page Screen Error")
        time.sleep(60)
        login()
