import customtkinter as ctk
import requests

# FastAPI server URL
API_URL = "http://127.0.0.1:8000/train_data/"

# CUSTOMTKINTER GUI
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("900x600")
app.title("🚆 Train Occupancy Input")

# LAYOUT SETUP
app.grid_columnconfigure((0, 1), weight=1)
app.grid_rowconfigure(0, weight=1)

# LEFT PANEL: FORM INPUTS
left_frame = ctk.CTkFrame(app, corner_radius=10)
left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
left_frame.grid_columnconfigure(0, weight=1)

# TRAIN ID INPUT
train_label = ctk.CTkLabel(left_frame, text="Train ID:")
train_label.grid(row=0, column=0, pady=(20, 5), padx=10, sticky="w")
train_input = ctk.CTkEntry(left_frame, placeholder_text="e.g., 001")
train_input.grid(row=1, column=0, padx=10, sticky="ew")

# TRAIN CLASS INPUT
train_class = ctk.CTkLabel(left_frame, text="Train Class:")
train_class.grid(row=2, column=0, pady=(20, 5), padx=10, sticky="w")
train_class_input = ctk.CTkEntry(left_frame, placeholder_text="e.g., Express or Economy")
train_class_input.grid(row=3, column=0, padx=10, sticky="ew")

# NO. OF CARRIAGES INPUT
carriages = ctk.CTkLabel(left_frame, text="Carriages:")
carriages.grid(row=4, column=0, pady=(20, 5), padx=10, sticky="w")
carriages_input = ctk.CTkEntry(left_frame, placeholder_text="e.g., 8")
carriages_input.grid(row=5, column=0, padx=10, sticky="ew")


generate_button = ctk.CTkButton(left_frame, text="Generate Wagon Inputs")
generate_button.grid(row=6, column=0, pady=10, padx=10, sticky="ew")

# SPEED INPUT
speed_label = ctk.CTkLabel(left_frame, text="Speed (Km/H):")
speed_label.grid(row=7, column=0, pady=(20, 5), padx=10, sticky="w")
speed_input = ctk.CTkEntry(left_frame, placeholder_text="e.g., 150")
speed_input.grid(row=8, column=0, padx=10, sticky="ew")

send_button = ctk.CTkButton(left_frame, text="Send to FastAPI")
send_button.grid(row=9, column=0, pady=10, padx=10, sticky="ew")

# STATUS LABEL
status_label = ctk.CTkLabel(left_frame, text="", text_color="green")
status_label.grid(row=10, column=0, pady=10, padx=10, sticky="w")

right_frame = ctk.CTkScrollableFrame(app, corner_radius=10)
right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
right_frame.grid_columnconfigure(0, weight=1)

carriage_inputs = []

def generate_inputs():
    for widget in right_frame.winfo_children():
        widget.destroy()
    carriage_inputs.clear()

    try:
        wagon_count = int(carriages_input.get())
    except ValueError:
        status_label.configure(text="⚠️ Invalid wagon count", text_color="yellow")
        return

    for i in range(wagon_count):
        label = ctk.CTkLabel(right_frame, text=f"Wagon {i+1}", font=ctk.CTkFont(weight="bold"))
        label.grid(row=i*3, column=0, pady=(10, 0), padx=10, sticky="w")

        max_seats_entry = ctk.CTkEntry(right_frame, placeholder_text="Max Seats")
        max_seats_entry.grid(row=i*3+1, column=0, padx=10, pady=(0, 2), sticky="ew")

        occ_seats_entry = ctk.CTkEntry(right_frame, placeholder_text="Occupied Seats")
        occ_seats_entry.grid(row=i*3+2, column=0, padx=10, pady=(0, 10), sticky="ew")

        carriage_inputs.append({
            "max_seats": max_seats_entry,
            "occupied_seats": occ_seats_entry
        })

def send_data():
    train = train_input.get()
    train_class = train_class_input.get()
    carriages = carriages_input.get()
    speed = speed_input.get()

    if not (train and train_class and carriages and speed):
        status_label.configure(text="⚠️ Fill in all fields", text_color="yellow")
        return

    try:
        speed = float(speed)
        carriage_data = []

        for i, car in enumerate(carriage_inputs):
            seats = int(car["max_seats"].get())
            occ = int(car["occupied_seats"].get())
            level = (occ / seats) * 100 if seats > 0 else 0

            carriage_data.append({
                "carriage_number": i + 1,
                "max_seats": seats,
                "occupied_seats": occ,
                "occupancy_level": level
            })

        data = {
            "train_id": train,
            "train_class": train_class,
            "carriages": carriage_data,
            "speed": speed
        }

        response = requests.post(API_URL, json=data)

        if response.status_code == 200:
            status_label.configure(text="✅ Sent to Kafka!", text_color="green")
        else:
            status_label.configure(text="❌ Error with API", text_color="red")

    except Exception as e:
        status_label.configure(text=f"❌ Error: {e}", text_color="red")

generate_button.configure(command=generate_inputs)
send_button.configure(command=send_data)

app.mainloop()
