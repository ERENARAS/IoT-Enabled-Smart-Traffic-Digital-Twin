
# Smart Ambulance Priority System
This project is a hybrid prototype system designed to automatically grant priority passage to emergency vehicles (ambulances) at traffic lights. The system synchronizes real-world hardware detection (using a Raspberry Pi and Camera) with a virtual traffic simulation (SUMO).
## Project Goal
The primary objective is to minimize waiting times for ambulances at busy intersections, thereby reducing response times for emergencies and preventing potential accidents at crossroads. The system visually detects the ambulance and safely switches the intersection lights to green for the emergency vehicle while turning conflicting directions red.
## System Architecture
The system consists of two main independent units communicating over a TCP/IP network: the "Field Hardware" and the "Simulation Computer".

<img width="2816" height="1536" alt="Gemini_Generated_Image_1balgz1balgz1bal" src="https://github.com/user-attachments/assets/89a4fcf4-e3d6-4486-a4ea-babbeb5d515a" />

#### 1. Field / Real World (Raspberry Pi)

This unit acts as the "eye" of the system and the physical control point in the real world.

* Camera Detection (OpenCV): Captures real-time video via a USB camera. Using Python and the OpenCV library, it analyzes frames to detect specific colors representing an ambulance (e.g., red emergency lights).
* GPIO Control: Manages the Raspberry Pi's GPIO pins based on detection status. It controls physical traffic lights (LEDs) and updates status messages on an I2C LCD screen (e.g., "AMBULANCE PASSING").
* Socket Server: Listens for incoming connection requests from the simulation computer and broadcasts the current detection status ("Ambulance Arrived" or "Ambulance Gone") over the network.

#### 2. Simulation Computer (SUMO)

This unit runs the virtual digital twin of the intersection.

* SUMO Simulation: Simulates vehicle traffic and virtual traffic lights within a predefined intersection scenario.
* TraCI (Traffic Control Interface): Allows the Python script to interface with and manipulate the running SUMO simulation in real-time (e.g., changing traffic light phases).
* Socket Client: Connects to the Raspberry Pi server. Upon receiving an "Ambulance Arrived" signal from the field, it uses TraCI to switch the simulation's traffic lights to green in the ambulance's direction, synchronizing the virtual world with real-world events.

## Hardware Connection Schematic

The wiring details for the Raspberry Pi and peripheral components used in the field unit are shown in the schematic below.

##### Components and GPIO Pin Mapping:

- Raspberry Pi 4 (or Model 3B+): Main control unit.
- USB Web Camera: For image processing.
- Traffic Lights (LEDs):
  * Red LED -> GPIO 17
  * Yellow LED -> GPIO 22
  * Green LED -> GPIO 27
  * (Note: Appropriate resistors, e.g., 220Ω or 330Ω, must be used for each LED)
-16x2 LCD Screen (with I2C Backpack - PCF8574):
  * SDA -> GPIO 2 (SDA)
  * SCL -> GPIO 3 (SCL)
  * VCC -> 5V
  * GND -> GND
<img width="2816" height="1536" alt="Gemini_Generated_Image_k3jp5fk3jp5fk3jp" src="https://github.com/user-attachments/assets/b1c67dd6-7877-42a1-8cf9-eb01f9169cd7" />


## Installation and Requirements

##### Hardware Requirements

* Raspberry Pi (with Wi-Fi or Ethernet connectivity)
* USB Camera
* Red, Yellow, and Green LEDs with resistors
* 16x2 LCD Screen with I2C interface
* Breadboard and Jumper wires
* A PC/Laptop for simulation

##### Software Requirements
Raspberry Pi Side (Python 3):
```bash
pip3 install opencv-python
pip3 install RPi.GPIO
pip3 install RPLCD smbus2
```

(Note: Ensure I2C is enabled via raspi-config.)

###### Computer Side:
  * [SUMO - Simulation of Urban MObility](https://eclipse.dev/sumo/) must be installed.
  * Python 3 and the traci library (usually comes with SUMO, or install via pip install traci).

## Usage
  1. Assemble the hardware connections according to the provided schematic.
  2. First, run the Python simulation script (the client) on your PC. This script will wait for a connection from the Pi.
  3. Next, run the camera detection and server script on the Raspberry Pi.
  4. Trigger the system by showing the defined target color (simulating an ambulance) to the camera:
     * The physical Green LED on the Pi will turn on.
     * The LCD screen will display an "EMERGENCY" message.
     * The corresponding traffic light in the running SUMO simulation will also turn green simultaneously.

## Future Development
Future iterations of this system could include:
  * Replacing simple color detection with AI-based object detection (e.g., YOLO) for accurate ambulance recognition.
  * Integration of a "Green Wave" system where multiple intersections coordinate to provide a continuous clear path.
  * Adding an audio detection module to identify siren sounds.
