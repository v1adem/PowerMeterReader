from rtu.SerialReaderRS485 import SerialReaderRS485

baudrate = 9600

reader = SerialReaderRS485("SDM120 test", "SDM120", 6, 2, baudrate, 8, "N", 1)

print(reader.read_all_properties(["voltage", "current", "active_power", "apparent_power", "reactive_power", "power_factor"]))