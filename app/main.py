from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Survey Backend")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock Auth Dependency
class UserContext:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role # "admin" or "answerer"

async def get_current_user(
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_role: str = Header("answerer", alias="X-Role")
):
    # Basic validation
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header missing")
    if x_role not in ["admin", "answerer"]:
        raise HTTPException(status_code=400, detail="Invalid X-Role. Must be 'admin' or 'answerer'")
    return UserContext(user_id=x_user_id, role=x_role)

@app.post("/surveys/", response_model=schemas.Survey)
def create_survey(
    survey: schemas.SurveyCreate, 
    db: Session = Depends(get_db), 
    user: UserContext = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create surveys")
    return crud.create_survey(db=db, survey=survey, owner_id=user.user_id)

@app.get("/surveys/", response_model=List[schemas.Survey])
def read_surveys(
    db: Session = Depends(get_db), 
    user: UserContext = Depends(get_current_user)
):
    return crud.get_surveys(db, user_id=user.user_id, role=user.role)

@app.post("/surveys/{survey_id}/questions/", response_model=schemas.Question)
def create_question_for_survey(
    survey_id: int, 
    question: schemas.QuestionCreate, 
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create questions")
    
    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if survey.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only add questions to surveys you own")
        
    return crud.add_question(db=db, survey_id=survey_id, question=question)

@app.get("/surveys/{survey_id}", response_model=schemas.Survey)
def read_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    # Both admins and answerers might need to see the survey structure
    # But access rules might differ. 
    # For simplicity, we allow viewing if you have list access.
    # We should strictly follow "Answerers can view surveys available to them"
    # Admin: own or shared.
    
    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if user.role == "admin":
        # Check ownership or share
        is_shared = False
        for share in survey.shares:
            if share.shared_user_id == user.user_id:
                is_shared = True
                break
        
        if survey.owner_id != user.user_id and not is_shared:
             raise HTTPException(status_code=403, detail="Access denied")
             
    # If answerer, assuming public availability as per list logic.

    return survey

@app.post("/surveys/{survey_id}/responses/", response_model=schemas.Response)
def submit_response(
    survey_id: int, 
    response: schemas.ResponseCreate, 
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    if user.role != "answerer":
        # Spec says "Answerers can submit responses". Doesn't explicitly forbid admins, 
        # but usually roles are distinct. I'll enforce answerer only for strictness, 
        # or maybe admins can answer too? "Answerer" is a role.
        # "The system has two user roles: Admin, Answerer". 
        # Let's enforce role == answerer to be precise.
        raise HTTPException(status_code=403, detail="Only answerers can submit responses")

    # Check if survey exists
    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    return crud.create_response(db=db, survey_id=survey_id, user_id=user.user_id, response_data=response)

@app.get("/my-responses/", response_model=List[schemas.Response])
def read_my_responses(
    db: Session = Depends(get_db), 
    user: UserContext = Depends(get_current_user)
):
    if user.role != "answerer":
         raise HTTPException(status_code=403, detail="Only answerers have 'my responses' in this context")
    return crud.get_responses_by_user(db, user_id=user.user_id)

@app.get("/surveys/{survey_id}/responses/", response_model=List[schemas.Response])
def read_survey_responses(
    survey_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view survey responses")
    
    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Check access
    is_shared = False
    for share in survey.shares:
        if share.shared_user_id == user.user_id:
            is_shared = True
            break
            
    if survey.owner_id != user.user_id and not is_shared:
        raise HTTPException(status_code=403, detail="Access denied to this survey's responses")
        
    return survey.responses

@app.get("/surveys/{survey_id}/aggregates")
def read_survey_aggregates(
    survey_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    # This is a bit extra but requested in "View simple aggregates"
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view aggregates")

    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Check access (reuse logic)
    is_shared = any(s.shared_user_id == user.user_id for s in survey.shares)
    if survey.owner_id != user.user_id and not is_shared:
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate basic aggregates
    # Total responses
    total_responses = len(survey.responses)
    
    # Per question stats
    stats = {}
    for q in survey.questions:
        q_stats = {"type": q.question_type, "count": 0}
        
        # Get all answers for this question
        answers = [a for r in survey.responses for a in r.answers if a.question_id == q.id]
        q_stats["count"] = len(answers)
        
        if q.question_type == "bool":
            true_count = sum(1 for a in answers if a.value.lower() == "true")
            false_count = sum(1 for a in answers if a.value.lower() == "false")
            q_stats["true"] = true_count
            q_stats["false"] = false_count
        elif q.question_type == "rank":
            # Just listing counts of each value for now, or avg if numeric
            # Assuming rank is numeric 1-N
            try:
                values = [int(a.value) for a in answers if a.value.isdigit()]
                if values:
                    q_stats["average"] = sum(values) / len(values)
            except:
                pass
        
        stats[q.id] = q_stats

    return {"total_responses": total_responses, "question_stats": stats}

@app.post("/surveys/{survey_id}/share", response_model=schemas.SurveyShareCreate)
def share_survey(
    survey_id: int,
    share: schemas.SurveyShareCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can share surveys")
        
    survey = crud.get_survey(db, survey_id=survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    if survey.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="Only the owner can share the survey")
        
    crud.share_survey(db, survey_id=survey_id, shared_user_id=share.shared_user_id)
    return share
