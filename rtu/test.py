from pymodbus.client import ModbusTcpClient


class EastronESP1200Reader:
    def __init__(self, ip_address, port=502):
        self.client = ModbusTcpClient(ip_address, port)
        self.client.connect()

    def read_data(self, unit_id, start_register, count):
        # Читання даних з реєстру
        result = self.client.read_holding_registers(start_register, count, 1)
        if result.isError():
            print("Error reading data")
            return None
        else:
            return result.registers

    def close_connection(self):
        self.client.close()

# Приклад використання:
reader = EastronESP1200Reader('192.168.1.100')  # IP-адреса ESP-1200
data = reader.read_data(unit_id=1, start_register=0, count=10)

if data:
    print("Read data:", data)

reader.close_connection()