import paho.mqtt.client as mqtt
import sqlite3
import json
from datetime import datetime

mqtt_broker = "192.168.1.105" 
port = 1883
topic = "sound/classification"

conn = sqlite3.connect('server_log.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sound_classification_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        outcome TEXT,
        confidence REAL
    )
''')

def log_to_database(outcome, confidence):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO sound_classification_log (timestamp, outcome, confidence) VALUES (?, ?, ?)",
                   (timestamp, outcome, confidence))
    conn.commit()

def on_message(client, userdata, message):
    print("Message received") 
    try:
        payload = json.loads(message.payload.decode())
        outcome = payload.get("outcome", "Unknown")
        confidence = payload.get("confidence", 0.0)
        timestamp = payload.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        log_to_database(outcome, confidence)
        print(f"Logged: {outcome} with confidence {confidence} at {timestamp}")

    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

client = mqtt.Client()
client.on_message = on_message

client.connect(mqtt_broker)
client.subscribe(topic)
client.loop_forever()
