# App Server Guide

This guide explains how to run the FastAPI server in this repository.

## Prerequisites

- Python 3.10+
- pip

## 1) Install Dependencies

Run these commands from the repository root:

```powershell
cd D:\Fungus\fungus
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you use Git Bash:

```bash
cd /d/Fungus/fungus
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2) Run the Server

From repository root:

```powershell
uvicorn app.main:app --reload
```

The API starts at:

- http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 3) Run Tests

```powershell
python -m pytest tests/test_api.py -v
```

## 4) Data Storage

- Data is stored in JSON files under `app/storage/`.
- No external database setup is required for local development.
- Missing storage files are created automatically on first write.

## Common Issues

- If `uvicorn` is not found, ensure virtual environment is activated.
- If imports fail, run commands from repository root (`D:\Fungus\fungus`).
