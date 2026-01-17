import os
import sys
import socket
import select


pi_ip = '192.168.1.21'
pi_port = 12345
sumo_config_file = "simulasyon.sumo.cfg"
kavsak_id = "J9"
FAZ_YESIL = 0
FAZ_SARI = 1
FAZ_KIRMIZI = 2
SARI_SURESI = 3.0

client_socket = None

def baglanti_kur():
    global client_socket
    try:
        print(f"Baglaniliyor... {pi_ip}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((pi_ip, pi_port))
        client_socket.setblocking(0)
        print("BAGLANDI")
    except:
        print("Pi Yok")

def sinyal_gonder(mesaj):
    if client_socket:
        try: client_socket.send(mesaj.encode())
        except: pass


if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
traci.start(["sumo-gui", "-c", sumo_config_file, "--start", "--delay", "100"])
baglanti_kur()

STATE_RED = 0
STATE_GREEN = 1
STATE_YELLOW = 2

mevcut_state = STATE_RED
state_baslangic_zamani = 0
traci.trafficlight.setPhase(kavsak_id, FAZ_KIRMIZI)


kamera_aktif_hafiza = False

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    sim_time = traci.simulation.getTime()

    # MESAJ OKU
    if client_socket:
        try:
            ready, _, _ = select.select([client_socket], [], [], 0)
            if ready:
                msg = client_socket.recv(1024).decode()
                if "AMBULANS_GELDI" in msg:
                    kamera_aktif_hafiza = True
                    print(" Sinyal: GELDI")
                elif "AMBULANS_GITTI" in msg:
                    kamera_aktif_hafiza = False
                    print(" Sinyal: GITTI")
        except: pass

    # SANAL KONTROL
    sanal_ambulans = False
    for v in traci.vehicle.getIDList():
        if "ambulans" in v:
            try:
                if traci.vehicle.getNextTLS(v)[0][2] < 60: sanal_ambulans = True
            except: pass
            break

    #  MANTIK
    if kamera_aktif_hafiza or sanal_ambulans:
        if mevcut_state != STATE_GREEN:
            traci.trafficlight.setPhase(kavsak_id, FAZ_YESIL)
            mevcut_state = STATE_GREEN
            sinyal_gonder("AMBULANS_GELDI")

    else:
        # Normale Dönüş
        if mevcut_state == STATE_GREEN:
            traci.trafficlight.setPhase(kavsak_id, FAZ_SARI)
            mevcut_state = STATE_YELLOW
            state_baslangic_zamani = sim_time
            sinyal_gonder("AMBULANS_GITTI") # Pi Sarı yakacak

        elif mevcut_state == STATE_YELLOW:
            if sim_time - state_baslangic_zamani >= SARI_SURESI:
                traci.trafficlight.setPhase(kavsak_id, FAZ_KIRMIZI)
                mevcut_state = STATE_RED
                sinyal_gonder("SISTEM_KIRMIZI") # Pi Kırmızı yakacak

        elif mevcut_state == STATE_RED:
            traci.trafficlight.setPhase(kavsak_id, FAZ_KIRMIZI)

traci.close()
if client_socket: client_socket.close()