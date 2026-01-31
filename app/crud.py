from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_survey(db: Session, survey: schemas.SurveyCreate, owner_id: str):
    db_survey = models.Survey(title=survey.title, owner_id=owner_id)
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    return db_survey

def get_surveys(db: Session, user_id: str = None, role: str = "answerer"):
    # If admin, can see own surveys + shared.
    if role == "admin":
        if not user_id:
             return [] # Should not happen if auth is enforced
        
        # Surveys owned by user OR shared with user
        # We can do a union or a complex query.
        # Simplest:
        return db.query(models.Survey).outerjoin(models.SurveyShare).filter(
            (models.Survey.owner_id == user_id) | (models.SurveyShare.shared_user_id == user_id)
        ).all()
    else:
        # Answerer sees all surveys? Spec says "View available surveys".
        # Assuming all surveys are public to answerers for this exercise.
        return db.query(models.Survey).all()

def get_survey(db: Session, survey_id: int):
    return db.query(models.Survey).filter(models.Survey.id == survey_id).first()

def add_question(db: Session, survey_id: int, question: schemas.QuestionCreate):
    db_question = models.Question(**question.dict(), survey_id=survey_id)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def create_response(db: Session, survey_id: int, user_id: str, response_data: schemas.ResponseCreate):
    # Create response entry
    db_response = models.Response(survey_id=survey_id, user_id=user_id)
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    # Create answers
    for ans in response_data.answers:
        db_answer = models.Answer(
            response_id=db_response.id,
            question_id=ans.question_id,
            value=ans.value
        )
        db.add(db_answer)
    
    db.commit()
    db.refresh(db_response)
    return db_response

def get_responses_by_user(db: Session, user_id: str):
    return db.query(models.Response).filter(models.Response.user_id == user_id).all()

def share_survey(db: Session, survey_id: int, shared_user_id: str):
    # Check if already shared
    existing = db.query(models.SurveyShare).filter_by(survey_id=survey_id, shared_user_id=shared_user_id).first()
    if existing:
        return existing
    
    share = models.SurveyShare(survey_id=survey_id, shared_user_id=shared_user_id)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share
