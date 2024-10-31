import json

def load_devices(filename="devices.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_devices(devices, filename="devices.json"):
    with open(filename, "w") as file:
        json.dump(devices, file, indent=4)

def add_device(devices, mac_address, ip_address, filename="devices.json"):
    device = {"mac": mac_address, "ip": ip_address}
    devices.append(device)
    save_devices(devices, filename)
    return devices
