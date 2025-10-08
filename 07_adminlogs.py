import customtkinter as ctk
import threading
from kafka import KafkaConsumer
import json
from datetime import datetime

# Kafka Config
KAFKA_BROKER = "localhost:9092"
TOPIC_PASSENGER = "passenger-real-time-info"
TOPIC_NOTIFICATIONS = "train-notifications"
TOPIC_OPERATIONAL = "operational-scheduling"
TOPIC_OCCUPANCY = "train-occupancy-levels"

# Setup CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Admin Dashboard - Logging")
        self.geometry("950x650")

        self.tabview = ctk.CTkTabview(self, width=930, height=620)
        self.tabview.pack(padx=10, pady=10)

        self.tab_occupancy = self.tabview.add("Occupancy Levels")
        self.tab_notification = self.tabview.add("Train Notifications")
        self.tab_operational = self.tabview.add("Operational Scheduling")
        self.tab_passenger = self.tabview.add("Passenger Info")
        
        

        # Create textboxes for each tab
        self.text_occupancy = self._create_tab_textbox(self.tab_occupancy)
        self.text_notification = self._create_tab_textbox(self.tab_notification)
        self.text_operational = self._create_tab_textbox(self.tab_operational)
        self.text_passenger = self._create_tab_textbox(self.tab_passenger)
        
    

        # Start background threads for Kafka consumption
        threading.Thread(target=self.consume_occupancy_levels, daemon=True).start()
        threading.Thread(target=self.consume_notifications, daemon=True).start()
        threading.Thread(target=self.consume_operational_scheduling, daemon=True).start()
        threading.Thread(target=self.consume_passenger_info, daemon=True).start()
        
        

    def _create_tab_textbox(self, parent_tab):
        textbox = ctk.CTkTextbox(parent_tab, width=900, height=580, wrap="word")
        textbox.pack(padx=10, pady=10)
        return textbox

    def consume_passenger_info(self):
        consumer = KafkaConsumer(
            TOPIC_PASSENGER,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        for msg in consumer:
            data = msg.value
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = (
                f"[{timestamp}]\n 🚆Train {data['train_id']} → {data['status']}\n"
                f"Occupancy: {data['occupancy_level']}%, Carriages: {data['carriages']}, Speed: {data['speed']}km/h\n\n\n"
            )
            self.text_passenger.insert("end", output)
            self.text_passenger.see("end")

    def consume_notifications(self):
        consumer = KafkaConsumer(
            TOPIC_NOTIFICATIONS,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        for msg in consumer:
            data = msg.value
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = f"[{timestamp}]\n 📢 Notification: {data.get('message', 'No message provided.')}\n\n\n"
            self.text_notification.insert("end", output)
            self.text_notification.see("end")

    def consume_operational_scheduling(self):
        consumer = KafkaConsumer(
            TOPIC_OPERATIONAL,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        for msg in consumer:
            data = msg.value
            timestamp = data.get('timestamp') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = (
                f"[{timestamp}]\n 🛠️ Train {data['train_id']} Action: {data['action']}, \n"
                f"Reason: {data['reason']}, Status: {data['status']}\n"
                f"Speed: {data['speed']} km/h, Carriages: {data['carriages']}, Occupancy: {data['occupancy_level']}%\n\n\n"
            )
            self.text_operational.insert("end", output)
            self.text_operational.see("end")

    def consume_occupancy_levels(self):
        consumer = KafkaConsumer(
            TOPIC_OCCUPANCY,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )
        for msg in consumer:
            data = msg.value
            timestamp = data.get('timestamp') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            total_occupancy = 0
            total_seats = 0

            for carriage in data["carriage_details"]:
                total_seats += carriage["max_seats"]
                total_occupancy += carriage["occupied_seats"]

            # Calculate the average occupancy level for the entire train
            if total_seats > 0:
                average_occupancy_level = (total_occupancy / total_seats) * 100
            else:
                average_occupancy_level = 0.0

            output = (
                f"[{timestamp}]\n 📊 Train {data['train_id']} → Occupancy Level: {average_occupancy_level:.2f}%\n\n\n"
            )
            self.text_occupancy.insert("end", output)
            self.text_occupancy.see("end")


if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
