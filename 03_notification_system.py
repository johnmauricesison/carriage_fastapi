from kafka import KafkaConsumer, KafkaProducer
import json

from kafka.errors import KafkaError
from pydantic import BaseModel, ValidationError

KAFKA_BROKER = "localhost:9092"
TOPIC1 = "train-occupancy-levels"
NOTIFICATION_TOPIC = "train-notifications"


OCCUPANCY_ALERT_THRESHOLD = {
    "high" : 90,
    "medium": 70,
    "low": 40
}

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

try:
    consumer = KafkaConsumer(
        TOPIC1,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda m: json.dumps(m).encode('utf-8')
    )
    
except KafkaError as ke:
    print(f"❌ Kafka connection error: {ke}")
    exit(1)

print("🔔 Notification system running and monitoring train occupancy...\n")



def notif(raw_data: dict):
    try:
        data = TrainData(**raw_data)
    except ValidationError as ve:
        print(f"⚠️ Data validation error: {ve}")
        return
    total_seats = 0
    total_occupancy = 0

    for carriage in data.carriage_details:
        total_seats += carriage.max_seats
        total_occupancy += carriage.occupied_seats

    avg_occupancy = (total_occupancy / total_seats) * 100 if total_seats > 0 else 0.0

    if avg_occupancy > OCCUPANCY_ALERT_THRESHOLD["high"]:
        alert = "🚨 High Alert"
    elif avg_occupancy > OCCUPANCY_ALERT_THRESHOLD["medium"]:
        alert = "🛎️ Moderate Alert"
    elif avg_occupancy > OCCUPANCY_ALERT_THRESHOLD["low"]:
        alert = "🧊 Low Alert"
    else:
        alert = "✅ No Alert"

    notification_msg = {
        "train_id": data.train_id,
        "train_class": data.train_class,
        "message": f"{alert}: Train {data.train_id} occupancy is at {avg_occupancy:.2f}%.",
        "average_occupancy_level": round(avg_occupancy, 2),
        "carriages": data.carriages,
        "carriage_details": [
            {
                "carriage_number": carriage.carriage_number,
                "max_seats": carriage.max_seats,
                "occupied_seats": carriage.occupied_seats,
                "occupancy_level": round((carriage.occupied_seats / carriage.max_seats) * 100, 2)
            }
            for carriage in data.carriage_details
        ],
        "speed": data.speed
    }

    print(f"📤 Sending notification for train {data.train_id}: {notification_msg['message']} \n {notification_msg}")
    producer.send(NOTIFICATION_TOPIC, value=notification_msg)
    

try:
    for message in consumer:
        raw_data = message.value
        if raw_data:
            notif(raw_data)
except KeyboardInterrupt:
    print("🛑 Graceful shutdown requested by user.")
except Exception as e:
    print(f"🔥 Unexpected runtime error: {e}")
