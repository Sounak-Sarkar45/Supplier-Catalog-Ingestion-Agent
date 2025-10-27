# Supplier Catalog Ingestion Agent

A **LangGraph-powered FastAPI** application for automating supplier catalog data extraction, validation, and email notifications. This intelligent agent leverages **multimodal Groq LLMs, MySQL, and SMTP** to process supplier catalog images, extract structured product data, validate entries, update databases, and notify procurement teams — all autonomously.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup) 
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

## Overview

The **Supplier Catalog Agent** is an intelligent document-processing workflow designed for procurement automation. It reads supplier catalog images, extracts product metadata (e.g., Product Name, SKU, Price, MOQ), validates the extracted information against existing database records,pdates entries, and automatically sends a detailed email report to procurement teams. This system combines LangGraph’s state-based orchestration with FastAPI, Groq multimodal models, and MySQL persistence to deliver a full-cycle automation pipeline.

## Features

1. **Multimodal LLM Extraction** – Uses Groq models to parse text, numbers, and fields directly from supplier catalog images.

2. **Automated Validation Pipeline** – Applies business logic to detect discrepancies (e.g., price deviations, MOQ issues, discontinued models).

3. **Database Integration** – Reads and writes validated product entries to a MySQL database.

4. **Dynamic Email Generation** – Crafts HTML-based email reports summarizing product validations and flags.

5. **LangGraph Workflow** – Modular, stateful execution of extraction → validation → database → email pipeline.

6. **FastAPI Backend** – RESTful endpoint for real-time catalog image uploads and automated processing.

7. **Environment-Driven Configuration** – Secure and modular setup via .env file for API keys and credentials.

## Architecture

| Layer | Description |
|-------|-------------|
| **LangGraph Layer** | Manages workflow execution and state propagation between nodes. |
| **Agent Layer** | Contains node functions implementing extraction, validation, DB updates, and notifications. |
| **Configuration Layer** | Loads API keys, initializes Groq models, and sets up database/email configurations.. |
| **Service Layer** | Handles LLM calls, database queries, and business rule validations. |
| **FastAPI Layer** | Exposes a REST API for catalog image upload and orchestrates workflow execution. |

---

## Prerequisites

- Python 3.10 or higher  
- Git
- MySQL (with access credentials)
- Groq API Key (for LLM inference)
- SMTP Account (for sending email reports)

---

## Installation & Setup

### Clone the Repository
```bash
git clone https://Sounak-Sarkar45/Supplier-Catalog-Ingestion-Agent.git
cd Supplier-Catalog-Ingestion-Agent
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
GROQ_API_KEY=<your_groq_api_key>

# LLM Models
LLM_EXTRACTION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_EMAIL_MODEL=llama-3.1-8b-instant
LLM_TEMPERATURE=0

# MySQL Configuration
MYSQL_HOST=<mysql_host>
MYSQL_USER=<mysql_user>
MYSQL_PASSWORD=<mysql_password>
MYSQL_DATABASE=<mysql_database>

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SENDER_EMAIL=<sender_email>
SENDER_PASSWORD=<app_password>
RECEIVER_EMAIL=<receiver_email>
```

### Database Setup

#### Create the following MySQL tables:

```bash
CREATE TABLE supplier_catalog_agent_dataset (
    Product_Name VARCHAR(255),
    SKU VARCHAR(50),
    Price FLOAT,
    Category VARCHAR(100),
    Supplier VARCHAR(100)
);

CREATE TABLE supplier_catalog_details (
    Date VARCHAR(50),
    Product_Name VARCHAR(255),
    SKU VARCHAR(50),
    Description TEXT,
    Category VARCHAR(100),
    Price VARCHAR(50),
    MOQ VARCHAR(50),
    Specification TEXT,
    Availability_Status VARCHAR(50),
    Supplier VARCHAR(100),
    Phone VARCHAR(50),
    Mail VARCHAR(100),
    Suggested_Description TEXT,
    Status VARCHAR(50)
);
```

### Run the Application
#### Start the FastAPI app:
```bash
uvicorn main:app --reload
```
Access API at: http://127.0.0.1:8000/

### API Endpoints
### Catalog Processing Workflow
| Method | Endpoint                | Description                                  |
| ------ | ----------------------- | -------------------------------------------- |
| POST   | `/process_catalog_image/` | Uploads a supplier catalog image and triggers the LangGraph workflow. |

Example Request :
```POST
{
  "file": "image.png"
}
```
Example Response:
```json
{
    "status": "Success",
    "suggested_status": "Pending Review",
    "flags": [
        "Price Out of Range",
        "Discontinued Model"
    ],
    "extracted_data": {
        "Date": "2025-10-27 15:49:06",
        "Product_Name": "Triple-buffered asynchronous model",
        "SKU": "SKU-9990",
        "Price": 245.3,
        "MOQ": 25,
        "Availability": "Discontinued",
        "Suggested_Factors": "Price Out of Range, Discontinued Model",
        "Suggested_Status": "Pending Review"
    },
    "database_entry": {
        "Date": "10/27/2025, 3:49:06 PM UTC",
        "Product_Name": "Triple-buffered asynchronous model",
        "SKU": "SKU-9990",
        "Description": "Walk pull majority necessary cut red hospital.",
        "Category": "Electronics",
        "Price": "$245.30",
        "MOQ": 25,
        "Specification": "Color: DarkOliveGreen, Power: 20W, Material: Metal, Warranty: 9 months",
        "Availability_Status": "Discontinued",
        "Supplier": "Brown-Livingston",
        "Phone": "value not provided",
        "Mail": "value not provided",
        "Suggested_Description": "Price Out of Range, Discontinued Model",
        "Status": "Pending Review"
    },
    "summary": "Catalog item processed. Status: Pending Review. Email generation attempted."
}
```

### Usage Examples

- Upload a supplier catalog image through `/process_catalog_image/`
- The pipeline executes:
  1. Extraction → Fields parsed from image using multimodal Groq LLM
  2. Validation → Business rules check historical deviations
  3. Database Update → Inserts processed record into MySQL
  4. Email Notification → Sends HTML summary report to procurement team

### Configuration

#### Environmental Variables

| Variable | Description |
| :--- | :--- |
| `GROQ_API_KEY` | Groq LLM API key. |
| `LLM_EXTRACTION_MODEL` | Model used for catalog data extraction. |
| `LLM_EMAIL_MODEL` | Model used for email generation. |
| `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | MySQL connection parameters. |
| `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECEIVER_EMAIL` | SMTP email configuration parameters. |

### Release Notes
#### v1.0.0

- End-to-end supplier catalog automation
- Groq LLM integration for multimodal extraction
- MySQL + SMTP connectivity
- FastAPI endpoint for real-time catalog ingestion
