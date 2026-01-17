import cv2
import numpy as np
import RPi.GPIO as GPIO
import socket
import select
import time
from RPLCD.i2c import CharLCD

HOST = '0.0.0.0'
PORT = 12345

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)

KIRMIZI_PIN = 17
SARI_PIN = 22
YESIL_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(KIRMIZI_PIN, GPIO.OUT)
GPIO.setup(SARI_PIN, GPIO.OUT)
GPIO.setup(YESIL_PIN, GPIO.OUT)


def ekran_yaz(satir1, satir2):
    try:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(satir1)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(satir2)
    except:
        pass


def isiklari_sondur():
    GPIO.output(KIRMIZI_PIN, GPIO.LOW)
    GPIO.output(SARI_PIN, GPIO.LOW)
    GPIO.output(YESIL_PIN, GPIO.LOW)


def mod_kirmizi():
    isiklari_sondur()
    GPIO.output(KIRMIZI_PIN, GPIO.HIGH)
    ekran_yaz("DURUM: GUVENLI", "Kamera Aktif...")


def mod_yesil():
    isiklari_sondur()
    GPIO.output(YESIL_PIN, GPIO.HIGH)
    ekran_yaz("!!! ACIL DURUM !!!", "AMBULANS GECIYOR")


def mod_sari():
    isiklari_sondur()
    GPIO.output(SARI_PIN, GPIO.HIGH)
    ekran_yaz("DIKKAT!", "Normale Donuyor")


print("Sistem Baslatiliyor...")
mod_kirmizi()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Baglanti Bekleniyor...")
conn, addr = server_socket.accept()
print(f"Baglandi: {addr}")
conn.setblocking(0)

cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)

kirmizi_algilandi = False

try:
    while True:

        ret, frame = cap.read()
        if ret:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([170, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask = cv2.inRange(hsv, lower1, upper1) + cv2.inRange(hsv, lower2, upper2)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            su_an_kirmizi_var = False
            for c in contours:
                if cv2.contourArea(c) > 500:
                    su_an_kirmizi_var = True
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    break

            if su_an_kirmizi_var:
                if not kirmizi_algilandi:

                    mod_yesil()
                    try:
                        conn.send("AMBULANS_GELDI".encode())
                        print("KAMERA: Gördüm -> Yeşil Yaktım")
                    except:
                        pass
                    kirmizi_algilandi = True

            else:
                if kirmizi_algilandi:

                    try:
                        conn.send("AMBULANS_GITTI".encode())
                        print("KAMERA: Gitti -> Mac'e bildirildi")
                    except:
                        pass
                    kirmizi_algilandi = False

            cv2.imshow('Kamera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        try:
            ready, _, _ = select.select([conn], [], [], 0)
            if ready:
                data = conn.recv(1024).decode()

                if not kirmizi_algilandi:
                    if "AMBULANS_GITTI" in data:
                        mod_sari()
                    elif "SISTEM_KIRMIZI" in data:
                        mod_kirmizi()
                    elif "AMBULANS_GELDI" in data:
                        mod_yesil()

        except:
            pass

except KeyboardInterrupt:
    print("Kapatiliyor...")
finally:
    GPIO.cleanup()
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    server_socket.close()