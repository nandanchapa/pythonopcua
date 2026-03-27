# Python OPC UA to AWS IoT Core

This project runs an OPC UA Server that generates 4 random sensor nodes and 
optionally publishes the data to AWS IoT Core.

## Setup
1. Create a virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## Usage
- Set `ENABLE_AWS = True` in `server.py` to enable cloud publishing.
- Run the server: `python opcserver.py`

## Infrastructure Provisioning
This project uses **Terraform** to automate the creation of AWS IoT Core resources.

### Prerequisites
1.  **AWS CLI** configured with valid credentials.
2.  **Terraform** installed on your machine.

### Setup Steps
1.  **Provision AWS Resources:**
    ```bash
    terraform init
    terraform apply -auto-approve
    ```
    *This will generate `certificate.pem.crt` and `private.pem.key` in the project root.*

2.  **Download Amazon Root CA:**
    The AWS IoT Python SDK requires the Root CA to verify the server identity.
    ```bash
    wget [https://www.amazontrust.com/repository/AmazonRootCA1.pem](https://www.amazontrust.com/repository/AmazonRootCA1.pem)
    ```

3.  **Run the Bridge:**
    ```bash
    python opcuaserver.py
    ```

### Resources Managed by Terraform
* `aws_iot_thing`: The logical representation of the OPC UA - AWS IoT Core.
* `aws_iot_certificate`: The hardware-level security identity.
* `aws_iot_policy`: Grants `iot:Connect` and `iot:Publish` permissions.
* `local_file`: Automatically exports the keys to the local directory for Python.

### AWS IoT Console Output
![AWS IoT MQTT Client](assets/images/AWSIoTCore_MQTTClient.png)

### OPC UA Server Execution
![Terminal Output](assets/images/Python_OPCUA_Server.png)

### OPC UA Publish Data to AWS IoTCore
![AWS IoT Core Publish](assets/images/PythonOPCUA_AWSIoTCore_Publish.png)


## Architecture

```mermaid
graph TD
    %% Node Definitions
    subgraph Provisioning ["1. Provisioning Phase (One-Time)"]
        TF[Terraform Script]
        CA_DL[[wget Root CA]]
    end

    subgraph Local ["2. Runtime Environment (VirtualBox / Linux)"]
        A[Python Script: opcuaserver.py]
        B[(OPC UA Address Space)]
        
        subgraph Auth ["Security Credentials"]
            CERT[certificate.pem.crt]
            KEY[private.pem.key]
            ROOT[AmazonRootCA1.pem]
        end
    end

    subgraph Cloud ["3. Cloud (AWS IoT Core)"]
        IOT[AWS IoT Gateway]
        POL[IoT Policy]
        THG[IoT Thing]
        TOPIC["MQTT Topic:nandan/opcua/sensors"]
    end

    %% Provisioning Connections
    TF -.-> THG
    TF -.-> POL
    TF -.-> CERT
    TF -.-> KEY
    CA_DL -.-> ROOT

    %% Runtime Connections
    A --> B
    
    %% Expanded connections for better GitHub compatibility
    CERT --> A
    KEY --> A
    ROOT --> A
    
    A ===|"Secure MQTT (8883)"| IOT
    IOT --> TOPIC

    %% Styling
    classDef provision fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef local fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;
    classDef auth fill:#f1f8e9,stroke:#33691e,stroke-width:1px,stroke-dasharray: 5 5,color:#000;
    classDef cloud fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000;

    class TF,CA_DL provision;
    class A,B local;
    class CERT,KEY,ROOT auth;
    class IOT,POL,THG,TOPIC cloud;
```
