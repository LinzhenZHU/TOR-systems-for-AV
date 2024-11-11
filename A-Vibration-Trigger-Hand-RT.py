import socket
import time
import os
# ESP32's IP address and port number
ESP32_IP = '192.168.4.1'  # Replace with your ESP32's IP address
ESP32_PORT = 80

def send_command(command):
    try:
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to ESP32 server
        client_socket.connect((ESP32_IP, ESP32_PORT))

        # Build HTTP GET request
        request = f"GET /{command} HTTP/1.1\r\nHost: {ESP32_IP}\r\n\r\n"
        client_socket.send(request.encode())

        time.sleep(1)
        # Close connection
        client_socket.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    command = input("2 enter")
    start_time = time.time()
    send_command(command)
    input("Press Enter to stop timing...")
    end_time = time.time()

    # Calculate reaction time
    reaction_time = end_time - start_time-2
    print(f"Your reaction time is: {reaction_time:.3f} seconds")

    file_path = "A-Vibration-Hand-RT.txt"
    if os.path.exists(file_path):
        with open(file_path, "a") as file:  # Append mode
            file.write(f"{reaction_time:.3f}\n")
    else:
        with open(file_path, "w") as file:  # Write mode (create new)
            file.write(f"{reaction_time:.3f}\n")


