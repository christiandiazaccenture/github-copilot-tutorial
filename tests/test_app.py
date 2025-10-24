"""
Tests for the Mergington High School API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_root_redirect():
    """Test that the root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    """Test that we can get the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check if we have activities in the response
    assert len(activities) > 0
    
    # Check the structure of an activity
    first_activity = next(iter(activities.values()))
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)

def test_signup_for_activity():
    """Test the signup process for activities"""
    activity_name = "Chess Club"
    test_email = "newstudent@mergington.edu"
    
    # First, ensure the student isn't already signed up
    response = client.get("/activities")
    activities = response.json()
    
    # If student is already in any activity, we'll get an error on signup
    for activity in activities.values():
        if test_email in activity["participants"]:
            pytest.skip("Test email already registered in an activity")
    
    # Try to sign up
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {test_email} for {activity_name}"
    
    # Verify the student was added
    response = client.get("/activities")
    activities = response.json()
    assert test_email in activities[activity_name]["participants"]

def test_signup_duplicate_error():
    """Test that a student cannot sign up for multiple activities"""
    activity_name = "Chess Club"
    test_email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 200
    
    # Second signup should fail
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()

def test_signup_nonexistent_activity():
    """Test signup for a non-existent activity"""
    response = client.post("/activities/NonexistentClub/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_from_activity():
    """Test that a student can unregister from an activity"""
    activity_name = "Chess Club"
    test_email = "tounregister@mergington.edu"
    
    # First, sign up the student
    response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
    assert response.status_code == 200
    
    # Then unregister them
    response = client.post(f"/activities/{activity_name}/unregister?email={test_email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {test_email} from {activity_name}"
    
    # Verify they were removed
    response = client.get("/activities")
    activities = response.json()
    assert test_email not in activities[activity_name]["participants"]

def test_unregister_not_registered():
    """Test unregistering a student who isn't registered"""
    response = client.post("/activities/Chess Club/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"].lower()