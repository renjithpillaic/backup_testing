import datetime
import os
from netmiko import ConnectHandler

DEVICE_FILE = "devices.txt"
USERNAME = "cisco"
PASSWORD = "Cisco123!"  # Update with your lab password

def backup_ios_nxos(ip):
    device = {
        "device_type": "cisco_ios",  # Default to IOS
        "ip": ip,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": PASSWORD,
    }

    try:
        # Step 1: Try SSH, fallback to Telnet
        try:
            connection = ConnectHandler(**device)
        except Exception:
            print(f"SSH failed for {ip}, trying Telnet...")
            device["device_type"] = "cisco_ios_telnet"
            connection = ConnectHandler(**device)

        connection.enable()

        # Step 2: Detect NX-OS
        version = connection.send_command("show version")
        if "NX-OS" in version:
            print(f"Detected Nexus Platform on {ip}. Switching driver...")
            connection.disconnect()

            device["device_type"] = "cisco_nxos"
            try:
                connection = ConnectHandler(**device)
            except Exception:
                print(f"Nexus SSH failed for {ip}, trying Nexus Telnet...")
                device["device_type"] = "cisco_nxos_telnet"
                connection = ConnectHandler(**device)

            connection.enable()

        # Step 3: Backup config
        print(f"Pulling running configuration from {ip}...")
        output = connection.send_command("show running-config")
        save_config(ip, output)

        connection.disconnect()

    except Exception as e:
        print(f"Failed to backup {ip}: {e}")

def save_config(identifier, config):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{identifier}_{timestamp}.txt"
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
        
        # Push all backups to GitHub
        git_push()

    except FileNotFoundError:
        print(f"Error: Inventory file '{DEVICE_FILE}' not found in the current directory.")

if __name__ == "__main__":
    main()
