import datetime
import os
from netmiko import ConnectHandler

DEVICE_FILE = "devices.txt"
USERNAME = "cisco"
PASSWORD = "Cisco123!"

def backup_ios_nxos(ip):
    device = {
        "device_type": "cisco_ios",
        "ip": ip,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": PASSWORD,
    }

    try:
        try:
            connection = ConnectHandler(**device)
        except Exception:
            print(f"SSH failed for {ip}, trying Telnet...")
            device["device_type"] = "cisco_ios_telnet"
            connection = ConnectHandler(**device)

        connection.enable()

        version = connection.send_command("show version")
        if "NX-OS" in version:
            print(f"Detected Nexus Platform on {ip}. Switching driver...")
            connection.disconnect()
            device["device_type"] = "cisco_nxos"
            connection = ConnectHandler(**device)
            connection.enable()

        print(f"Pulling running configuration from {ip}...")
        output = connection.send_command("show running-config")
        save_config(ip, output)

        connection.disconnect()

    except Exception as e:
        print(f"Failed to backup {ip}: {e}")

def save_config(identifier, config):
    # Create folder with date and time
    folder_name = datetime.datetime.now().strftime("backup_%Y%m%d_%H%M")
    os.makedirs(folder_name, exist_ok=True)

    # Save file inside that folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{folder_name}/backup_{identifier}_{timestamp}.txt"
    with open(filename, "w") as f:
        f.write(config)
    print(f"Backup successful for {identifier} -> {filename}\n")

def git_push():
    try:
        os.system("git add .")
        os.system('git commit -m "Daily backup commit"')
        os.system("git push origin main")
        print("Backup pushed to GitHub successfully.")
    except Exception as e:
        print(f"Git push failed: {e}")

def main():
    try:
        with open(DEVICE_FILE, "r") as f:
            entries = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        for ip in entries:
            print(f"Starting backup sequence for node: {ip}")
            backup_ios_nxos(ip)
        git_push()
    except FileNotFoundError:
        print(f"Error: Inventory file '{DEVICE_FILE}' not found.")

if __name__ == "__main__":
    main()
