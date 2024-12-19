const express = require("express");
const mongoose = require("mongoose");
const mqtt = require("mqtt");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(bodyParser.json());
app.use(cors());

// MongoDB Configuration
mongoose.connect("mongodb://localhost:27017/ObjectDetection", {
});

const DetectionLog = mongoose.model("DetectionLog", new mongoose.Schema({
  object: { type: String, required: true },
  confidence: { type: Number, required: true },
  timestamp: { type: Date, required: true },
}), "DetectionLogs");

const ArchivedLogs = mongoose.model("ArchivedLogs", new mongoose.Schema({
  object: { type: String, required: true },
  confidence: { type: Number, required: true },
  timestamp: { type: Date, required: true },
}), "ArchivedLogs");

// MQTT Configuration
const mqttClient = mqtt.connect("mqtt://broker.hivemq.com");

// API Endpoints
app.get("/api/logs", async (req, res) => {
  try {
    const logs = await DetectionLog.find().sort({ timestamp: -1 }).limit(10);
    console.log("Logs fetched from MongoDB:", logs); // Debug line
    res.json(logs);
  } catch (err) {
    console.error("Error fetching logs:", err);
    res.status(500).send("Internal Server Error");
  }
});


app.post("/api/command", (req, res) => {
  const { command } = req.body;
  mqttClient.publish("home_security/commands", command, (err) => {
    if (err) {
      console.error("Error publishing command:", err);
      return res.status(500).send("Failed to publish command.");
    }
    console.log(`Command published: ${command}`);
    res.send({ status: "Command sent", command });
  });
});

app.get("/api/system_status", async (req, res) => {
  try {
    // Check MongoDB connection
    const mongoStatus = mongoose.connection.readyState === 1 ? "Connected" : "Disconnected";

    // Count logs
    const logCount = await DetectionLog.countDocuments({});

    // Check MQTT connection
    const mqttStatus = mqttClient.connected ? "Connected" : "Disconnected";

    // Alarm status (simulate from an in-memory flag or extend logic)
    let alarmActive = false;
    let alarmFrequency = 0;
    let alarmDuration = 0;
    let flashActive = false;
    let flashFreq = 0;
    let flashDuration = 0;

    await mqttClient.publishAsync("home_security/commands", "get_status");

    // get the last message from the MQTT broker under the topic home_security/status
    mqttClient.subscribe("home_security/status");

    await new Promise((resolve) => {
      mqttClient.on("message", (topic, message) => {
        console.log("Received message from MQTT broker:", topic, message.toString());
        if (topic === "home_security/status") {
          const response = JSON.parse(message.toString());
          alarmActive = response.alarm_active;
          alarmFrequency = response.frequency;
          alarmDuration = response.duration;
          flashActive = response.flash_active;
          flashFreq = response.flash_freq;
          flashDuration = response.flash_duration;

          resolve();
        }
      });
    });

    // Construct system status
    const status = {
      mongoStatus,
      logCount,
      mqttStatus,
      alarmActive,
      alarmFrequency,
      alarmDuration,
      flashActive,
      flashFreq,
      flashDuration,
    };

    res.json(status);
  } catch (err) {
    console.error("Error fetching system status:", err);
    res.status(500).send("Error fetching system status.");
  }
});

app.post("/api/cache_logs", async (req, res) => {
  try {
    const logs = await DetectionLog.find();
    ArchivedLogs.insertMany(logs);
    DetectionLog.deleteMany({}).exec();
    res.json({ status: "Logs archived and cache cleared." });
  } catch (err) {
    console.error("Error fetching logs:", err);
    res.status(500).send("Internal Server Error");
  }
});


// Start Server
const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
