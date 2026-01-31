import requests
import sys
import time
import subprocess

# Start the server in a subprocess? Or assume it's running?
# For this script to be standalone "runnable code", it's best if it assumes the server is running 
# OR starts it. Let's assume the user starts it or we instruct them to.
# But for my own verification, I can try to start it.
# Let's keep it simple: assume server is at localhost:8000

BASE_URL = "http://127.0.0.1:8000"

def print_header(msg):
    print(f"\n{'='*50}\n{msg}\n{'='*50}")

def test_flow():
    # 1. Admin Create Survey
    print_header("1. Admin creating survey")
    headers_admin1 = {"X-User-ID": "admin1", "X-Role": "admin"}
    
    survey_data = {"title": "Employee Satisfaction"}
    resp = requests.post(f"{BASE_URL}/surveys/", json=survey_data, headers=headers_admin1)
    if resp.status_code != 200:
        print(f"Failed to create survey: {resp.text}")
        return
    survey = resp.json()
    survey_id = survey['id']
    print(f"Created Survey: {survey['title']} (ID: {survey_id})")

    # 2. Add Questions
    print_header("2. Admin adding questions")
    q1 = {"text": "How happy are you?", "ordering": 1, "question_type": "rank"}
    q2 = {"text": "Do you like remote work?", "ordering": 2, "question_type": "bool"}
    q3 = {"text": "Any feedback?", "ordering": 3, "question_type": "text"}
    
    for q in [q1, q2, q3]:
        r = requests.post(f"{BASE_URL}/surveys/{survey_id}/questions/", json=q, headers=headers_admin1)
        print(f"Added question: {q['text']} -> {r.status_code}")

    # 3. Answerer View Surveys
    print_header("3. Answerer viewing surveys")
    headers_ans1 = {"X-User-ID": "user1", "X-Role": "answerer"}
    r = requests.get(f"{BASE_URL}/surveys/", headers=headers_ans1)
    surveys = r.json()
    print(f"Available surveys for user1: {len(surveys)}")
    
    # 4. Submit Response
    print_header("4. Answerer submitting response")
    
    # Need question IDs
    r_survey = requests.get(f"{BASE_URL}/surveys/{survey_id}", headers=headers_ans1)
    questions = r_survey.json()['questions']
    q_ids = {q['text']: q['id'] for q in questions}
    
    response_data = {
        "answers": [
            {"question_id": q_ids["How happy are you?"], "value": "5"},
            {"question_id": q_ids["Do you like remote work?"], "value": "true"},
            {"question_id": q_ids["Any feedback?"], "value": "Great!"}
        ]
    }
    
    r = requests.post(f"{BASE_URL}/surveys/{survey_id}/responses/", json=response_data, headers=headers_ans1)
    print(f"Submission status: {r.status_code}")
    
    # 5. Admin View Responses
    print_header("5. Admin1 viewing responses")
    r = requests.get(f"{BASE_URL}/surveys/{survey_id}/responses/", headers=headers_admin1)
    responses = r.json()
    print(f"Total responses seen by admin1: {len(responses)}")
    
    # 6. Admin View Aggregates
    print_header("6. Admin1 viewing aggregates")
    r = requests.get(f"{BASE_URL}/surveys/{survey_id}/aggregates", headers=headers_admin1)
    print(f"Aggregates: {r.json()}")

    # 7. Access Control Check (Admin2 cannot see yet)
    print_header("7. Access Control Check (Admin2)")
    headers_admin2 = {"X-User-ID": "admin2", "X-Role": "admin"}
    r = requests.get(f"{BASE_URL}/surveys/{survey_id}/responses/", headers=headers_admin2)
    print(f"Admin2 access (before share): {r.status_code} (Expected 403)")

    # 8. Share Survey
    print_header("8. Share Survey")
    share_data = {"shared_user_id": "admin2"}
    r = requests.post(f"{BASE_URL}/surveys/{survey_id}/share", json=share_data, headers=headers_admin1)
    print(f"Share status: {r.status_code}")
    
    # 9. Admin2 View Shared
    print_header("9. Admin2 viewing shared survey")
    r = requests.get(f"{BASE_URL}/surveys/{survey_id}/responses/", headers=headers_admin2)
    print(f"Admin2 access (after share): {r.status_code} (Expected 200)")
    if r.status_code == 200:
        print(f"Responses seen by Admin2: {len(r.json())}")

if __name__ == "__main__":
    try:
        # Check if server is up
        requests.get(BASE_URL)
        test_flow()
    except requests.exceptions.ConnectionError:
        print("Server not running. Please run 'uvicorn app.main:app' in another terminal.")
