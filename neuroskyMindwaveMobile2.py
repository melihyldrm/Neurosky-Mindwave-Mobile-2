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
                aa_index = np.where(byte_data == 0xAA)[0]  # gelen veri pakedi içinde 0xAA ile başlayan verileri arar
                i = 0
                while i < len(aa_index) - 1:
                    if aa_index[i + 1] - aa_index[i] == 1: #rdışık iki 0xAA baytının başlangıç ve bitiş indeksleri belirlenir. aa_index[i] konumu ile bir sonraki konum (aa_index[i + 1]) arasındaki farkın 1 olduğu kontrol edilir. Bu, ardışık 0xAA baytlarının olduğunu gösterir. Başlangıç indeksi aa_start değişkenine atanır ve bitiş indeksi aa_end değişkenine atanır.
                        aa_start = aa_index[i]
                        aa_end = aa_start + 2
                        
                        while i < len(aa_index) - 1 and aa_index[i + 1] - aa_index[i] == 1: #Bu iç içe geçmiş döngü, ardışık 0xAA baytlarının tamamını bulur. İç içe geçmiş döngüde, eğer bir sonraki konum ile mevcut konum arasındaki fark hala 1 ise, aa_end indeksini günceller ve i sayaçını artırır. Bu, ardışık baytların tamamını bulmak için döngüyü gezinmeye devam eder.
                            aa_end = aa_index[i + 1] + 1
                            i += 1
                        
                        if aa_end < len(byte_data) and byte_data[aa_start + 2] != 0x04:
                            aa_sequence = byte_data[aa_start:aa_end]
                        
                    i += 1 #Döngünün sonunda, i sayaç değeri artırılır ve bir sonraki aa_index konumunu kontrol etmek için döngü bir sonraki adıma geçer.
                
                if len(aa_index) == 0:
                    continue    
                
                aa_start = aa_index[0]  # ilk 0xAA byte'nın konumunu belirler
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
            print("Bağlantı koptu veri akışı kesildi")
    
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
            print("veri akışı kesildi")
