import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime

# MQTT Broker configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "home_security/alerts"
COMMAND_TOPIC = "home_security/commands"

# MongoDB configuration
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["ObjectDetection"]
collection = db["DetectionLogs"]

active = True

# Callback for when a message is received
def on_message(client, userdata, msg):
    global active
    if msg.topic == COMMAND_TOPIC:
        print(f"Received command: {msg.payload.decode()}")
        if msg.payload.decode() == "stop":
            active = False
        elif msg.payload.decode() == "start":
            active = True
        return
    else:
      message = msg.payload.decode()
      if not active:
          print("Subscriber is inactive.")
          return
      print(f"Received message: {message}")

      # Parse the message (Object: obj_class, Confidence: confidence, Timestamp: timestamp)
      try:
          parts = message.split(", ")
          obj = parts[0].split(": ")[1]
          confidence = float(parts[1].split(": ")[1])
          timestamp = datetime.strptime(parts[3].split(": ")[1], "%Y-%m-%d %H:%M:%S")

          # Insert into MongoDB
          detection_entry = {
              "object": obj,
              "confidence": confidence,
              "timestamp": timestamp
          }
          collection.insert_one(detection_entry)
          print("Data inserted into MongoDB.")
      except Exception as e:
          print(f"Error processing message: {e}")

# Initialize MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect to broker and subscribe to the topic
client.connect(BROKER, PORT, keepalive=60)
client.subscribe(TOPIC)
client.subscribe(COMMAND_TOPIC)

print(f"Subscribed to topic: {TOPIC}")
client.loop_forever()
