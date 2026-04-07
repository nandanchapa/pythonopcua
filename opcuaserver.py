import asyncio
import random
import json
import logging
import os
from dotenv import load_dotenv
from asyncua import Server
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from influxdb_client_3 import InfluxDBClient3, Point

# --- 1. LOAD ENVIRONMENT VARIABLES ---
# This looks for a file named .env in the same folder as this script
load_dotenv()

# --- CONFIGURATION ---
ENABLE_AWS = False  # Set to True to enable AWS IoT, False to run local only
ENABLE_INFLUX = True

AWS_ENDPOINT = "awsiotcoreendpoint-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "OPCUA_Client"
PATH_TO_CERT = "certificate.pem.crt"
PATH_TO_KEY = "private.pem.key"
PATH_TO_ROOT_CA = "AmazonRootCA1.pem"
TOPIC = "nandan/opcua/sensors"

# InfluxDB 3 Config (Pulled strictly from .env)
INFLUX_HOST = "http://localhost:8181"
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_DB = os.getenv("INFLUXDB_DATABASE")

def init_aws_mqtt():
    """Initializes the AWS MQTT Client."""
    if not ENABLE_AWS:
         return None
   
    try:

        mqtt_client = AWSIoTMQTTClient(CLIENT_ID)
        mqtt_client.configureEndpoint(AWS_ENDPOINT, 8883)
        mqtt_client.configureCredentials(PATH_TO_ROOT_CA, PATH_TO_KEY, PATH_TO_CERT)
        
        print(f"--- Attempting to connect to {AWS_ENDPOINT} ---")
        connection_success = mqtt_client.connect()
        
        if connection_success:
            print("--- SUCCESS: Connected to AWS IoT Core ---")
            return mqtt_client
        else:
            print("--- FAILURE: Connection returned False (Check IoT Policy/Cert) ---")
            return None

    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"CRITICAL AWS ERROR: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return None

def init_influxdb():
    """Initializes the InfluxDB 3 Client for local storage."""
    if not ENABLE_INFLUX:
        return None
    
    # Safety Check: Ensure .env variables actually loaded
    if not INFLUX_TOKEN or not INFLUX_DB:
        print("⚠️  WARNING: InfluxDB credentials missing from .env!")
        return None

    try:
        client = InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=INFLUX_DB)
        print(f"✅ SUCCESS: InfluxDB 3 Client Initialized")
        return client
    except Exception as e:
        print(f"❌ INFLUX INIT ERROR: {e}")
        return None

def publish_to_aws(mqtt_client, payload):
    """Helper function to publish data only if client is active."""
    
    if ENABLE_AWS and mqtt_client:
        mqtt_client.publish(TOPIC, json.dumps(payload), 1)
        print(f"Published to AWS: {payload}")

def write_to_influx(influx_client, payload):
    """Encapsulates InfluxDB 3 High-Speed writing."""
    if ENABLE_INFLUX and influx_client:
        try:
            # Create a point and map the entire payload dictionary as fields
            point = Point("pythonopcua_sensors").tag("source", "nandan_virtualbox")
            for sensor_name, value in payload.items():
                point.field(sensor_name, float(value))
            
            influx_client.write(record=point)
            print(f"🗄️  InfluxDB Local: Data point saved")
        except Exception as e:
            print(f"❌ INFLUX WRITE ERROR: {e}")

async def main():
    # 1. Initialize AWS (Returns None if ENABLE_AWS is False)
    mqtt_client = init_aws_mqtt()
    influx_client = init_influxdb()
    
    # 2. Initialize OPC UA Server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/nandanopcua/server/")
    
    uri = "http://nandan.opcua.github.io"
    idx = await server.register_namespace(uri)

    # 3. Create Object and Nodes
    myobj = await server.nodes.objects.add_object(idx, "RandomSensorObject")
    nodes = []
    for i in range(1, 5):
        node = await myobj.add_variable(idx, f"RandomNumber_{i}", 0.0)
        await node.set_writable()
        nodes.append(node)

    print(f"OPC UA Server started at {server.endpoint}")

    async with server:
        while True:
            payload = {}
            for i, node in enumerate(nodes):
                val = round(random.uniform(10.0, 100.0), 2)
                # Update OPC UA Nodes 
                await node.write_value(val)
                payload[f"sensor_{i+1}"] = val
            # 4. Attempt to Publish (Logic is hidden inside the function)
            publish_to_aws(mqtt_client, payload)
            write_to_influx(influx_client, payload)
            print(f"Final Payload: {payload}")

            await asyncio.sleep(2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("n🛑Server stopped by user")