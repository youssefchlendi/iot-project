from ultralytics import YOLO
import cv2
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Broker configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "object_detection/results"

# Initialize MQTT client
client = mqtt.Client()
client.connect(BROKER, PORT, keepalive=60)

# Load a pre-trained YOLOv8 model
model = YOLO("yolov8n.pt")

# Initialize the webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not access the webcam.")
    exit()

print("Press 'q' to quit.")

while True:
    # Read a frame from the webcam
    ret, frame = camera.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Perform object detection
    results = model.predict(source=frame, conf=0.5, show=False)
    annotated_frame = results[0].plot()

    # Extract detection results
    for box in results[0].boxes:
        # Get object class and confidence score
        obj_class = model.names[int(box.cls[0])]  # Map class index to label
        confidence = box.conf[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare and send MQTT message
        message = f"Object: {obj_class}, Confidence: {confidence:.2f}, Timestamp: {timestamp}"
        client.publish(TOPIC, message)
        print(f"Published: {message}")

    # Display the annotated frame
    cv2.imshow("YOLO with MQTT", annotated_frame)

    # Break loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close all OpenCV windows
camera.release()
cv2.destroyAllWindows()
client.disconnect()
