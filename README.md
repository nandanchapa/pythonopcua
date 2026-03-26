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

## Architecture

```mermaid

graph LR
    %% Node Definitions
    subgraph Local ["Local Environment (VirtualBox / Linux)"]
        A[Python Script: server.py]
        B[(OPC UA Address Space)]
        C{ENABLE_AWS Toggle}
    end

    subgraph External ["External Protocols"]
        D[OPC UA Client: e.g., UaExpert]
    end

    subgraph Cloud ["Cloud (AWS)"]
        E[AWS IoT Core]
        F[MQTT Topic: nandan/opcua/sensors]
    end

    %% Connections with specific label positioning
    A -->|1. Generates| B
    B -->|2. Updates| A
    
    %% Move the port label to the start of the line to avoid the middle intersection
    D -.->|Reads/Writes Port: 4840| B
    
    A ---|3. Check Toggle| C
    
    %% Use thick line for cloud to separate it visually
    C ===|If True Port: 8883| E
    E -->|4. Publishes| F

    %% Styling with Black Text
    classDef local fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef cloud fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000;
    classDef toggle fill:#e8f5e9,stroke:#2e7d32,stroke-dasharray: 5 5,color:#000;

    class A,B local;
    class D external;
    class E,F cloud;
    class C toggle;
```
