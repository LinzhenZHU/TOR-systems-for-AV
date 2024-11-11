import pyaudio
import numpy as np
import socket
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
# ESP32's IP address and port number
ESP32_IP = '192.168.4.1'  # Replace with your ESP32's IP address
ESP32_PORT = 80

# Reference to store socket object
client_socket = None

def send_command(command):
    global client_socket
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to ESP32 server
        client_socket.connect((ESP32_IP, ESP32_PORT))

        # Build HTTP GET request
        request = f"GET /{command} HTTP/1.1\r\nHost: {ESP32_IP}\r\n\r\n"
        client_socket.send(request.encode())

    except Exception as e:
        print(f"Error: {e}")

try:
    print("Starting recording...")

    # Discard the first second of data
    for _ in range(int(RATE / CHUNK)):
        stream.read(CHUNK)

    print("Starting formal data processing...")

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

        # Check if above threshold
        if rms > RMS_THRESHOLD:
            print("Volume detected above threshold")
            send_command("1")  # Send command to ESP32

            # Start timing
            start_time = time.time()
            input("Press Enter to stop timing...")
            end_time = time.time()

            # Calculate reaction time
            reaction_time = end_time - start_time
            print(f"Your reaction time is: {reaction_time:.3f} seconds")

            break

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