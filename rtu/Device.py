from abc import ABC, abstractmethod


class Device(ABC):
    def __init__(self, custom_name, device_address, device_name, port, baudrate: int, bytesize: int, parity, stopbits: int):
        self.custom_name = custom_name
        self.device_address = device_address
        self.device_name = device_name
        self.port = port
        self.baudrate = baudrate,
        self.bytesize = bytesize,
        self.parity = parity,
        self.stopbits = stopbits

    @abstractmethod
    def read_all_properties(self):
        """Read all device properties"""
        pass

    @abstractmethod
    def read_one_property_register(self, parameter: str):
        """Read one property register"""
        pass

    def to_dict(self):
        """Return device properties as a dictionary"""
        return {
            "custom_name": self.custom_name,
            "device_address": self.device_address,
            "device_name": self.device_name,
            "port": self.port,
        }
