"""
Tests for the High School Management System API

Tests for all endpoints including:
- GET /activities
- POST /activities/{activity_name}/signup
- DELETE /activities/{activity_name}/participants/{email}
- GET / (redirect)

Following AAA (Arrange-Act-Assert) testing pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
    
    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        # Arrange
        test_email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "message" in response_data
        assert test_email in response_data["message"]
        assert activity_name in response_data["message"]
    
    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds participant to activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        # Get initial state
        response_before = client.get("/activities")
        initial_participants = response_before.json()[activity_name]["participants"]
        initial_count = len(initial_participants)
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert
        response_after = client.get("/activities")
        final_participants = response_after.json()[activity_name]["participants"]
        final_count = len(final_participants)
        
        assert email in final_participants
        assert final_count == initial_count + 1
    
    def test_signup_for_nonexistent_activity_returns_404(self):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        invalid_activity = "Fake Activity"
        test_email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup?email={test_email}"
        )
        
        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "Activity not found" in response_data["detail"]
    
    def test_signup_duplicate_student_returns_400(self):
        """Test that duplicate signup returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert "already signed up" in response_data["detail"]


class TestRemoveParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_success(self):
        """Test successful removal of participant"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "Removed" in response_data["message"]
    
    def test_remove_participant_from_activity(self):
        """Test that participant is actually removed from activity"""
        # Arrange
        email = "daniel@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Get initial state
        response_before = client.get("/activities")
        initial_participants = response_before.json()[activity_name]["participants"]
        initial_count = len(initial_participants)
        assert email in initial_participants
        
        # Act
        client.delete(f"/activities/{activity_name}/participants/{email}")
        
        # Assert
        response_after = client.get("/activities")
        final_participants = response_after.json()[activity_name]["participants"]
        final_count = len(final_participants)
        
        assert email not in final_participants
        assert final_count == initial_count - 1
    
    def test_remove_from_nonexistent_activity_returns_404(self):
        """Test removal from non-existent activity returns 404"""
        # Arrange
        invalid_activity = "Fake Activity"
        test_email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/participants/{test_email}"
        )
        
        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "Activity not found" in response_data["detail"]
    
    def test_remove_nonexistent_participant_returns_404(self):
        """Test removal of participant not in activity returns 404"""
        # Arrange
        email = "notreal@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "not signed up" in response_data["detail"]


class TestActivitySignupLimits:
    """Tests for activity participant limits"""
    
    def test_activity_respects_max_participants(self):
        """Test that activities have max_participants field"""
        # Arrange - No special setup needed
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert activity_data["max_participants"] > 0
            assert len(activity_data["participants"]) <= activity_data["max_participants"]
