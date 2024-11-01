import csv
import json
import os
from datetime import datetime
from logging import error

from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


def decode_data(data, property_specifications):
    decoded_data = 0
    if property_specifications["format"] == "float":
        decoded_data = decode_32bit_float(data)

    return decoded_data


def decode_32bit_float(data):
    decoded_data = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.BIG,
                                                      wordorder=Endian.BIG).decode_32bit_float()
    return decoded_data


class SerialReaderRS485:
    def __init__(self,
                 device_custom_name,
                 device_name,
                 port,
                 device_address,
                 baudrate,
                 bytesize,
                 parity,
                 stopbits):
        self.device_custom_name = device_custom_name
        self.device_address = device_address

        json_path = os.path.join(os.path.dirname(__file__), '..', 'register_maps', f'{device_name}.json')

        with open(json_path, 'r') as f:
            property_specifications_list = json.load(f)
        self.property_specifications_list = property_specifications_list

        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate[0],
            parity=parity[0],
            stopbits=stopbits,
            bytesize=bytesize[0],
        )

    def connect(self):
        return self.client.connect()

    def read_property(self, property_name: str):
        """
        Read register value from serial device
        :param property_name: name from device.json
        :return: Value from register(s)
        """
        if self.connect():
            property_specifications = self.property_specifications_list[property_name]
            property_address = property_specifications['register']

            response = {}
            try:
                if property_specifications["type"] == "holding":
                    response = self.client.read_holding_registers(property_address, count=4,
                                                                  slave=self.device_address)
                if property_specifications["type"] == "input":
                    response = self.client.read_input_registers(property_address, count=4,
                                                                slave=self.device_address)
                if response.isError():
                    error(
                        f"{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | There is no response | {property_specifications}")
                    return None

                return decode_data(data=response.registers, property_specifications=property_specifications)

            except Exception as e:
                error(f"{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | {e}")

            finally:
                self.client.close()

        else:
            error("Device not connected")

    def read_all_properties(self):
        results = {"device_id": self.device_custom_name}

        for property_name in self.property_specifications_list.keys():
            value = self.read_property(property_name)

            results[property_name] = {
                "value": value,
                "units": self.property_specifications_list[property_name]["units"]
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.device_custom_name}_{timestamp}.csv"
        filepath = os.path.join(os.path.dirname(__file__), '..', 'reports', filename)

        with open(filepath, mode='w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(["Parameter", "Value", "Units"])
            for prop, data in results.items():
                if isinstance(data, dict) and "value" in data and "units" in data:
                    writer.writerow([prop, data["value"], data["units"]])
                else:
                    writer.writerow([prop, data, ""])

        return filepath
