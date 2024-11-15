import paho.mqtt.client as mqtt

mqtt_broker = "192.168.1.105" 
topic = "test/topic"

client = mqtt.Client("TestClient")
client.connect(mqtt_broker)

client.publish(topic, "Hello from Python MQTT")
print("Message published")
