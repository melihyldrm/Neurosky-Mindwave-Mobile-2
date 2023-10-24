from neuroskyMindwaveMobile2 import MindWaveMobileThread
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse
import socket
from fastapi.middleware.cors import CORSMiddleware
import threading
import json

app = FastAPI()

bluetooth_status = True

udpStreamCount = 0

@app.get("/amiawake")
def awake():
    return {"message:" : "Device is open!"}

# Bluetooth'u açma işlemi
@app.get("/on")
def turn_on_bluetooth_device():
    global bluetooth_status
    if not bluetooth_status:
        bluetooth_status = True
    return {"message": "Bluetooth is on"}

# Bluetooth'u kapatma işlemi
@app.get("/off")
def turn_off_bluetooth_device():
    global bluetooth_status
    if bluetooth_status:
        bluetooth_status = False
    return {"message": "Bluetooth is off"}

# Çevredeki blueetooth cihazlarını tarama fonksiyonu
@app.get("/scan")
def scan_bluetooth_device():
    if not bluetooth_status:
        return {"message": "Bluetooth is off. You can't scan"}
    
    device = MindWaveMobileThread()
    scanned_devices = device.scan_devices()
    device_list = {"devices": [{"name": name, "MAC": address} for address, name in scanned_devices]}
    return device_list

connected_sockets = {}  # Sözlük, MAC adresini sokete bağlamak için kullanılacak0
devicesSockets =[]

# mac adresi belirtilen cihaza bağlanma fonksiyonu
@app.get("/connect")    
def connect_to_bluetooth_device(mac: str):
    global bluetooth_status, connected_sockets

    if len(connected_sockets) == 2:
        return {"message:" : "You've reached maximum devices"}

    myMindWave = MindWaveMobileThread()
    devicesSockets.append(myMindWave)

    if not bluetooth_status:
        return {"message": "Bluetooth is off. You can't connect"} 
    if mac in connected_sockets:
        return {"message": "You've already connected"}
    try:
        bluetooth_socket = myMindWave.bluteooth_connect(mac)
        if bluetooth_socket:
            connected_sockets[mac] = bluetooth_socket
            return {"message": "Connected address: " + mac}
        else:
            return {"message": "Failed to connect to device"}
    except:
        return {"message": "Connection error"}   

streamingFlag = True

# mac adresi belirtilen cihazla bağlantıyı kesme fonksiyonu
@app.get("/disconnect")
def disconnect_to_bluetooth_device(mac: str):
    global connected_sockets, streamingFlag, devicesSockets
    if not bluetooth_status:
        return {"message": "Bluetooth is off. You can't disconnect"}
    if mac not in connected_sockets:
        return {"message": "You're not already connected to the device"}
    try:        
        for device in devicesSockets:
            device.stop()
            remove_device_socket(device)
            connected_sockets.clear()
        return {"message": "Device has ended: " + mac}              
    except:
        return {"message": "Failed disconnection"}
    
def remove_device_socket(socket_thread):
    global devicesSockets
    devicesSockets = []

# bağlanılan cihazdan gelen verileri yazdıran fonksiyon
UDP_IP = "127.0.0.1"
UDP_PORT = 8082

@app.get("/stream")
def udp_server_task():
    global udpStreamCount, streamingFlag
    udpStreamCount = udpStreamCount + 1
    if udpStreamCount > 1:
        return {"message": "Data flow has already started"}
    
    server_thread = threading.Thread(target=start_streaming_data)
    server_thread.start()
    return {"message": "Data flow started"}
 

def start_streaming_data():
    global streamingFlag, udpStreamCount
    address = (UDP_IP, UDP_PORT)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def dev1DataRecvCallback(attention, meditation, signalQuality):

        signalQuality = 200 - signalQuality

        if signalQuality == 200:
            attentionByte = int(attention).to_bytes(1, "big")
            meditationByte = int(meditation).to_bytes(1, "big")
            signalQualityByte = int(signalQuality).to_bytes(1, "big")
            x = 1
            y = x.to_bytes(1, "big")
            data1 = y+attentionByte+meditationByte+signalQualityByte
            server_socket.sendto(data1, address)
        else:
            attentionByte = int(0).to_bytes(1, "big")
            meditationByte =  int(0).to_bytes(1, "big")
            signalQualityByte = int(signalQuality).to_bytes(1, "big")
            x = 1
            y = x.to_bytes(1, "big")
            data1 = y+attentionByte+meditationByte+signalQualityByte
            server_socket.sendto(data1, address)
        pass
        

    def dev2DataRecvCallback(attention, meditation, signalQuality): 

        signalQuality = 200 - signalQuality

        if signalQuality == 200:
            attentionByte = int(attention).to_bytes(1, "big")
            meditationByte = int(meditation).to_bytes(1, "big")
            signalQualityByte = int(signalQuality).to_bytes(1, "big")
            x = 2
            y = x.to_bytes(1, "big")
            data2 = y+attentionByte+meditationByte+signalQualityByte
            server_socket.sendto(data2, address)
        else:
            attentionByte = int(0).to_bytes(1, "big")
            meditationByte =  int(0).to_bytes(1, "big")
            signalQualityByte = int(signalQuality).to_bytes(1, "big")
            x = 2
            y = x.to_bytes(1, "big")
            data2 = y+attentionByte+meditationByte+signalQualityByte
            server_socket.sendto(data2, address)
        pass

    while streamingFlag:
        try:
            if len(devicesSockets) < 1:
                print("no connection")
                break

            elif len(devicesSockets) == 1:
                print("Retrieving data from only one device")
                mindwave1 = devicesSockets[0]
                mindwave1.setDaemon(True)
                mindwave1.setDataReceiveCallback(dev1DataRecvCallback)
                mindwave1.start()
                return

            elif len(devicesSockets) == 2:
                print("Retrieving data from two device")
                mindwave1 = devicesSockets[0]
                mindwave2 = devicesSockets[1]
                mindwave1.setDaemon(True)
                mindwave2.setDaemon(True)
                mindwave1.setDataReceiveCallback(dev1DataRecvCallback)
                mindwave2.setDataReceiveCallback(dev2DataRecvCallback)
                mindwave1.start()
                mindwave2.start()
                return
            else:
                print("Unexpected error")
        except:
            print("Data flow error")
    

    return {"message:" : "Data flow has started"}  

@app.get("/stream_stop")
def streamStop():
    global streaming_flag, connected_sockets, devicesSockets
    streaming_flag = False
    for device in devicesSockets:
        device.stop()
        connected_sockets.clear()
        devicesSockets = []
    return {"mesaj:" : "Data flow stopped. Device connection has ended"} 

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8080)


