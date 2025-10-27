# Supplier Catalog Ingestion Agent

A **LangGraph-powered FastAPI** application for automating supplier catalog data extraction, validation, and email notifications. This intelligent agent leverages **multimodal Groq LLMs, MySQL, and SMTP** to process supplier catalog images, extract structured product data, validate entries, update databases, and notify procurement teams — all autonomously.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation-&-setup) 
  - [Clone the Repository](#clone-the-repository)
  - [Create Virtual Environment](#create-virtual-environment)
  - [Install Dependencies](#install-dependencies)
  - [Environment Configuration](#environment-configuration)
  - [Database Setup](#database-setup)
  - [Run the Application](#run-the-application)
- [API Endpoints](#api-endpoints)
  - [Catalog Processing Workflow](#catalog-processing-workflow)
- [Usage Examples](#usage-examples)
- [Release Notes](#v100)

---

## Features

The LangGraph workflow follows this sequence:

1. **Load Data** → Reads and validates input CSV.  
2. **Production Forecaster** → Uses Prophet to forecast units produced.  
3. **Check Shortfall** → Compares forecasts against monthly targets.  
4. **Location Risk Classifier** → Evaluates city-wise operational risks.  
5. **Safety Risk Analyzer** → Calculates safety-based risk scores.  
6. **Send Alerts** → Dispatches automated summary emails.

## Architecture

| Layer | Description |
|-------|-------------|
| **LangGraph Layer** | Manages state transitions and agent communication. |
| **Agent Layer** | Implements business logic for analysis, targeting, and recommendations. |
| **Service Layer** | Handles data fetching and transformations. |
| **Schema Layer** | Defines Pydantic models for input/output validation. |
| **Flask Layer** | Exposes Flask APIs for external integration. |

---

## Prerequisites

- Python 3.10 or higher  
- Git

---

## Installation & Setup

### Clone the Repository
```bash
git clone https://github.com/GWC-Agentic-AI/AI-Driven-Downtime-Root-Cause-Agent.git
cd AI-Driven-Downtime-Root-Cause-Agent
```

### Create Virtual Environment

Using Python venv:
```bash
python -m venv venv
# Activate on Windows
venv\Scripts\activate
# Activate on macOS/Linux
source venv/bin/activate
```
Optional: Using UV for virtual environment
```bash
pip install uv
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### Install Dependencies
```bash 
pip install -r requirements.txt
```
#### or using uv
```bash
uv add -r requirements.txt
```

### Environment Configuration

#### Create a ```.env``` file in the project root:
```bash
SENDER_EMAIL=<sender_email>
SENDER_PASSWORD=<<sender_password>
RECIEVER_MAIL=<receiver_email>
```

### Run the Application
```bash
python run.py
```
Access API at: http://127.0.0.1:5000/

### API Endpoints
### Upload Data
| Method | Endpoint                | Description                                  |
| ------ | ----------------------- | -------------------------------------------- |
| POST   | `/api/upload-data` | Upload the inventory csv file of records to check downtime. |

Example Request :
```POST
{
  "file": "Inventory.csv"
}
```
Example Response:
```json{
    "file_path": "D:\\Inventory.csv",
    "message": "File saved to D:\\Inventory.csv"
}
```

### Downtime Analysis
| Method | Endpoint                                      | Description                                                     |
| ------ | --------------------------------------------- | --------------------------------------------------------------- |
| POST   | `/api/run-analysis` | Submits the data for Downtime check with a monthly target and forecast manufacture for next {n} days. |

Example Request:
```json{
  "data_path": "D:/Inventory.csv",
  "monthly_target": 15000,
  "forecast_days": 30
}
```
Example Response:
```json
{
    "message": "Analysis completed and alerts sent.",
    "shortfall_status": {
        "Forecasted Total Units": {
            "0": ....,
            "1": ....
        },
        "Month": {
            "0": "2025-04",
            "1": "2025-05"
        },
        "Monthly Target": {
            "0": 15000,
            "1": 15000
        },
        "Shortfall": {
            "0": true,
            "1": true
        }
    }
}
```

### Usage Examples

- Start manufacturing analysis using historical data and forecast for the upcoming days.
- Send the analysis responses via email.

### v1.0.0

- Initial release of Downtime & Maintenance Agent

- Core LangGraph pipeline for Upload Data, Forecasting, Shortfall Alert, Location Alert & Safety Alert.

- Flask integration for API access.

- Workflow visualization (graph.png)

- Modular and extensible codebase
