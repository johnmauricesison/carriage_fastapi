from fastapi import FastAPI, HTTPException
from kafka.errors import KafkaError
from pydantic import BaseModel
from kafka import KafkaProducer
import json

app = FastAPI()

KAFKA_BROKER = "localhost:9092"

try:
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
except KafkaError as e:
    producer = None
    print(f"Kafka connection failed: {e}")


class CarriageData(BaseModel):
    carriage_number: int
    max_seats: int
    occupied_seats: int

class TrainData(BaseModel):
    train_id: str
    train_class: str
    carriages: list[CarriageData]
    speed: float



@app.post("/train_data/")
async def train_data(train_data: TrainData):
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka broker unavailable")
    
    try:
        total_occupancy = 0
        total_seats = 0

        for carriage in train_data.carriages:
            if carriage.max_seats == 0:
                raise ValueError(f"Carriage {carriage.carriage_number} has zero max seats.")
            total_seats += carriage.max_seats
            total_occupancy += carriage.occupied_seats

        if total_seats > 0:
            average_occupancy_level = (total_occupancy / total_seats) * 100 if total_seats > 0 else 0.0
        else:
            average_occupancy_level = 0.0

        data = { 
            "train_id": train_data.train_id, 
            "train_class": train_data.train_class, 
            "carriages": len(train_data.carriages), 
            "carriage_details": [
                {
                    "carriage_number": carriage.carriage_number,
                    "max_seats": carriage.max_seats,
                    "occupied_seats": carriage.occupied_seats,
                    "occupancy_level": (carriage.occupied_seats / carriage.max_seats) * 100
                }
                for carriage in train_data.carriages
            ],
            "speed": train_data.speed,
            "average_occupancy_level": average_occupancy_level
        }

        producer.send('train-occupancy-levels', json.dumps(data).encode('utf-8'))
        return {"message": "Train data sent to Kafka", "average_occupancy_level": data}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except KafkaError as ke:
        raise HTTPException(status_code=500, detail="Failed to send data to Kafka")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)