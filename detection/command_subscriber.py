
from json import dumps
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import winsound
import threading
import datetime
from threading import Thread

# Global variables for alarm customization
alarm_active = False
alarm_thread = None
duration = 1000  # milliseconds
freq = 440  # Hz

# MQTT Broker configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "home_security/commands"
STATUS_TOPIC = "home_security/status"

# MongoDB configuration
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["ObjectDetection"]
collection = db["DetectionLogs"]
archive_collection = db["ArchivedLogs"]

# Alarm sound thread
def alarm_loop():
    global alarm_active, freq, duration
    while alarm_active:
        winsound.Beep(freq, duration)

# Handle incoming MQTT commands
def on_message(client, userdata, msg):
    global alarm_active, alarm_thread, freq, duration

    command = msg.payload.decode()
    print(f"Received command: {command}")

    if command.startswith("set_alarm"):
        # Parse and set alarm frequency and duration
        try:
            params = dict(param.split('=') for param in command.split()[1:])
            freq = int(params.get("freq", freq))
            duration = int(params.get("duration", duration))
            print(f"Alarm settings updated: freq={freq}, duration={duration}")
        except Exception as e:
            print(f"Error parsing set_alarm command: {e}")

    elif command == "turn_on_alarm":
        alarm_active = True
        if not alarm_thread or not alarm_thread.is_alive():
            alarm_thread = threading.Thread(target=alarm_loop)
            alarm_thread.daemon = True
            alarm_thread.start()
        print("Alarm turned ON!")

    elif command == "turn_off_alarm":
        alarm_active = False
        if alarm_thread:
            alarm_thread.join()
        print("Alarm turned OFF!")

    elif command == "get_status":
        log_count = collection.count_documents({})
        status = {
            "alarm_active": alarm_active,
            "log_count": log_count,
        }
        print(f"System Status: {status}")
        # dispatch to STATUS_TOPIC 
        result = {
          "alarm_active": alarm_active,
          "frequency": freq,
          "duration": duration,
          "log_count": collection.count_documents({})
        }
        client.publish(STATUS_TOPIC, dumps(result))
        

    elif command.startswith("archive_logs"):
        # Archive logs before a specific date
        try:
            before_date = command.split()[1].split('=')[1]
            archive_date = datetime.datetime.strptime(before_date, "%Y-%m-%d")
            print(f"Archiving logs before {archive_date}")
            logs_to_archive = collection.find({"timestamp": {"$lt": archive_date}})
            # logs_to_archive number
            count = collection.count_documents({"timestamp": {"$lt": archive_date}})
            print(f"Archiving {count} logs")
            archive_collection.insert_many(logs_to_archive)
            collection.delete_many({"timestamp": {"$lt": archive_date}})
            print(f"Logs archived before {before_date}")
        except Exception as e:
            print(f"Error archiving logs: {e}")

    elif command.startswith("trigger_device"):
        # Trigger an external device
        try:
            params = dict(param.split('=') for param in command.split()[1:])
            device_name = params.get("name", "unknown")
            action = params.get("action", "unknown")
            print(f"Triggering device: {device_name} with action: {action}")
        except Exception as e:
            print(f"Error parsing trigger_device command: {e}")

    elif command == "reset_system":
        # Reset the system
        alarm_active = False
        if alarm_thread:
            alarm_thread.join()
        collection.delete_many({})
        print("System reset to default state.")

    else:
        print(f"Unknown command: {command}")


  # Initialize MQTT client and connect to broker

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, keepalive=60)

# Subscribe to the commands topic
client.subscribe(TOPIC)
print(f"Subscribed to topic: {TOPIC}")


if __name__ == '__main__':
  # mqtt_thread = Thread(target=lambda: client.loop_forever())
  # mqtt_thread.daemon = True
  # mqtt_thread.start()
  client.loop_forever()
