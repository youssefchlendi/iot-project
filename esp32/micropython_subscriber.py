import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient
from time import sleep
from json import dumps

# Global Constants
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = b"home_security/commands"
STATUS_TOPIC = b"home_security/status"
BUZZER_PIN = 14
FIRST_RED_PIN = 23
FIRST_BLUE_PIN = 22
SECOND_RED_PIN = 21
SECOND_BLUE_PIN = 19
DEFAULT_DURATION = 1000  # Default alarm duration in milliseconds
DEFAULT_FREQ = 440       # Default alarm frequency in Hz
DEFAULT_FLASH_FREQ = 1   # Default flash frequency in seconds
DEFAULT_FLASH_DURATION = 1  # Default flash duration in seconds
SET_FLASH_COMMAND = "set_flash"
SET_ALARM_COMMAND = "set_alarm"
TURN_ON_ALARM_COMMAND = "turn_on_alarm"
TURN_OFF_ALARM_COMMAND = "turn_off_alarm"
TURN_ON_FLASH_COMMAND = "turn_on_flash"
TURN_OFF_FLASH_COMMAND = "turn_off_flash"
GET_STATUS_COMMAND = "get_status"
RESET_SYSTEM_COMMAND = "reset_system"

buzzer = Pin(BUZZER_PIN, Pin.OUT)
firstRed = Pin(FIRST_RED_PIN, Pin.OUT)
firstBlue = Pin(FIRST_BLUE_PIN, Pin.OUT)
secondRed = Pin(SECOND_RED_PIN, Pin.OUT)
secondBlue = Pin(SECOND_BLUE_PIN, Pin.OUT)

buzzer.value(0)
firstRed.value(0)
firstBlue.value(0)
secondRed.value(0)
secondBlue.value(0)


# Global variables for alarm customization
alarm_active = False
flash_active = False
duration = 1000
freq = 440
flash_freq = 1
flash_duration = 1

# MQTT Broker configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = b"home_security/commands"
STATUS_TOPIC = b"home_security/status"

# Variables for non-blocking alarm
last_buzz_time = 0
buzzer_state = False  # False: OFF, True: ON

def flashLEDs():
    global flash_active, flash_freq, flash_duration
    if flash_active:
        firstRed.value(1)
        firstBlue.value(0)
        secondRed.value(1)
        secondBlue.value(0)
        sleep(flash_freq)
        firstRed.value(0)
        firstBlue.value(1)
        secondRed.value(0)
        secondBlue.value(1)
        sleep(flash_freq)
    else:
        firstRed.value(0)
        firstBlue.value(0)
        secondRed.value(0)
        secondBlue.value(0)

# Function to handle buzzing
def buzz(current_time):
    global buzzer_state, last_buzz_time
    if buzzer_state:
        # Turn off the buzzer
        buzzer.value(0)
        buzzer_state = False
        # Set the next buzz time based on frequency
        # Period = 1/frequency (seconds)
        period = 1 / freq
        last_buzz_time = current_time + period
    else:
        # Turn on the buzzer
        buzzer.value(1)
        buzzer_state = True
        # Duration to keep the buzzer on
        on_duration = duration / 1000  # Convert ms to seconds
        last_buzz_time = current_time + on_duration

# Handle incoming MQTT commands
def on_message(topic, msg):
    global alarm_active, freq, duration, flash_active, flash_freq, flash_duration
    command = msg.decode()
    print(f"Received command: {command}")

    if command.startswith(SET_ALARM_COMMAND):
        try:
            # Example command: set_alarm freq=500 duration=500
            params = dict(param.split('=') for param in command.split()[1:])
            freq = int(params.get("freq", freq))
            duration = int(params.get("duration", duration))
            print(f"Alarm settings updated: freq={freq}, duration={duration}")
        except Exception as e:
            print(f"Error parsing set_alarm command: {e}")

    elif command.startswith(SET_FLASH_COMMAND):
        try:
            # Example command: set_flash freq=500 duration=500
            params = dict(param.split('=') for param in command.split()[1:])
            flash_freq = int(params.get("freq", flash_freq))
            flash_duration = int(params.get("duration", flash_duration))
            print(f"Flash settings updated: freq={flash_freq}, duration={flash_duration}")
        except Exception as e:
            print(f"Error parsing set_flash command: {e}")
            
    elif command == TURN_ON_ALARM_COMMAND:
        alarm_active = True
        print("Alarm turned ON!")
    
    elif command == TURN_ON_FLASH_COMMAND:
        flash_active = True
        print("Flash turned ON!")

    elif command == TURN_OFF_ALARM_COMMAND:
        alarm_active = False
        # Ensure buzzer is turned off when alarm is deactivated
        buzzer.value(0)
        print("Alarm turned OFF!")
        
    elif command == TURN_OFF_FLASH_COMMAND:
        flash_active = False
        print("Flash turned OFF!")

    elif command == GET_STATUS_COMMAND:
        status = {
            "alarm_active": alarm_active,
            "frequency": freq,
            "duration": duration,
            "flash_active": flash_active,
            "flash_freq": flash_freq,
            "flash_duration": flash_duration
        }
        print(f"System Status: {status}")
        client.publish(STATUS_TOPIC, dumps(status))

    elif command == RESET_SYSTEM_COMMAND:
        alarm_active = False
        # Ensure buzzer is turned off when system is reset
        buzzer.value(0)
        print("System reset to default state.")

    else:
        print(f"Unknown command: {command}")

# Connect to wifi
print("Connecting to WiFi", end="")
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('Wokwi-GUEST', '')
while not sta_if.isconnected():
  print(".", end="")
  time.sleep(0.1)
print(" Connected!")


# Initialize MQTT client and connect to broker
client = MQTTClient("pico_client", BROKER, port=PORT)
client.set_callback(on_message)
client.connect()

# Subscribe to the commands topic
client.subscribe(TOPIC)
print(f"Subscribed to topic: {TOPIC}")

# Main loop
if __name__ == '__main__':
    while True:
        client.check_msg()  # Check for new MQTT messages

        if alarm_active:
            current_time = time.time()
            # Check if it's time to toggle the buzzer
            if current_time >= last_buzz_time:
                buzz(current_time)
        else:
            # Ensure buzzer is off if alarm is not active
            if buzzer.value() != 0:
                buzzer.value(0)
                
        if flash_active:
            flashLEDs()
        else:
            firstRed.value(0)
            firstBlue.value(0)
            secondRed.value(0)
            secondBlue.value(0)

        sleep(0.1)  # Small delay to prevent excessive CPU usage
