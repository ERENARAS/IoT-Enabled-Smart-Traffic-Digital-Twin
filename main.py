import os
import sys
import socket
import select


pi_ip = '192.168.1.21'
pi_port = 12345
sumo_config_file = "simulasyon.sumo.cfg"
junction_id = "J9"
PHASE_GREEN = 0
PHASE_YELLOW = 1
PHASE_RED = 2
YELLOW_DURATION = 3.0

client_socket = None

def establish_connection():
    global client_socket
    try:
        print(f"Connecting... {pi_ip}")
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((pi_ip, pi_port))
        client_socket.setblocking(0)
        print("CONNECTED")
    except:
        print("Pi Not Found")

def send_signal(message):
    if client_socket:
        try:
            client_socket.send(message.encode())
        except:
            pass


if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    
import traci
traci.start(["sumo-gui", "-c", sumo_config_file, "--start", "--delay", "100"])
establish_connection()

STATE_RED = 0
STATE_GREEN = 1
STATE_YELLOW = 2

current_state = STATE_RED
state_start_time = 0
traci.trafficlight.setPhase(junction_id, PHASE_RED)


camera_active_memory = False

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    sim_time = traci.simulation.getTime()

    # MESAJ OKU
    if client_socket:
        try:
            ready, _, _ = select.select([client_socket], [], [], 0)
            if ready:
                msg = client_socket.recv(1024).decode()
                if "AMBULANCE_ARRIVED" in msg:
                    camera_active_memory = True
                    print(" Signal: ARRIVED")
                elif "AMBULANCE_DEPARTED" in msg:
                    camera_active_memory = False
                    print(" Signal: DEPARTED")
        except: pass

    # SANAL KONTROL
    virtual_ambulance = False
    for v in traci.vehicle.getIDList():
        if "ambulans" in v:
            try:
                if traci.vehicle.getNextTLS(v)[0][2] < 60: virtual_ambulance = True
            except: pass
            break

    #  MANTIK
    if camera_active_memory or virtual_ambulance:
        if current_state != STATE_GREEN:
            traci.trafficlight.setPhase(junction_id, PHASE_GREEN)
            current_state = STATE_GREEN
            send_signal("AMBULANCE_ARRIVED")

    else:
        # Normale Dönüş
        if current_state == STATE_GREEN:
            traci.trafficlight.setPhase(junction_id, PHASE_YELLOW)
            current_state = STATE_YELLOW
            state_start_time = sim_time
            send_signal("AMBULANCE_DEPARTED") # Pi turns on Yellow

        elif current_state == STATE_YELLOW:
            if sim_time - state_start_time >= YELLOW_DURATION:
                traci.trafficlight.setPhase(junction_id, PHASE_RED)
                current_state = STATE_RED
                send_signal("SYSTEM_RED") # Pi turns on Red

        elif current_state == STATE_RED:
            traci.trafficlight.setPhase(junction_id, PHASE_RED)

traci.close()
if client_socket: client_socket.close()