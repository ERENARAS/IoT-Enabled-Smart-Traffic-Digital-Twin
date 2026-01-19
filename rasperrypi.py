import cv2
import numpy as np
import RPi.GPIO as GPIO
import socket
import select
import time
from RPLCD.i2c import CharLCD

HOST = '0.0.0.0'
PORT = 12345

# LCD Setup
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)

RED_PIN = 17
YELLOW_PIN = 22
GREEN_PIN = 27

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)


def write_to_screen(line1, line2):
    try:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2)
    except:
        pass


def turn_off_lights():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)


def mode_red():
    turn_off_lights()
    GPIO.output(RED_PIN, GPIO.HIGH)
    write_to_screen("STATUS: SAFE", "Camera Active...")


def mode_green():
    turn_off_lights()
    GPIO.output(GREEN_PIN, GPIO.HIGH)
    write_to_screen("!! EMERGENCY !!", "AMBULANCE PASS")


def mode_yellow():
    turn_off_lights()
    GPIO.output(YELLOW_PIN, GPIO.HIGH)
    write_to_screen("CAUTION!", "Returning Normal")


print("System Starting...")
mode_red()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Waiting for connection...")
conn, addr = server_socket.accept()
print(f"Connected: {addr}")
conn.setblocking(0)

cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)

red_detected = False

try:
    while True:

        ret, frame = cap.read()
        if ret:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Red color range
            lower1 = np.array([0, 100, 100])
            upper1 = np.array([10, 255, 255])
            lower2 = np.array([170, 100, 100])
            upper2 = np.array([180, 255, 255])
            mask = cv2.inRange(hsv, lower1, upper1) + cv2.inRange(hsv, lower2, upper2)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            red_present_now = False
            for c in contours:
                if cv2.contourArea(c) > 500:
                    red_present_now = True
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    break

            # LOGIC: Sending signals to PC
            if red_present_now:
                if not red_detected:
                    mode_green()
                    try:
                        conn.send("AMBULANCE_ARRIVED".encode())
                        print("CAMERA: Saw -> Turned Green")
                    except:
                        pass
                    red_detected = True

            else:
                if red_detected:
                    try:
                        conn.send("AMBULANCE_DEPARTED".encode())
                        print("CAMERA: Departed")
                    except:
                        pass
                    red_detected = False

            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

        # LOGIC: Receiving signals from PC
        try:
            ready, _, _ = select.select([conn], [], [], 0)
            if ready:
                data = conn.recv(1024).decode()

                if not red_detected: # Only listen to PC if camera doesn't see ambulance
                    if "AMBULANCE_DEPARTED" in data:
                        mode_yellow()
                    elif "SYSTEM_RED" in data:
                        mode_red()
                    elif "AMBULANCE_ARRIVED" in data:
                        mode_green()

        except:
            pass

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    GPIO.cleanup()
    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    server_socket.close()