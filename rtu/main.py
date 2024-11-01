import time
from datetime import datetime
from logging import error

from rtu.DeviceManager import DeviceManager
import pandas as pd

if __name__ == "__main__":
    device_manager = DeviceManager()

    while True:
        try:
            report_path = device_manager.get_device_by_custom_name("Test 2 Device").read_all_properties()
            print(f"Report has been saved in: {report_path}")

            df = pd.read_csv(report_path)
            print(df)
            print("-----")
        except KeyboardInterrupt:
            print("Program interrupted")
            break
        except Exception as e:
            error(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | {e}")

        time.sleep(60)
