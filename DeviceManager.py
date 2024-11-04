import json

from rtu.Eastron.EastronSDM120 import EastronSDM120
from rtu.ElNet.Elnet import Elnet
from rtu.IME.NEMO96HDLe import NEMO96HDLe


class DeviceManager:
    _instance = None  # Class variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            cls._instance = super(DeviceManager, cls).__new__(cls)  # Create a new instance
        return cls._instance  # Return the existing instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.devices_parameters = {}
            self.devices = {}
            self.fetch_devices()
            self.initialized = True  # Mark the instance as initialized

    def fetch_devices(self):
        try:
            with open("rtu/devices.json", 'r') as f:
                self.devices_parameters = json.load(f)
            for device in self.devices_parameters.values():
                if device["device_name"] == "Eastron-SDM120":
                    self.devices[device["custom_name"]] = EastronSDM120(device["custom_name"],
                                                                        device["device_address"],
                                                                        device["port"])
                elif device["device_name"] == "ElNet-PQ":
                    self.devices[device["custom_name"]] = Elnet(device["custom_name"],
                                                                device["device_address"],
                                                                device["port"])
                elif device["device_name"] == "NEMO96HDLe":
                    self.devices[device["custom_name"]] = NEMO96HDLe(device["custom_name"],
                                                                     device["device_address"],
                                                                     device["port"])
        except FileNotFoundError:
            self.devices = {}
        return self.devices

    def get_device_by_custom_name(self, custom_name):
        return self.devices.get(custom_name)

    def add_device(self, device):
        device_id = str(len(self.devices_parameters) + 1)
        self.devices_parameters[device_id] = device.to_dict()

        with open("rtu/devices.json", 'w') as f:
            json.dump(self.devices_parameters, f, indent=4)

        self.fetch_devices()
