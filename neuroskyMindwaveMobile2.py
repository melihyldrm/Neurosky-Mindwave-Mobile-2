import threading
import bluetooth
import numpy as np
import time
from bluetooth.btcommon import BluetoothError
from raspicontrol import BluetoothDevice

class MindWaveMobileThread(threading.Thread):
     
    def __init__(self):
        super().__init__()
        self.bt_device = BluetoothDevice()
        self.recv_status = True

        self._attention = 0
        self._meditation = 0
        self._signalQuality = 0
        self._bytedata = 0
        self.dataRecvCallbackFunc = None
        self.devMACAdress = None
        self.sock = None
        self.running_flag = True

    # def set_device_mac_adress(self, pAdr):
    #     self.dev1MACAdress = pAdr

    def scan_devices(self):
        scanned_devices = self.bt_device.scan_bluetooth()
        return scanned_devices
    
    def bluteooth_connect(self, mac_address):
        self.sock = self.bt_device.connects(mac_address)
        self.devMACAdress = mac_address        
        return self.sock

    def read_mindwave_data(self):
        try:
            while self.recv_status:
                data = self.sock.recv(1024)
                if not data:
                    continue
                byte_data = np.frombuffer(data, dtype=np.uint8)
                aa_index = np.where(byte_data == 0xAA)[0]  #searches for data starting with 0xAA in the incoming data packet
                i = 0
                while i < len(aa_index) - 1:
                    if aa_index[i + 1] - aa_index[i] == 1: #The starting and ending indexes of two consecutive 0xAA bytes are determined. It is checked that the difference between position aa_index[i] and the next position (aa_index[i + 1]) is 1. This indicates that there are consecutive 0xAA bytes. The starting index is assigned to the variable aa_start and the ending index is assigned to the variable aa_end.
                        aa_start = aa_index[i]
                        aa_end = aa_start + 2
                        
                        while i < len(aa_index) - 1 and aa_index[i + 1] - aa_index[i] == 1: #This nested loop finds all consecutive 0xAA bytes. In the nested loop, if the difference between the next position and the current position is still 1, it updates the index aa_end and increments the counter i. This continues navigating the loop to find all consecutive bytes.
                            aa_end = aa_index[i + 1] + 1
                            i += 1
                        
                        if aa_end < len(byte_data) and byte_data[aa_start + 2] != 0x04:
                            aa_sequence = byte_data[aa_start:aa_end]
                        
                    i += 1 #At the end of the loop, the i counter value is incremented and the loop moves to the next step to check the next aa_index position.
                
                if len(aa_index) == 0:
                    continue    
                
                aa_start = aa_index[0]  # determines the position of the first 0xAA byte
                if byte_data[aa_start + 2] != 0x04:
                    length = byte_data[aa_start + 2] 
                    if length == 0x20:
                        if byte_data[aa_start + 3] == 0x02:
                            sq = byte_data[aa_start + 4]
                            self._signalQuality = sq
                            
                        if byte_data[aa_start + 5] == 0x83:
                            eegpower = byte_data[aa_start + 5]
                            attention_level = byte_data[aa_start + 32]
                            meditation_level = byte_data[aa_start + 34]
                            self._attention = attention_level
                            self._meditation = meditation_level
                            self._bytedata = byte_data
                            
                        if self.dataRecvCallbackFunc is not None:
                            self.dataRecvCallbackFunc(self._attention, self._meditation, self._signalQuality)      
            time.sleep(0.01)
        except:
            print("Connection lost, data flow interrupted")
    
    def setDataReceiveCallback(self, pFunc):
        self.dataRecvCallbackFunc = pFunc

    def getAttention(self):
        return self._attention
    
    def getMeditation(self):
        return self._meditation
    
    def getSignalQuality(self):
        return self._signalQuality
    
    def stop(self):
        # self.stop_event.set()
        # self.running_flag = False
        self.recv_status = False
        self.join()
        if self.sock:
            self.sock.close()
            
    def run(self):
        try:
            self.read_mindwave_data()
            self.setDaemon(True)
            # Close the Bluetooth connection when reading is finished
            self.stop()
        except:
            print("data flow has ended")
