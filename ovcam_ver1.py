import cv2
import numpy as np
import urllib.request
import time

# Stream URL for ESP32 camera
url = "http://192.168.1.19/cam-hi.jpg"

# Load cascade classifier for face detection
face_cascade = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')

def detect_faces(frame):
    if frame is None:
        print("Error: Failed to capture frame from stream.")
        return 0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces)

def main():
    while True:
        try:
            # Open the stream
            stream = urllib.request.urlopen(url)

            while True:
                frame_buffer = stream.read()  # Read a frame
                if not frame_buffer:
                    break  # End of stream

                frame = cv2.imdecode(np.frombuffer(frame_buffer, dtype=np.uint8), cv2.IMREAD_COLOR)
                num_faces = detect_faces(frame)
                print("Number of faces detected:", num_faces)

                # Delay for a short interval (adjust as needed)
                time.sleep(0.5)

        except Exception as e:
            print("Error:", e)

        finally:
            # Close the stream
            stream.close()

if __name__ == "__main__":
    main()
