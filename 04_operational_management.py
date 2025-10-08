from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
import json
from pydantic import BaseModel, ValidationError


TOPIC_OCCUPANCY = "train-occupancy-levels"
TOPIC_SCHEDULING = "operational-scheduling"
KAFKA_BROKER = "localhost:9092"

class CarriageData(BaseModel):
    carriage_number: int
    max_seats: int
    occupied_seats: int

class TrainData(BaseModel):
    train_id: str
    train_class: str
    carriages: int
    carriage_details: list[CarriageData]
    speed: float

def safe_deserializer(message):
    try:
        return TrainData.model_validate_json(message.decode('utf-8'))
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during deserialization: {e}")
        return None
    

consumer = KafkaConsumer(
    TOPIC_OCCUPANCY,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: TrainData.model_validate_json(m.decode('utf-8'))

)

# Kafka Producer to send alerts
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')

)


print("🔔 Operational management running and monitoring train occupancy...\n")



DECISION_MAP = {
    "ADD_TRIP": {
        "reason": "Critical demand, add trip",
        "status": "1HOUR"
    },
    "ADD_CARRIAGES": {
        "reason": "High demand, adding wagons",
        "status": "NEXT_TRIP"
    },
    "MERGE_ROUTE": {
        "reason": "Moderate demand, merging similar routes",
        "status": "RESCHEDULED"
    },
    "REDUCE_FREQUENCY": {
        "reason": "Low demand, reducing trip frequency",
        "status": "2HOURS"
    },
    "CANCEL_TRIP": {
        "reason": "Very low demand, cancelling trip",
        "status": "CANCELLED"
    },
    "ROUTE_REVIEW": {
        "reason": "Train route or speed needs review",
        "status": "FLAGGED"
    },
    "MAINTAIN_SCHEDULE": {
        "reason": "Stable operation",
        "status": "EA"
    },
    "INVALID": {
        "reason": "Data integrity issue",
        "status": "error"
    }
}



def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def determine_schedule(data: TrainData):

    try:

        action = "MAINTAIN_SCHEDULE"
        total_seats = 0
        total_occupancy = 0

        for carriage in data.carriage_details:
            total_seats += carriage.max_seats
            total_occupancy += carriage.occupied_seats

        occupancy_level = (total_occupancy / total_seats) * 100 if total_seats > 0 else 0.0
        
        if occupancy_level >= 90:
            # 🚨 Overcrowded
            if data.speed >= 200: 
                action = "ADD_TRIP"

            # 🚨 High but slower train || ⚠️ High demand
            else:
                action = "ADD_CARRIAGES"


        # ✅ Stable usage
        elif 60 <= occupancy_level < 90:
            action = "MAINTAIN_SCHEDULE"

        # 🌀 Underused
        elif 50 <= occupancy_level < 70:
            action = "MERGE_ROUTE"

        # 🧊 Low demand
        elif 25 <= occupancy_level < 40:
            action = "REDUCE_FREQUENCY"

        # 🛑 Critically low || 🏗️ Too many wagons & underused
        elif occupancy_level < 25:
            action = "CANCEL_TRIP"

        # 🐢 Slow business train
        if data.train_class.upper() == 'EXPRESS' and data.speed < 80:
            action = "ROUTE_REVIEW"

        # ⚡ Speedy economy train
        elif data.train_class.upper() == 'ECONOMY' and data.speed > 110:
            action = "ROUTE_REVIEW"


        # 🔎 Invalid input check (optional)
        if occupancy_level > 150 or data.carriages <= 0:
            action = "INVALID"
        

        return {
            "train_id": data.train_id,
            "action": action,
            "reason": DECISION_MAP[action]["reason"],
            "status": DECISION_MAP[action]["status"],
            "carriages": data.carriages,
            "occupancy_level": round(occupancy_level),
            "speed": data.speed,
            "timestamp": get_current_timestamp()
        }
    
    except Exception as e:
        print(f"Error processing train data: {e}")
        return None

for message in consumer:
    try:
        data = message.value
        schedule_decision = determine_schedule(data)

        if schedule_decision:
            print(f"[{schedule_decision['timestamp']}]\nTrain {schedule_decision['train_id']} → {schedule_decision['action']} ({schedule_decision['reason']}) → ({schedule_decision['status']})")
            producer.send(TOPIC_SCHEDULING, value=schedule_decision)
        else:
            print("Failed to process message due to error in train data.")
    except ValidationError as ve:
        print(f"Validation error: {ve}")
    except Exception as e:
        print(f"Unexpected error in message processing: {e}")