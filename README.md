# TOR-systems-for-AV
### Requirements:
1. MCU ESP32, Vibration Motor connected to Pin D10.
2. UMH Board
3. CARLA Drive Simulation Platform
4. Intel RealSense Camera

## N-Back Task:
1. A N-back game to test the attention level of the users
2. You can define "N" to occupy different level of focus for the users
3. The potential correct rate can be modified freely!
4. The overall performance of the users will be recorded automatically

## Trigger:
1. TOR Trigger (To maximize the compatbility of all the Drive Simulation Platfroms, creatively realize the TOR Trigeer based on the sound, using a 3.5mm to 3.5mm cable to connect your trigger divice and your Simulation Platform. Adjust the parameters, to make the sound of the TOR from the Simulation Platform to enable a successful trigger!)
2. Remote Manully Trigger

## Terminal:
1. Contact Vibration Terminal (Hand & Face)
2. Contact-less Haptic UMH Terminal (Hand & Face)
The structure of two terminals:

# How to use:
The overall toplogy: ![Model]https://github.com/LinzhenZHU/TOR-systems-for-AV/blob/main/image.png
## A: Vibration|Hand
1. Upload Wearable_Vibration_Terminal.ino to the ESP32
2. Run A-Vibration-Trigger-Hand-RT.py to realize manully trigger, the reaction time of the users will be recorded automatically.
3. The Contact Vibration Terminal will stimuli if received the trigger signal.
4. Test A-Vibration-Trigger-Hand-Drive.py to see if the TOR sound in your Simulation Platform can enable the trigger or not, adjust the parameter to make the trigger work properly.
5. Run A-Vibration-Trigger-Hand-Drive.py to realize TOR trigger, the reaction time of the users will be recorded in the CARLA Platform.
6. The Contact Vibration Terminal will stimuli if received the trigger signal.

## B: UMH|Hand
1. Run the CircleHand.cs to drive the UMH Board
2. Test B-Midair-Trigger-Hand-Uni.py to see if the TOR sound in your Simulation Platform can enable the trigger or not, adjust the parameter to make the trigger work properly.
3. In order to control the variable, for this task, the manual trigger should also be triggered by a sound, please prepare a sound which can also trigger it properly. Play this sound to eanble the manual trigger.
4. Write the position coordinates of the hand into the CSV file.
5. The UMH Board will stimuli the hand position coordinates if received the trigger signal.
6. The reaction time of the users will be recorded automatically.

## C: Vibration|Face
1. Upload Wearable_Vibration_Terminal.ino to the ESP32
2. Run C-Vibration-Trigger-Face-RT.py to realize manully trigger, the reaction time of the users will be recorded automatically.
3. The Contact Vibration Terminal will stimuli if received the trigger signal.
4. Test C-Vibration-Trigger-Face-Drive.py to see if the TOR sound in your Simulation Platform can enable the trigger or not, adjust the parameter to make the trigger work properly.
5. Run C-Vibration-Trigger-Face-Drive.py to realize TOR trigger, the reaction time of the users will be recorded in the CARLA Platform.
6. The Contact Vibration Terminal will stimuli if received the trigger signal.

## D: UMH|Face
1. Run the CircleFace.cs to drive the UMH Board
2. Run D-FaceRecognition.py to use RealSense camera to recognition the facial sites in real-time. The 3D coordinates will be recorded into a CSV file.
3. Test D-Midair-Trigger-Face-Uni.py to see if the TOR sound in your Simulation Platform can enable the trigger or not, adjust the parameter to make the trigger work properly.
4. In order to control the variable, for this task, the manual trigger should also be triggered by a sound, please prepare a sound which can also trigger it properly. Play this sound to eanble the manual trigger.
5. The UMH Board will stimuli the latest face position coordinates if received the trigger signal.
6. The reaction time of the users will be recorded automatically.
