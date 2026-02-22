import os
import time
import threading
import queue
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

chrome_options = Options()
user_data_dir = os.path.expanduser("~/whatsapp-session")
chrome_options.add_argument(f"user-data-dir={user_data_dir}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(60)

message_queue = queue.Queue()

def whatsapp_goto(url):
    driver.get(url)
    WebDriverWait(driver, 25).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@contenteditable='true']")
        )
    )
    print("WhatsApp Web loaded")

def send_message(phone_number, message):
    try:
        whatsapp_goto(
            f"https://web.whatsapp.com/send?phone={phone_number}&text={message}"
        )

        time.sleep(2)

        try:
            invalid = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(text(),'invalid')]")
                )
            )
            if invalid:
                return False, "Invalid or unregistered number"
        except:
            pass

        WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Send']")
            )
        ).click()

        time.sleep(1)
        return True, "Message sent"

    except Exception as e:
        return False, str(e)

def queue_worker():
    while True:
        phone_number, message = message_queue.get()
        try:
            success, msg = send_message(phone_number, message)
            print(f"[QUEUE] {phone_number} → {msg}")
        except Exception as e:
            print(f"[QUEUE ERROR] {e}")
        finally:
            message_queue.task_done()
            time.sleep(2)

@app.route("/send-message", methods=["POST"])
def api_send_message():
    data = request.json
    phone_number = data.get("phone_number")
    message = data.get("message")

    if not phone_number or not message:
        return jsonify({
            "status": "error",
            "message": "phone_number and message are required"
        }), 400

    message_queue.put((phone_number, message))

    return jsonify({
        "status": "queued",
        "message": "Message added to queue",
        "queue_size": message_queue.qsize()
    }), 202

def run_flask():
    app.run(host="0.0.0.0", port=5005)

if __name__ == "__main__":
    whatsapp_goto("https://web.whatsapp.com/")

    threading.Thread(target=queue_worker, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()

    while True:
        time.sleep(1)