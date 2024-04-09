import socket
import cv2
import threading
import time
import RPi.GPIO as GPIO
import time
import Adafruit_DHT as dht
import mpu6050
import time
import numpy as np
import urllib.request
from flask import Flask, jsonify, send_from_directory
import openpyxl
from openpyxl import Workbook


mpu6050 = mpu6050.mpu6050(0x68)


app = Flask(__name__)

#ESP32 Connector
url = "http://192.168.205.30/cam-hi.jpg"
face_cascade = cv2.CascadeClassifier('/home/cube/Desktop/Final/haarcascade_profileface.xml')

# Global variables
num_faces_detected = 0
accelerometer_data = {}
gyroscope_data = {}
temperature = None
humidity = None



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
		

def read_sensor_data():
    accelerometer_data = mpu6050.get_accel_data()
    gyroscope_data = mpu6050.get_gyro_data()
    temperature = mpu6050.get_temp()

    return accelerometer_data, gyroscope_data, temperature
    
def gio_main():
	init()
	while True:
		accelerometer_data, gyroscope_data, temperature = read_sensor_data()
		print("Accelerometer data: ", accelerometer_data)
		print("Gyroscope data: ", gyroscope_data)
		time.sleep(10)
	
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
		

#Number of Faces Detection
def detect_faces(frame):
    if frame is None:
        print("Error: Failed to capture frame from stream.")
        return 0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces)

def capture_frames():
    global num_faces_detected
    while True:
        try:
            stream = urllib.request.urlopen(url)

            while True:
                frame_buffer = stream.read()
                if not frame_buffer:
                    break 
                frame = cv2.imdecode(np.frombuffer(frame_buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                num_faces = detect_faces(frame)
                num_faces_detected = num_faces
                time.sleep(0.5)

        except Exception as e:
            print("Error:", e)

        finally:
            stream.close()
#HTML Connect

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/data')
def get_data():
    global num_faces_detected
    return jsonify({'faces_detected': num_faces_detected})



@app.route('/sensor-readings')
def get_sensor_readings():
    global accelerometer_data, gyroscope_data, temperature, humidity
    
    # Sample data for demonstration
    accelerometer_data = {'x': 1.23, 'y': 2.34, 'z': 3.45}
    gyroscope_data = {'x': 0.12, 'y': 0.23, 'z': 0.34}
    temperature = 25.5
    humidity = 50.0
    
    # Construct JSON response with sensor readings
    sensor_readings = {
        'accelerometer': accelerometer_data,
        'gyroscope': gyroscope_data,
        'temperature': temperature,
        'humidity': humidity
    }
    
    # Return JSON response
    return jsonify(sensor_readings)

def main():
    try:
        print("Starting server...")
        global gas_running, temp_running
        capture_thread = threading.Thread(target=capture_frames)
        capture_thread.start()
        app.run(host='0.0.0.0',port=5000,debug=True)
        start()
    except KeyboardInterrupt:
        print("Shutting down.")

		
if __name__=="__main__":
	main()
	

