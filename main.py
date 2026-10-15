import os
import subprocess
import sys

#   [message, script name]
options = {
    "url_set": ["Setup .ics URL", "store_ics.py"],
    "fetch_content": ["Fetch calendar content", "fetch.py"]
}

script_list = list(options.values())
for index, (message, _) in enumerate(script_list, start=1):
    print(f"{index}. {message}")

user_choice = input("Choose an option: ")

if user_choice.isdigit():
    choice_num = int(user_choice) - 1

    if 0 <= choice_num < len(script_list):
        _, script = script_list[choice_num]
        script_path = os.path.join(os.path.dirname(__file__), script)
        subprocess.run([sys.executable, script_path], check=True)
    else:
        print("Invalid option number.")
else:
    print("Please enter a valid number.")