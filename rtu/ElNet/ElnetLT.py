from rtu.SerialReaderRS485 import SerialReaderRS485


class ElnetLT:
    def __init__(self, device_address, port):
        self.device_address = device_address
        self.device_name = "ElnetLT"
        self.port = port
        self.reader = SerialReaderRS485(device_name=self.device_name,
                                        port=self.port,
                                        device_address=self.device_address)
