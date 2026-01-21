"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Save original state
    original_state = {
        k: {"participants": v["participants"].copy()} 
        for k, v in activities.items()
    }
    
    yield
    
    # Restore original state
    for key in activities:
        activities[key]["participants"] = original_state[key]["participants"].copy()


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Soccer Club" in data
        assert "Art Club" in data

    def test_activities_have_required_fields(self, client):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_initial_participants(self, client):
        """Test that some activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have initial participants
        assert len(data["Chess Club"]["participants"]) > 0
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that duplicate signup is prevented"""
        # First signup
        client.post(
            "/activities/Basketball%20Team/signup?email=student@mergington.edu"
        )
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Basketball%20Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the list"""
        email = "newstudent@mergington.edu"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Art Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Art%20Club/signup?email=" + email
        )
        
        # Check count increased
        response2 = client.get("/activities")
        new_count = len(response2.json()["Art Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response2.json()["Art Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister"""
        # First signup
        client.post(
            "/activities/Drama%20Club/signup?email=student@mergington.edu"
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Drama%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregistered" in data["message"].lower() or "Unregistered" in data["message"]

    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregister of student not signed up"""
        response = client.delete(
            "/activities/Basketball%20Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/NonExistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        email = "student@mergington.edu"
        activity = "Debate%20Team"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify they're signed up
        response1 = client.get("/activities")
        assert email in response1.json()["Debate Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify they're removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Debate Team"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307


class TestIntegration:
    """Integration tests for full workflows"""

    def test_signup_and_unregister_workflow(self, client, reset_activities):
        """Test complete signup and unregister workflow"""
        email = "integration@mergington.edu"
        activity = "Chess%20Club"
        
        # Get initial participant count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify count increased
        response2 = client.get("/activities")
        after_signup_count = len(response2.json()["Chess Club"]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify count back to initial
        response3 = client.get("/activities")
        final_count = len(response3.json()["Chess Club"]["participants"])
        assert final_count == initial_count

    def test_multiple_signups(self, client, reset_activities):
        """Test multiple students signing up for same activity"""
        activity = "Math%20Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Math Club"]["participants"])
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are signed up
        response_final = client.get("/activities")
        final_count = len(response_final.json()["Math Club"]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in response_final.json()["Math Club"]["participants"]
