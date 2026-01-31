from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class AnswerCreate(BaseModel):
    question_id: int
    value: str

class Answer(AnswerCreate):
    id: int
    response_id: int

    class Config:
        from_attributes = True

class ResponseCreate(BaseModel):
    answers: List[AnswerCreate]

class Response(BaseModel):
    id: int
    survey_id: int
    user_id: str
    submitted_at: datetime
    answers: List[Answer] = []

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    text: str
    ordering: int
    question_type: str # "rank", "bool", "text"

class Question(QuestionCreate):
    id: int
    survey_id: int

    class Config:
        from_attributes = True

class SurveyShareCreate(BaseModel):
    shared_user_id: str

class SurveyCreate(BaseModel):
    title: str

class Survey(SurveyCreate):
    id: int
    owner_id: str
    created_at: datetime
    questions: List[Question] = []
    # We might not want to return responses by default in the list view

    class Config:
        from_attributes = True

class SurveyWithResponses(Survey):
    responses: List[Response] = []
