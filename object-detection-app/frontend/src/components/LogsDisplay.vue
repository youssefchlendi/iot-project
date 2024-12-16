<template>
  <div class="logs-container">
    <div class="header-container">
      <h1>Object Detection Logs</h1>
      <button class="refresh-button" @click="fetchLogs">
        <span>Refresh</span>
      </button>
    </div>

    <!-- System Monitoring Section -->
    <div class="monitoring-container">
      <h2>System Monitoring</h2>
      <ul>
        <li><strong>MongoDB Status:</strong> {{ status.mongoStatus }}</li>
        <li><strong>Log Count:</strong> {{ status.logCount }}</li>
        <li><strong>MQTT Status:</strong> {{ status.mqttStatus }}</li>
        <li>
          <strong>Alarm Active:</strong> {{ status.alarmActive ? "Yes" : "No" }}
        </li>
        <li>
          <strong>Alarm Frequency:</strong> {{ status.alarmFrequency }} Hz
        </li>
        <li><strong>Alarm Duration:</strong> {{ status.alarmDuration }} ms</li>
      </ul>
      <button class="refresh-button" @click="fetchSystemStatus">
        <span>Refresh Status</span>
      </button>
    </div>

    <div class="alerts-container">
      <h2>Real-Time Alerts</h2>
      <ul>
        <li v-for="(alert, index) in alerts" :key="index">
          {{ alert }}
        </li>
      </ul>
    </div>

    <!-- Detection Logs Table -->
    <table class="logs-table">
      <thead>
        <tr>
          <th>Object</th>
          <th>Confidence</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log._id">
          <td>{{ log.object }}</td>
          <td>{{ log.confidence.toFixed(2) }}</td>
          <td>{{ new Date(log.timestamp).toLocaleString() }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Command Form -->
    <form @submit.prevent="sendCommand" class="command-form">
      <input
        v-model="command"
        type="text"
        placeholder="Enter command"
        required
      />
      <button type="submit">Send Command</button>
    </form>
  </div>
</template>

<script>
import axios from "axios";
import mqtt from "mqtt";

export default {
  data() {
    return {
      logs: [],
      command: "",
      alerts: [],
      mqttClient: null,
      status: {
        mongoStatus: "Unknown",
        logCount: 0,
        mqttStatus: "Unknown",
        alarmActive: false,
        alarmFrequency: 440,
        alarmDuration: 1000,
      },
    };
  },
  methods: {
    async fetchLogs() {
      try {
        const response = await axios.get("http://localhost:3000/api/logs");
        this.logs = response.data;
      } catch (error) {
        console.error("Error fetching logs:", error);
      }
    },
    async fetchSystemStatus() {
      try {
        const response = await axios.get(
          "http://localhost:3000/api/system_status"
        );
        this.status = response.data;
      } catch (error) {
        console.error("Error fetching system status:", error);
      }
    },
    async sendCommand() {
      try {
        await axios.post("http://localhost:3000/api/command", {
          command: this.command,
        });
        await this.fetchLogs();
        await this.fetchSystemStatus();
        alert("Command sent successfully!");
        this.command = "";
      } catch (error) {
        console.error("Error sending command:", error);
        alert("Failed to send command.");
      }
    },
    setupMqttSubscription() {
      const brokerUrl = "ws://broker.hivemq.com:8000/mqtt"; // MQTT WebSocket broker
      this.mqttClient = mqtt.connect(brokerUrl);

      this.mqttClient.on("connect", () => {
        console.log("Connected to MQTT broker");
        this.mqttClient.subscribe("home_security/alerts", (err) => {
          if (err) {
            console.error("Subscription error:", err);
          } else {
            console.log("Subscribed to home_security/alerts");
          }
        });
      });

      this.mqttClient.on("message", (topic, message) => {
        if (topic === "home_security/alerts") {
          const alertMessage = message.toString();
          this.alerts.push(alertMessage);

          // Limit displayed alerts to the last 10
          if (this.alerts.length > 10) {
            this.alerts.shift();
          }
        }
      });

      this.mqttClient.on("error", (err) => {
        console.error("MQTT error:", err);
      });
    },
  },
  mounted() {
    this.fetchLogs();
    this.fetchSystemStatus();
    this.setupMqttSubscription();
  },
  beforeDestroy() {
    if (this.mqttClient) {
      this.mqttClient.end();
    }
  },
};
</script>

<style scoped>
.logs-container {
  max-width: 800px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  color: #333;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.refresh-button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background-color: #4caf50;
  color: white;
  cursor: pointer;
  font-size: 16px;
}

.logs-container h1 {
  text-align: center;
  color: #444;
}

.monitoring-container {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f5f5f5;
}

.monitoring-container h2 {
  text-align: center;
  margin-bottom: 10px;
  color: #444;
}

.monitoring-container ul {
  list-style: none;
  padding: 0;
}

.monitoring-container ul li {
  margin: 8px 0;
  font-size: 16px;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.logs-table th,
.logs-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}

.logs-table th {
  background-color: #f4f4f4;
  font-weight: bold;
}

.logs-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.logs-table tr:hover {
  background-color: #f1f1f1;
}

.command-form {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
}

.command-form input {
  padding: 8px;
  width: 70%;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.command-form button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background-color: #4caf50;
  color: white;
  cursor: pointer;
  font-size: 16px;
}

.command-form button:hover {
  background-color: #45a049;
}

.alerts-container {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fff5f5;
}

.alerts-container h2 {
  margin-bottom: 10px;
  color: #e74c3c;
}

.alerts-container ul {
  list-style: none;
  padding: 0;
}

.alerts-container ul li {
  margin: 8px 0;
  padding: 8px;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  background-color: #ffe6e6;
  color: #e74c3c;
  font-weight: bold;
}
</style>
