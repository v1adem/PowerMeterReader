import json

from rtu.Eastron.EastronSDM120 import EastronSDM120


class DeviceManager:
    def __init__(self):
        self.devices_parameters = {}
        self.devices = {}
        self.get_devices()

    def get_devices(self):
        try:
            with open("devices.json", 'r') as f:
                self.devices_parameters = json.load(f)
            for device in self.devices_parameters.values():
                if device["device_name"] == "Eastron-SDM120":
                    self.devices[device["custom_name"]] = EastronSDM120(device["custom_name"], device["device_address"],
                                                                        device["port"])
        except FileNotFoundError:
            self.devices = {}
        return self.devices

    def get_device_by_custom_name(self, custom_name):
        return self.devices.get(custom_name)

    def add_device(self, device):
        self.devices[device.custom_name] = device.to_dict()
        self.save_devices()

    def save_devices(self):
        with open("devices.json", 'w') as f:
            json.dump(self.devices, f, indent=4)
