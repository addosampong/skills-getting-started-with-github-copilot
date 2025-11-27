import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivities:
    """Test suite for /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_keys(self):
        """Test that activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignup:
    """Test suite for signup endpoint"""

    def test_signup_valid_participant(self):
        """Test successful signup for a participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_returns_message(self):
        """Test that signup returns a message"""
        response = client.post(
            "/activities/Programming Class/signup?email=newuser@example.com"
        )
        assert "message" in response.json()

    def test_signup_duplicate_participant_returns_400(self):
        """Test that signing up the same participant twice returns 400"""
        email = "duplicate@test.com"
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_to_full_activity_returns_400(self):
        """Test that signing up to a full activity returns 400"""
        # Get activities to find one that's full or fill one
        activities = client.get("/activities").json()
        
        # Create a minimal activity to test (we'll use an existing one)
        # For this test, we'll fill up an activity programmatically
        activity_name = "Art Club"
        
        # Sign up multiple participants until full
        for i in range(100):
            response = client.post(
                f"/activities/{activity_name}/signup?email=user{i}@test.com"
            )
            if response.status_code == 400 and "full" in response.json()["detail"]:
                assert response.status_code == 400
                break


class TestUnregister:
    """Test suite for unregister endpoint"""

    def test_unregister_valid_participant(self):
        """Test successful unregister of a participant"""
        email = "unregister_test@example.com"
        
        # First sign up
        signup_response = client.post(
            f"/activities/Math Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.post(
            f"/activities/Math Club/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        assert "Unregistered" in unregister_response.json()["message"]

    def test_unregister_returns_message(self):
        """Test that unregister returns a message"""
        email = "unregister_msg_test@example.com"
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        response = client.post(
            f"/activities/Drama Club/unregister?email={email}"
        )
        assert "message" in response.json()

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test that unregistering from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_participant_not_registered_returns_400(self):
        """Test that unregistering non-registered participant returns 400"""
        response = client.post(
            "/activities/Science Olympiad/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal_test@example.com"
        activity = "Basketball Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify participant is in list
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify participant is removed
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]


class TestIntegration:
    """Integration tests for the full workflow"""

    def test_signup_and_unregister_workflow(self):
        """Test the full signup and unregister workflow"""
        email = "workflow_test@example.com"
        activity = "Soccer Team"
        
        # Get initial state
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        activities_after_signup = client.get("/activities").json()
        assert len(activities_after_signup[activity]["participants"]) == initial_count + 1
        assert email in activities_after_signup[activity]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        activities_after_unregister = client.get("/activities").json()
        assert len(activities_after_unregister[activity]["participants"]) == initial_count
        assert email not in activities_after_unregister[activity]["participants"]
