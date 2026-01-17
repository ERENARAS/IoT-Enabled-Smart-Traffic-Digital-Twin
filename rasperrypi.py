import socket
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time


HOST = '0.0.0.0'
PORT = 12345


# Adresini 'i2cdetect -y 1' ile kontrol et (Genelde 0x27)
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)


KIRMIZI_PIN = 17
SARI_PIN = 22  # <--- YENİ EKLENDİ
YESIL_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pinleri Çıkış Olarak Ayarla
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
        pass  # Ekran hatası olursa sistem durmasın


def isiklari_sondur():
    GPIO.output(KIRMIZI_PIN, GPIO.LOW)
    GPIO.output(SARI_PIN, GPIO.LOW)
    GPIO.output(YESIL_PIN, GPIO.LOW)


def sistem_normal():
    # Sadece Kırmızı Yanar (Ambulans Yolu Kapalı)
    isiklari_sondur()
    GPIO.output(KIRMIZI_PIN, GPIO.HIGH)
    ekran_yaz("DURUM: GUVENLI", "Beklemede...")


def sistem_acil():
    # Sadece Yeşil Yanar (Ambulans Geçiyor)
    isiklari_sondur()
    GPIO.output(YESIL_PIN, GPIO.HIGH)
    ekran_yaz("!!! ACIL DURUM !!!", "AMBULANS GECIYOR")


def sistem_gecis():

    isiklari_sondur()
    GPIO.output(SARI_PIN, GPIO.HIGH)
    ekran_yaz("DIKKAT!", "Normale Donuyor")
    time.sleep(2)  # 2 Saniye Sarı Yanık Kalsın
    sistem_normal()  # Sonra Kırmızıya Dön



print("Sistem Başlatılıyor...")
ekran_yaz("Sistem Aciliyor", "Hazirlaniyor...")
sistem_normal()


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Pi Dinlemede... IP: {HOST} Port: {PORT}")
ekran_yaz("BAGLANTI", "BEKLENIYOR...")

try:
    conn, addr = server_socket.accept()
    print(f"🔗 BAGLANDI: {addr}")
    ekran_yaz("MAC BAGLANDI", "Simulasyon Hazir")
    time.sleep(2)
    sistem_normal()

    while True:
        data = conn.recv(1024).decode()
        if not data:
            break

        print(f"Gelen Veri: {data}")


        if "AMBULANS_GELDI" in data:
            sistem_acil()

        elif "AMBULANS_GITTI" in data:

            sistem_gecis()

except KeyboardInterrupt:
    print("\nKapatılıyor...")

finally:
    ekran_yaz("Sistem", "Kapandi")
    isiklari_sondur()
    GPIO.cleanup()
    conn.close()
    server_socket.close()