from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="survey", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="survey", cascade="all, delete-orphan")
    shares = relationship("SurveyShare", back_populates="survey", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    text = Column(String)
    ordering = Column(Integer)
    # Types: "rank", "bool", "text"
    question_type = Column(String) 

    survey = relationship("Survey", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    user_id = Column(String, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    survey = relationship("Survey", back_populates="responses")
    answers = relationship("Answer", back_populates="response", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    # We'll store the answer as a string. 
    # For Rank: comma separated indices or similar. 
    # For Bool: "true"/"false". 
    # For Text: the text itself.
    value = Column(String) 

    response = relationship("Response", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class SurveyShare(Base):
    __tablename__ = "survey_shares"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    shared_user_id = Column(String, index=True)

    survey = relationship("Survey", back_populates="shares")
