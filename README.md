
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

