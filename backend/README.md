# CrisisNet Backend

This directory contains the MCP Agents and the Coordinator for the CrisisNet system.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    *   Copy `.env.example` to `.env`.
    *   Set your `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS`.

## Running the System

To run the full workflow (Coordinator + Agents):

```bash
python coordinator/main.py
```

## Agents

*   **Data Collector:** `agents/data_collector/main.py` - Fetches disaster data.
*   **Risk Assessment:** `agents/risk_assessment/main.py` - Uses Vertex AI to classify risks.
