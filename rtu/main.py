
import time
from datetime import datetime
from logging import error

from rtu.Eastron.EastronSDM120 import EastronSDM120

if __name__ == "__main__":
    client1 = EastronSDM120(1, "COM1")
    #client2 = EastronSDM120(2, "COM1")

    while True:
        try:
            print(client1.read_all_properties())
            #print(client2.read_all_properties())
            print("-----")
        except KeyboardInterrupt:
            print("Program stopped...")
            break
        except Exception as e:
            error(f"{datetime.now().strftime("%d/%m/%Y %H:%M:%S")} | {e}")

        time.sleep(5)

