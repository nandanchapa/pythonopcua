import asyncio
import random
import json
import logging
from asyncua import Server
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# --- AWS CONFIGURATION ---
ENABLE_AWS = True  # Set to True to enable AWS IoT, False to run local only

AWS_ENDPOINT = "awsiotcoreendpoint-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "OPCUA_Client"
PATH_TO_CERT = "certificate.pem.crt"
PATH_TO_KEY = "private.pem.key"
PATH_TO_ROOT_CA = "AmazonRootCA1.pem"
TOPIC = "nandan/opcua/sensors"

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

def publish_to_aws(mqtt_client, payload):
    """Helper function to publish data only if client is active."""
    
    if ENABLE_AWS and mqtt_client:
        mqtt_client.publish(TOPIC, json.dumps(payload), 1)
        print(f"Published to AWS: {payload}")

async def main():
    # 1. Initialize AWS (Returns None if ENABLE_AWS is False)
    mqtt_client = init_aws_mqtt()
    
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
            print(f"Final Payload: {payload}")

            await asyncio.sleep(2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())