from ultralytics import YOLO
import cv2
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Broker configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "home_security/alerts"

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.connect(BROKER, PORT, keepalive=60)

# Load the pre-trained YOLOv8 model
model = YOLO("yolov8n.pt")

# Open the webcam (default ID 0)
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not access the webcam.")
    exit()

print("Press 'q' to quit.")

while True:
    # Capture a frame from the webcam
    ret, frame = camera.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # Perform inference
    results = model.predict(source=frame, conf=0.5, show=False)

    # Process all detections
    for box in results[0].boxes:
        obj_class = int(box.cls[0])  # Get the object class index
        label = model.names[obj_class]  # Get the label (e.g., 'person', 'car')
        confidence = box.conf[0]
        bbox = box.xyxy[0]  # Bounding box: [x_min, y_min, x_max, y_max]

        # Calculate bounding box size (area)
        bbox_width = bbox[2] - bbox[0]
        bbox_height = bbox[3] - bbox[1]
        bbox_area = bbox_width * bbox_height

        # Trigger alert based on bounding box size and confidence
        if confidence > 0.5 and bbox_area > 5000:  # Adjust threshold as needed
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Prepare MQTT message
            message = (
                f"Alert! Detected: {label}, Confidence: {confidence:.2f}, "
                f"Size: {bbox_area:.2f}, Timestamp: {timestamp}"
            )
            mqtt_client.publish(TOPIC, message)
            print(f"Published: {message}")

    # Annotate the frame with detection results
    annotated_frame = results[0].plot()

    # Display the frame
    cv2.imshow("YOLO General Alerts", annotated_frame)

    # Exit the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close OpenCV windows
camera.release()
cv2.destroyAllWindows()
mqtt_client.disconnect()
