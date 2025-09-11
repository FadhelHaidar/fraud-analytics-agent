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

Create a `.env` file inside the `app/` the `notebook/`  folder:

```
app/
  └── .env
notebook/
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

# Project Information

This project is an advanced agent chatbot capable of retrieving non-structured information and querying relational databases.
It leverages the Groq API to access the `llama-4-maverick-17b-128e-instruct` Large Language Model (LLM) and utilizes Mistral's `codestral` for translating natural language into SQL queries.
The embedding model used here is `Qwen3-Embedding-0.6B` for performing semantic searches.
The project employs three key frameworks:
- **Langgraph/Langchain**: For developing the intelligent agent.
- **Vanna AI**: For handling the text-to-SQL conversion process.
- **Ragas**: For agent response evaluation and scoring.

# Code Information

The project consists of the following key files:
- **app.py**: Contains the endpoint code.
- **agent.py**: Handles the agent logic.
- **tools.py**: Includes the code for agent tools.
- **eval.py**: Evaluates agent responses using faithfulness metrics.
- **config.py**: Manages model, embedding, and database configurations.
- **streamlit.app**: The frontend application.
- **setting.py**: Loads and stores environment variables.
