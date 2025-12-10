import requests
import time
import threading
import sys
import termios
import tty
from RPLCD.i2c import CharLCD

API_URL = "https://toddlermessagingservice.onrender.com/messages"
SENDER = "A"

# ---- LCD ----
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()

# ---- GLOBAL STATE ----
current_display = ""
typing_buffer = ""
is_typing = False
last_message_timestamp = None

# ---- Utility za LCD ----
def show_on_lcd(text):
    global current_display
    current_display = text
    lcd.clear()
    lcd.write_string(text[:32])  # max 16x2

# ---- 1. SLANJE PORUKE ----
def send_message(text):
    requests.post(
        API_URL,
        json={"sender": SENDER, "text": text}
    )

# ---- 2. PRIMANJE PORUKA OD B ----
def fetch_messages():
    global last_message_timestamp, is_typing

    while True:
        try:
            r = requests.get(API_URL)
            msgs = r.json()

            # uzmi poslednju poruku
            if not msgs:
                time.sleep(1)
                continue

            last = msgs[-1]  # poslednja u listi
            sender = last["sender"]
            text = last["text"]
            timestamp = last["timestamp"]

            # prikazuj samo poruke od B
            if sender == "B":
                # prikazi novu poruku samo ako je nova
                if timestamp != last_message_timestamp and not is_typing:
                    show_on_lcd(text)
                    last_message_timestamp = timestamp

        except Exception as e:
            # print(e)
            pass

        time.sleep(1)

# ---- 3. NON-BLOCKING GETCHAR ZA TASTATURU ----
def get_char():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# ---- 4. HANDLER ZA KUCKANJE ----
def keyboard_input():
    global typing_buffer, is_typing

    while True:
        ch = get_char()

        # kada korisnik krene da kuca
        is_typing = True

        if ch == "\n":  # ENTER
            if typing_buffer.strip():
                send_message(typing_buffer)
                show_on_lcd(typing_buffer)
            typing_buffer = ""
            is_typing = False
            continue

        elif ch == "\x7f":  # BACKSPACE
            typing_buffer = typing_buffer[:-1]
        else:
            typing_buffer += ch

        # prikazi sta A kuca
        show_on_lcd(typing_buffer)


# ---- START THREADS ----
thread_keyboard = threading.Thread(target=keyboard_input, daemon=True)
thread_fetcher = threading.Thread(target=fetch_messages, daemon=True)

thread_keyboard.start()
thread_fetcher.start()

# Glavna petlja ne radi nista
while True:
    time.sleep(1)

