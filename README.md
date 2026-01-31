# Survey Backend Service

A simple backend service for creating and answering surveys with role-based access control, built with FastAPI and SQLAlchemy.

## Overview

This project implements a survey system where:
- **Admins** can create surveys, add questions, view responses, and share surveys with other admins.
- **Answerers** can view available surveys, submit responses, and view their own history.

## Setup & specific instructions

1.  **Prerequisites**: Python 3.9+
2.  **Installation**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Using the provided virtual environment is recommended)*

## Running the Application

Start the server:
```bash
python -m uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Interactive API documentation (Swagger UI) is automatically generated and available at:
- **http://127.0.0.1:8000/docs**

## Verification

A demo script is provided to verify the core workflows:
```bash
python demo.py
```

## Design Decisions & Trade-offs

- **Framework**: Chosen **FastAPI** for its speed, automatic OpenAPI generation, and ease of use with Pydantic schemata.
- **Database**: **SQLite** was selected for simplicity and portability (zero-conf). **SQLAlchemy** is used as the ORM to allow easy switching to Postgres/MySQL if needed.
- **Authentication**: As per requirements, a full auth system was out of scope. We assume authentication is handled upstream and trust `X-User-ID` and `X-Role` headers.
    - *mock dependency* `get_current_user` enforces these headers.
- **Data Model**:
    - `Survey` owns `Questions` and `Responses`.
    - `Responses` own `Answers`.
    - `SurveyShare` table handles many-to-many sharing relations between Surveys and Admin users.
- **Trade-offs**:
    - **No Authentication**: The system is insecure without an API gateway or proper auth middleware.
    - **No Pagination**: Large lists of responses might slow down the API.
    - **Sync vs Async**: Used synchronous SQLite drivers. For production high-concurrency, `aiosqlite` and `async` database sessions would be preferred.

## Project Structure

- `app/main.py`: Entry point, API routes, and dependency injection.
- `app/models.py`: Database models.
- `app/schemas.py`: Pydantic models for data validation.
- `app/crud.py`: Database access logic.
- `app/database.py`: DB connection setup.
- `demo.py`: Verification script.
