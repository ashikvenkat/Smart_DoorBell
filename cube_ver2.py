import socket
import threading
import time
import RPi.GPIO as GPIO
import time
import Adafruit_DHT as dht

header = 64
format = 'utf-8'
discon_msg = "!DISCONNECTED"
ip = "192.168.1.9"
port = 5050
addr = (ip,port)
s= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(addr)

SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8
smokesensor_dpin = 26
smokesensor_apin = 0
#port initalization for the MQ-5 sensor
def init():
	GPIO.setwarnings(False)
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(SPIMOSI, GPIO.OUT)
	GPIO.setup(SPIMISO, GPIO.IN)
	GPIO.setup(SPICLK, GPIO.OUT)
	GPIO.setup(SPICS, GPIO.OUT)
	GPIO.setup(smokesensor_dpin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	GPIO.output(cspin, True)
	GPIO.output(clockpin, False)
	GPIO.output(cspin, False)
	commandout = adcnum
	commandout |= 0x18
	commandout <<= 3
	for i in range(5):
		if (commandout & 0x80):
			GPIO.output(mosipin, True)
		else:
			GPIO.output(mosipin, False)
			commandout <<= 1
			GPIO.output(clockpin, True)
			GPIO.output(clockpin, False)
	adcout = 0
	for i in range(12):
		GPIO.output(clockpin, True)
		GPIO.output(clockpin, False)
		adcout <<= 1
		if (GPIO.input(misopin)):
			adcout |= 0x1
	GPIO.output(cspin, True)
	adcout >>= 1 
	return adcout

def gas_main():
	 init()
	 while True:
		 smokelevel=readadc(smokesensor_apin, SPICLK, SPIMOSI, SPIMISO, SPICS)
		 if GPIO.input(smokesensor_dpin):
			 print("No Gas Leakage detected")
		 else:
			 print("Gas leakage detected ALERT!")
			 print("Current Gas AD vaule = {:.2f} V".format((smokelevel/1024.)*5))
		 time.sleep(5)
		   
		   
def read_Temp():
	while True:
		h,t = dht.read_retry(dht.DHT22, 4)
		if h is not None and t is not None:
			print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(t, h))
		else:
			print("Error taking the Temperature and Humidity readings. Please Check the connections")
		time.sleep(5)

	
def handle_client(conn,addr):
    print(f"new connection {addr} connected..")
    connected = True
    while connected:
        msg_len= conn.recv(header).decode(format).strip()
        if msg_len:
            msg_len = int(msg_len)
            msg = conn.recv(msg_len).decode(format).strip()
            if msg == discon_msg:
                connected = False
            print(f"[{addr}] {msg}")
            conn.send("Message Recieved!".encode(format))

    conn.close()

def start():
    s.listen()
    print(f"Listening server on {ip}")
    while True:
        conn,addr = s.accept()
        thread = threading.Thread(target=handle_client,args=(conn,addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count()}")


def main():
    try:
        print("Starting server...")
        global gas_running, temp_running
        gas_running = True
        temp_running = True
        
        thread_gas = threading.Thread(target=gas_main)
        thread_temp = threading.Thread(target=read_Temp)
        thread_gas.start()
        thread_temp.start()
        start()
    except KeyboardInterrupt:
        gas_running = False
        temp_running = False
        thread_gas.join()
        thread_temp.join()
        print("Shutting down.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
