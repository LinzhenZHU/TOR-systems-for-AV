import pyaudio
import numpy as np
import socket
import csv
import time

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 19600
CHUNK = 128  # Can be adjusted as needed

# Initialize pyaudio
audio = pyaudio.PyAudio()

# Open audio stream
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

RMS_THRESHOLD = 2000
# ESP32 IP address and port number
ESP32_IP = '192.168.4.1'  # Replace with your ESP32's IP address
ESP32_PORT = 80

# Reference for storing socket object
client_socket = None

def initialize_csv(csv_file_path):
    # Initialize CSV file with zero values
    try:
        with open(csv_file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['X', 'Y', 'Distance'])  # Write header
            csv_writer.writerow([0, 0, 0])  # Write initial values as zero
        print("Initialized CSV file with zero values")
    except Exception as e:
        print(f"Error initializing CSV file: {e}")

def read_last_line_and_write():
    # Read the last line of data and write to target CSV file
    try:
        with open('./data/source_data.csv', mode='r', newline='') as source_file:
            csv_reader = csv.reader(source_file)
            header = next(csv_reader)  # Read header
            last_row = list(csv_reader)[-1]  # Get last row of data

        with open('./data/target_data.csv', mode='w', newline='') as dest_file:
            csv_writer = csv.writer(dest_file)
            csv_writer.writerow(header)  # Write header
            csv_writer.writerow(last_row)  # Write last row of data

        print("Last row of data has been written to target CSV file, overwriting previous data")
    except Exception as e:
        print(f"Error reading or writing file: {e}")

try:
    print("Initializing data file...")
    initialize_csv('./data/target_data.csv')

    print("Starting audio recording...")

    # Discard first second of data
    for _ in range(int(RATE / CHUNK)):
        stream.read(CHUNK)

    print("Starting data processing...")

    while True:
        try:
            # Read data from stream
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        except IOError as e:
            # Handle overflow error
            if e.errno == -9981:
                print("Input overflow, buffer not read in time.")
                continue
            else:
                raise

        # Ensure data is valid
        if data.size == 0:
            print("Invalid data")
            continue

        # Calculate volume (RMS)
        rms = np.mean(data ** 2)

        print(rms)

        # Check if volume exceeds threshold
        if rms > RMS_THRESHOLD:
            print("Volume threshold exceeded")
            read_last_line_and_write()

            # Record reaction time
            start_time = time.time()
            input("Press Enter to stop timing...")
            end_time = time.time()
            reaction_time = end_time - start_time
            print(f"Your reaction time is: {reaction_time:.3f} seconds")

except KeyboardInterrupt:
    print("Recording terminated")
finally:
    # Close stream and terminate PyAudio
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Close client connection
    if client_socket:
        client_socket.close()

print("Program ended")
