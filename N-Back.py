import random
import time
import threading
import os

# Get user ID
user_id = input("Please enter your ID:")

# Define game parameters
n = int(input("Please enter the value of n (1 or 2):"))
total_rounds = 50
score = 0
start_round = 10
end_round = 40
probability_correct = 0.5  # Set probability of "correct" to 60%
displayed_messages = []  # Store all previously displayed messages

# Generate random number
def generate_number():
    return random.randint(0, 9)

# Handle user input
user_input = None

def get_user_input():
    global user_input
    user_input = input("")

# Clear screen function
def clear_screen():
    print("\n" * 100)  # Print multiple empty lines to cover previous output

# Game main loop
previous_numbers = []
for i in range(total_rounds):
    # Decide whether to generate a "correct" situation
    if random.random() < probability_correct and len(previous_numbers) >= n:
        # Generate the same number
        current_number = previous_numbers[-n]
    else:
        # Generate a different number
        while True:
            current_number = generate_number()
            if len(previous_numbers) < n or current_number != previous_numbers[-n]:
                break

    clear_screen()
    message = f"{current_number}"
    print(message)
    displayed_messages.append(message)  # Record displayed message

    # Start a new thread to receive user input
    user_input = None
    input_thread = threading.Thread(target=get_user_input)
    input_thread.start()

    # Display the number for 0.5 seconds
    time.sleep(0.5)
    clear_screen()  # Clear screen to display blank
    print(" ")  # Print blank line

    # Display blank screen for 2.5 seconds
    time.sleep(2.5)

    # Check user input and answer
    is_correct = (n <= len(previous_numbers) and current_number == previous_numbers[-n])
    if start_round <= i < end_round:
        if (user_input == "" and is_correct) or (user_input != "" and not is_correct):
            result_message = "Correct!"
            print(result_message)
            displayed_messages.append(result_message)  # Record displayed message
            score += 1
        else:
            result_message = "Incorrect!"
            print(result_message)
            displayed_messages.append(result_message)  # Record displayed message

    # Update the last n numbers
    previous_numbers.append(current_number)
    if len(previous_numbers) > n:
        previous_numbers.pop(0)

# Display game results
final_output = f"ID: {user_id}\nScore for numbers {start_round} to {end_round}: {score}/{end_round - start_round}"
print(final_output)
print("Summary:")
all_messages = ''.join(displayed_messages)
print(all_messages)

# Write results to a text file in the same directory as the program
file_path = "game_results.txt"
if os.path.exists(file_path):
    with open(file_path, "a") as file:  # Append mode
        file.write("\n" + final_output + "\n")
        file.write("Summary:\n")
        file.write(all_messages + "\n")
else:
    with open(file_path, "w") as file:  # Write mode (create new)
        file.write(final_output + "\n")
        file.write("Summary:\n")
        file.write(all_messages + "\n")



