import time
from datetime import datetime
from logging import error

from DeviceManager import DeviceManager


if __name__ == "__main__":
    device_manager = DeviceManager()

    while True:
        try:
            print(device_manager.fetch_devices())

            #report_path = device_manager.get_device_by_custom_name("NEMO").read_all_properties()
            #print(f"Report has been saved in: {report_path}")
            #print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} \n\n")
            #df = pd.read_csv(report_path)
            #print(df)
            #print("\n-----\n")
        except KeyboardInterrupt:
            print("Program interrupted")
            break
        except Exception as e:
            error(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | {e}")

        time.sleep(60)
