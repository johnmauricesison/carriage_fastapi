import customtkinter as ctk
from kafka import KafkaConsumer
import threading
import json


KAFKA_BROKER = "localhost:9092"
TOPIC_PASSENGER_INFO = "passenger-real-time-info"
TOPIC_NOTIFICATIONS = "train-notifications"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("600x400")
app.title("🚆 Passenger Dashboard")


train_passenger_data = {}
train_notification_data = {}


def consume_passenger_info():
    try:
        consumer = KafkaConsumer(
            TOPIC_PASSENGER_INFO,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        )
        for msg in consumer:
            data = msg.value
            train_passenger_data[data['train_id']] = data
    except Exception as e:
        print(f"[ERROR] Failed to connect to Kafka consumer for passenger info: {e}")


def consume_notifications():
    try:
        consumer = KafkaConsumer(
            TOPIC_NOTIFICATIONS,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        )
        for msg in consumer:
            data = msg.value
            train_notification_data[data['train_id']] = data
    except Exception as e:
        print(f"[ERROR] Failed to connect to Kafka consumer for notifications: {e}")


threading.Thread(target=consume_passenger_info, daemon=True).start()
threading.Thread(target=consume_notifications, daemon=True).start()


title = ctk.CTkLabel(app, text="🚆 Passenger App\nEnter Train ID", font=ctk.CTkFont(size=16, weight="bold"))
title.pack(pady=10)

train_id_entry = ctk.CTkEntry(app, placeholder_text="Train ID")
train_id_entry.pack(pady=5)


scrollable_frame = ctk.CTkScrollableFrame(app, height=250)
scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

result_label = ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=13), justify="left")
result_label.pack(pady=20)

def search_train():
    try:
        train_id = train_id_entry.get().strip()
        text = ""

        if train_id in train_notification_data:
            n_data = train_notification_data[train_id]
            text += (
                f"Notification Details\n"
                f"Message: {n_data['message']}\n"
                f"Train Class: {n_data['train_class']}\n"
                f"Occupancy Level: {n_data['average_occupancy_level']}%\n"
                f"Carriages: {n_data['carriages']}\n"
                f"Speed: {n_data['speed']} km/h\n"
            )

            text += "\n🚃 Carriage Details:\n"
            for carriage in n_data.get("carriage_details", []):
                text += (
                    f" - Carriage {carriage['carriage_number']}: "
                    f"{carriage['occupied_seats']}/{carriage['max_seats']} occupied "
                    f"({carriage['occupancy_level']}%)\n"
                )
        else:
            text += "\n🚫 No notification found for this Train ID.\n"

        if train_id in train_passenger_data:
            p_data = train_passenger_data[train_id]
            text += (
                f"\nTrain Schedule\n"
                f"Status: {p_data['status']}\n"
            )
        else:
            text += "🚫 No passenger data found for this Train ID.\n\n"

        result_label.configure(text=text)
    except ValueError as ve:
        result_label.configure(text=f"[ERROR] {ve}")
    except KeyError as ke:
        result_label.configure(text=f"[ERROR] Missing data for train: {ke}")
    except Exception as e:
        result_label.configure(text=f"[ERROR] Unexpected error: {e}")

search_button = ctk.CTkButton(app, text="Submit", command=search_train)
search_button.pack(pady=10)

app.mainloop()
