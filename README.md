# 🚅 Real-Time Train Occupancy Monitoring System (RTOMS)

**Author:** John Maurice P. Sison  
**Date:** April 22, 2025  

---

## 📘 Overview

The **Real-Time Train Occupancy Monitoring System (RTOMS)** is an intelligent monitoring platform inspired by **Deutsche Bahn’s Lightgate technology**. It uses optical sensors and real-time data processing to track and analyze:

- Passenger occupancy levels  
- Train classifications  
- Number of carriages  
- Train speed  

The system’s data-driven insights empower transportation operators to **optimize scheduling**, **enhance passenger experience**, and **improve operational efficiency**.

---

## 🎯 Objectives

- Provide real-time passenger capacity data.  
- Improve route and scheduling efficiency.  
- Deliver actionable insights for operational decisions.  
- Enhance passenger comfort and satisfaction.  

---

## 🧠 System Architecture

### 4+1 View Model
- **Logical View:** Defines the core data flow and service communication.  
- **Process View:** Details runtime processes and interactions between components.  
- **Development View:** Shows the microservice-based structure and responsibilities.  
- **Deployment View:** Explains how services are distributed and deployed.  
- **Use Cases:** Demonstrates real-world operational decision scenarios.  

---

## 🧩 Microservices Overview

| Service | Role | Topics Published/Consumed |
|----------|------|---------------------------|
| **A. Data Input Service** | Accepts manual or sensor train data | Publishes → `train-occupancy-levels` |
| **B. Operational Management** | Makes scheduling decisions | Consumes → `train-occupancy-levels`<br>Publishes → `operational-scheduling` |
| **C. Notification System** | Sends alerts (e.g., overcrowding, delays) | Consumes → `train-occupancy-levels`<br>Publishes → `train-notifications` |
| **D. Passenger Info Service** | Formats passenger data for end users | Consumes → `operational-scheduling`<br>Publishes → `passenger-real-time-info` |
| **E. Passenger App** | Displays real-time data to passengers | Consumes → `passenger-real-time-info`, `train-notifications` |
| **F. Logging & Analytics** | Aggregates data for system analysis | Consumes → all topics |

---

## 🧵 Kafka Topics

| Topic | Description |
|-------|--------------|
| `train-occupancy-levels` | Collects real-time train occupancy data |
| `train-notifications` | Publishes alerts for overcrowding, delays, and issues |
| `operational-scheduling` | Optimizes train schedules |
| `passenger-real-time-info` | Provides passengers with seat and availability data |

---

## 🚉 Data Model

| Field | Type | Description |
|--------|------|-------------|
| `train_id` | string | Unique train identifier |
| `train_class` | string | Class of train (e.g., *Express*, *Economy*) |
| `carriages` | integer | Number of carriages |
| `occupancy_level` | float | 0–1 ratio of occupancy |
| `speed` | float | Train speed (km/h) |
| `carriage_details` | list | Seat and occupancy details per carriage |

---

## ⚙️ Operational Decision Logic

| Criteria | Condition | Action | Message |
|-----------|------------|--------|----------|
| 🚨 Overcrowded | `occupancy >= 100%` & `speed >= 200` | `ADD_TRIP` | “A new train will be added shortly.” |
| ⚠ High Demand | `85% <= occupancy < 100%` | `ADD_CARRIAGES` | “Additional carriages are being added.” |
| ✅ Stable | `60% <= occupancy < 90%` | `MAINTAIN_SCHEDULE` | “Train operating as scheduled.” |
| 🌀 Underused | `50% <= occupancy < 70%` | `MERGE_ROUTE` | “Routes being optimized.” |
| 🧊 Low Demand | `25% <= occupancy < 40%` | `REDUCE_FREQUENCY` | “Reduced frequency due to lower demand.” |
| 🛑 Critically Low | `< 25%` | `CANCEL_TRIP` | “Train cancelled due to low demand.” |

---

