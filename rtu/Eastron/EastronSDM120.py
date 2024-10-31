from rtu.SerialReaderRS485 import SerialReaderRS485


class EastronSDM120:
    def __init__(self, device_address, port):
        self.device_address = device_address
        self.device_name = "Eastron-SDM120"
        self.port = port
        self.reader = SerialReaderRS485(device_name=self.device_name,
                                        port=self.port,
                                        device_address=self.device_address)

    def read_all_properties(self):
        """
        Read all parameters from Eastron-SDM120
        :return: Dictionary of parameter`s values (str, float)
        """
        return self.reader.read_all_properties()

    def read_one_property_register(self, parameter: str):
        """
        Read one parameter from Eastron-SDM120
        :param parameter: name of parameter
        :return: One parameter`s value (float)
        """
        return self.reader.read_property(parameter)
