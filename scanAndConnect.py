import bluetooth
import time

from bluetooth.btcommon import BluetoothError


class BluetoothDevice():   

    def __init__(self) -> None:
        self.sock = None
        self.bluetooth_status = False
        

    def scan_bluetooth(self):
        nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=5)
        return nearby_devices


    def connects(self, mac_address):
        for i in range(10):
            if i > 0:
                time.sleep(1)
            if not self.sock:
                self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
            try:
                self.sock.connect((mac_address, 1))
                # self.sock.setblocking(False)
                return self.sock
            except BluetoothError:
                print("ERROR!")
                return False
        return None
