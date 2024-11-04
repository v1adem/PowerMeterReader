from rtu.Device import Device
from rtu.SerialReaderRS485 import SerialReaderRS485


class Elnet(Device):
    def __init__(self, custom_name, device_address, port):
        super().__init__(custom_name, device_address, "Elnet", port, 9600, 8, "N", 1)
        self.reader = SerialReaderRS485(device_custom_name=custom_name,
                                        device_name=self.device_name,
                                        port=self.port,
                                        device_address=self.device_address,
                                        baudrate=self.baudrate,
                                        bytesize=self.bytesize,
                                        parity=self.parity,
                                        stopbits=self.stopbits)

    def read_all_properties(self):
        """
        Read all parameters from Elnet devices
        :return: Dictionary of parameter`s values (str, float)
        """
        return self.reader.read_all_properties()

    def read_one_property_register(self, parameter: str):
        """
        Read one parameter from Elnet devices
        :param parameter: name of parameter
        :return: One parameter`s value (float)
        """
        return self.reader.read_property(parameter)
