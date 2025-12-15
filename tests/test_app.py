"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Basketball Team": {
            "description": "Competitive basketball team for varsity competition",
            "schedule": "Mondays, Wednesdays, Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        },
        "Soccer Team": {
            "description": "Competitive soccer team for fall and spring seasons",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        },
        "Art Club": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Drama Club": {
            "description": "Perform in school plays and theatrical productions",
            "schedule": "Mondays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Debate Club": {
            "description": "Develop critical thinking and public speaking skills",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": []
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear current activities and reset
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Chess Club" in data
        assert len(data) == 9
    
    def test_activities_have_required_fields(self, client, reset_activities):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
    
    def test_chess_club_has_participants(self, client, reset_activities):
        """Test that Chess Club has pre-populated participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity(self, client, reset_activities):
        """Test signing up for an activity"""
        email = "john.doe@mergington.edu"
        activity = "Basketball Team"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_updates_participants(self, client, reset_activities):
        """Test that signup adds student to participants list"""
        email = "jane.smith@mergington.edu"
        activity = "Soccer Team"
        
        # Verify student is not in list
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify student is now in list
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that signing up twice returns an error"""
        email = "duplicate@mergington.edu"
        activity = "Art Club"
        
        # First signup
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Second signup (should fail)
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_activity_full(self, client, reset_activities):
        """Test signing up for an activity that is full"""
        activity = "Chess Club"
        
        # Chess Club has max 12 participants and currently has 2
        # Fill it up to capacity
        for i in range(10):  # Add 10 more to reach 12
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Next signup should fail
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregister:
    """Test the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_from_activity(self, client, reset_activities):
        """Test unregistering a student from an activity"""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify student is signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
    
    def test_unregister_updates_participants(self, client, reset_activities):
        """Test that unregister removes student from participants list"""
        activity = "Programming Class"
        email = "emma@mergington.edu"
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify student is removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        response = client.post(
            "/activities/Fake Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregistering a student who isn't signed up"""
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
