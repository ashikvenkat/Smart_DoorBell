#############
# User Parameters
#############

# Doorbell pin
DOORBELL_PIN = 26
# Number of seconds to keep the call active
DOORBELL_SCREEN_ACTIVE_S = 60
# Enables email notifications
ENABLE_EMAIL = True
# Email you want to send the notification from (only works with Gmail)
FROM_EMAIL = 'sender@gmail.com'
# You can generate an app password here to avoid storing your password in plain text
# This should also come from an environment variable
# https://support.google.com/accounts/answer/185833?hl=en
FROM_EMAIL_PASSWORD = 'password'
# Email you want to send the update to
TO_EMAIL = 'receiver@gmail.com'

# Directory and filename parameters for image capture
dir = './visitors/'
prefix = 'photo'


#############
# Program
#############

import time
import os
import signal
import subprocess
import smtplib
import uuid

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

try:
    import RPi.GPIO as GPIO
    import picamera
except RuntimeError:
    print("Error importing RPi.GPIO or picamera. This is probably because you need superuser. Try running again with 'sudo'.")


def send_email_notification(image_filename):
    if ENABLE_EMAIL:
        sender = EmailSender(FROM_EMAIL, FROM_EMAIL_PASSWORD)
        email = Email(
            sender,
            'Doorbell Notification',
            'A visitor is waiting at your door',
            'A visitor is waiting at your door. Please check the attached photo.',
            image_filename
        )
        email.send(TO_EMAIL)


def ring_doorbell(pin):
    # Capture an image when the doorbell is pressed
    image_filename = capture_img()

    # Send email notification with the captured image
    send_email_notification(image_filename)


class EmailSender:
    def __init__(self, email, password):
        self.email = email
        self.password = password


class Email:
    def __init__(self, sender, subject, preamble, body, image_filename):
        self.sender = sender
        self.subject = subject
        self.preamble = preamble
        self.body = body
        self.image_filename = image_filename

    def send(self, to_email):
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = self.subject
        msgRoot['From'] = self.sender.email
        msgRoot['To'] = to_email
        msgRoot.preamble = self.preamble

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        msgText = MIMEText(self.body)
        msgAlternative.attach(msgText)

        # Attach the captured image
        with open(self.image_filename, 'rb') as image_file:
            msgImage = MIMEImage(image_file.read())
            msgRoot.attach(msgImage)

        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        smtp.login(self.sender.email, self.sender.password)
        smtp.sendmail(self.sender.email, to_email, msgRoot.as_string())
        smtp.quit()


class Doorbell:
    def __init__(self, doorbell_button_pin):
        self._doorbell_button_pin = doorbell_button_pin

    def run(self):
        try:
            print("Starting Doorbell...")
            self._setup_gpio()
            print("Waiting for doorbell rings...")
            self._wait_forever()

        except KeyboardInterrupt:
            print("Safely shutting down...")

        finally:
            self._cleanup()

    def _wait_forever(self):
        while True:
            time.sleep(0.1)

    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._doorbell_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self._doorbell_button_pin, GPIO.RISING, callback=ring_doorbell, bouncetime=2000)

    def _cleanup(self):
        GPIO.cleanup(self._doorbell_button_pin)


def capture_img():
    if not os.path.exists(dir):
        os.makedirs(dir)

    files = sorted(glob.glob(os.path.join(dir, prefix + '[0-9][0-9][0-9].jpg')))
    count = 0

    if len(files) > 0:
        count = int(files[-1][-7:-4]) + 1

    filename = os.path.join(dir, prefix + '%03d.jpg' % count)

    with picamera.PiCamera() as camera:
        camera.capture(filename)

    return filename


if __name__ == "__main__":
    doorbell = Doorbell(DOORBELL_PIN)
    doorbell.run()
