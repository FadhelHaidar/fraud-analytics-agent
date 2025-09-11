# Project Setup Guide

This guide will help you set up the environment, run the databases, ingest data, and start the backend and frontend applications.

---

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.12
- pip
- Docker
- Docker Compose

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 1. Prepare the Environment Variables

Create a `.env` file inside the `app/` folder:

```
app/
  └── .env
```

Add the following variables to your `.env` file:

```env
GROQ_API_KEY=<your_api_key>
GROQ_API_URL=https://api.groq.com/openai/v1

MISTRAL_API_KEY=<your_api_key>

QDRANT_URL=http://localhost:6333  # Local database
POSTGRES_URL=postgresql://myuser:mypassword@localhost:5432/mydb  # Local PostgreSQL
```

> 🔑 Replace `<your_api_key>` and database credentials with your actual values.

---

## 2. Run the Databases

Start the databases using Docker Compose:

```bash
cd docker
docker compose up
```

This will spin up both Qdrant and PostgreSQL services.

---

## 3. Ingest the Data

1. Navigate to the **notebook** folder.
2. Run the following Jupyter notebooks in order:
   - `sql_data_ingestion.ipynb` → for relational database ingestion.
   - `vector_data_ingestion.ipynb` → for vector database ingestion.  
     ⚠️ Make sure to **uncomment the `vanna train` cell** before running.

---

## 4. Run the Backend and Frontend

From the `app/` folder, start both services:

```bash
# Run backend
fastapi run main.py  

# Run frontend
streamlit run streamlit_app.py
```

> ⚠️ **Do not change the FastAPI port**. The frontend expects the backend to run on the default `8000` port.

---

✅ You are now ready to use the system!
