# CrisisNet: A Multi-Agent Real-Time Crisis Intelligence System

## 1. Project Summary and Goal

**CrisisNet** is a multi-agent platform designed to provide real-time safety advice, threat detection, and route guidance during global emergencies, conflicts, and natural disasters. The primary goal is to monitor real-world data, identify emerging threats, and guide users toward safer decisions using a set of modular agents that communicate via the **Model Context Protocol (MCP)**.

The system relies heavily on **Google Gemini** for complex reasoning and classification, and **Google Cloud** services for hosting, data storage, and orchestration.

-----

## 2. Multi-Agent Architecture (How it Works)

CrisisNet uses a modular design composed of specialized agents that expose their capabilities through well-defined **MCP tool endpoints**. The Coordinator orchestrates the end to end workflow.

### Agent Roles

| Agent | Function | Key Tools | Key Technologies |
| :--- | :--- | :--- | :--- |
| **Coordinator Agent** | Orchestrates the full pipeline and manages tool calls. | `call_tool` via `ClientSession` | MCP, Python `asyncio` |
| **Data Collection Agent** | Fetches live information from online feeds and normalizes event objects. | `fetch_disaster_feed`, `fetch_weather` | GDACS API, USGS API, `requests` |
| **Risk Assessment Agent** | Computes severity, type, and risk score for each event. | `classify_event`, `estimate_severity` | **Vertex AI (Gemini-2.5-flash-lite)** |
| **Geolocation Safety Agent** (Planned) | Maps threats near a user, finds shelters, computes safe routes. | `map_threat_radius`, `find_safe_locations`, `compute_routes`, `rank_routes` | **Google Maps APIs** (Routes, Places, Geocoding) |
| **Communication Agent** (Planned) | Turns analytics into user friendly instructions. | `create_alert`, `generate_action_plan`, `explain_risk` | **Vertex AI (Gemini)** |

-----

## 3. Workflow: Current Implementation vs. Final Goal

### A. Current Prototype Flow (Working)

The Coordinator currently runs a basic 2 step workflow:

1. **Fetch Data**  
   Calls the Data Collection Agent’s `fetch_disaster_feed` with `source="MOCK"` or real APIs (GDACS, USGS).

2. **Assess Risk**  
   For each event, calls the Risk Assessment Agent’s `classify_event`, which uses **Gemini-2.5-flash-lite** to generate severity, risk score, and reasoning.

### B. Final System Workflow (Target)

| Step | Agent | Description |
| :--- | :--- | :--- |
| **1. Data Gathering** | Data Collection Agent | Fetches real world disaster data and stores normalized events in Firestore. |
| **2. Event Classification** | Risk Assessment Agent | Computes event category, severity, and risk score using Gemini and stores outputs. |
| **3. User Location Safety** | Geolocation Safety Agent | Determines user proximity to threats, finds shelters, and computes evacuation routes. |
| **4. Safety Instructions** | Communication Agent | Converts raw analytics into actionable emergency instructions and alerts. |
| **5. Continuous Monitoring** | Pub/Sub + Scheduler | Runs the gathering and classification cycle every few minutes. |