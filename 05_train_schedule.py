
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
import json
from pydantic import BaseModel, ValidationError

TOPIC_SCHEDULING = "operational-scheduling"
TOPIC_PASSENGER_INFO = "passenger-real-time-info"
KAFKA_BROKER = "localhost:9092"


class TrainSchedule(BaseModel):
    train_id: str
    action: str
    reason: str
    status: str
    occupancy_level: float
    carriages: int
    speed: float
    timestamp: str

consumer = KafkaConsumer(
    TOPIC_SCHEDULING,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: TrainSchedule.model_validate_json(m.decode('utf-8'))

)


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')

)

print("🔔 Passenger service running and monitoring train occupancy...\n")

ACTION_TRANSLATION = {
    "ADD_TRIP": "A new train will be added shortly due to high demand.",
    "ADD_CARRIAGES": "Additional carriages are being added to the train for better capacity.",
    "MERGE_ROUTE": "Two similar routes are being combined to optimize schedules.",
    "REDUCE_FREQUENCY": "The train frequency is reduced due to lower demand.",
    "CANCEL_TRIP": "The scheduled train has been cancelled due to very low demand.",
    "ROUTE_REVIEW": "The train's route or speed is under review for better performance.",
    "MAINTAIN_SCHEDULE": "The train is operating on its regular schedule, no changes.",
    "INVALID": "System issue or failed data retrieval."
}

STATUS_TRANSLATION = {
    "1HOUR": "The next train will depart in about an hour. Please wait for the next train.",
    "NEXT_TRIP": "This is the next train departure. Please standby.",
    "RESCHEDULED": "The train schedule has been rescheduled. Please wait for the next train.",
    "2HOURS": "The train will depart in two hours. Please wait.",
    "CANCELLED": "This train has been cancelled. Please wait for the next train.",
    "FLAGGED": "The train route is under review and may change. Please wait for the next train.",
    "EA": "The train is expected to arrive as scheduled. Please standby.",
    "error": "error, please try again."
}


def passenger_info(schedule: TrainSchedule):
    try:
        status_translation = STATUS_TRANSLATION.get(schedule.status, "Status unknown.")
        action_translation = ACTION_TRANSLATION.get(schedule.action, "Action unknown.")
        
        message = {
            "train_id": schedule.train_id,
            "status": status_translation,
            "action": action_translation,
            "occupancy_level": round(schedule.occupancy_level),
            "carriages": schedule.carriages,
            "speed": round(schedule.speed),
            "timestamp": schedule.timestamp
        }

        return message
    except Exception as e:
        print(f"[ERROR] Error processing train schedule: {e}")
        return None


for message in consumer:
    try:
        schedule_data = message.value
        passenger_message = passenger_info(schedule_data)

        if passenger_message:
            print(f"\n[{passenger_message['timestamp']}]\nTrain {passenger_message['train_id']} → {passenger_message['status']} → {passenger_message['action']}")
            producer.send(TOPIC_PASSENGER_INFO, value=passenger_message)
            print(f"[INFO] Sent to passengers: \n{passenger_message}")
        else:
            print("[ERROR] Failed to process passenger message.")

    except ValidationError as ve:
        print(f"[ERROR] Validation error: {ve}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")



