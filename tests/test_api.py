import pytest
from fastapi.testclient import TestClient
from app import app
from database.security import auth, verify_token
from database import models
import os

client = TestClient(app)

@pytest.fixture
def auth_headers():
    # Register and get token for a test user
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpass", "email": "test@example.com"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_register_user(client, db_session):
    response = client.post(
        "/register",
        json={"username": "newuser", "password": "newpass", "email": "new@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token is valid
    user = verify_token(data["access_token"], db_session)
    assert user is not None
    assert user.username == "newuser"

def test_login_user(client, db_session):
    # First register a user
    client.post(
        "/register",
        json={"username": "loginuser", "password": "loginpass", "email": "login@example.com"}
    )
    
    # Then try to login
    response = client.post(
        "/token",
        json={"username": "loginuser", "password": "loginpass", "email": "login@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token is valid
    user = verify_token(data["access_token"], db_session)
    assert user is not None
    assert user.username == "loginuser"

def test_login_wrong_password(client):
    # First register a user
    client.post(
        "/register",
        json={"username": "wrongpass", "password": "correctpass", "email": "wrong@example.com"}
    )
    
    # Try to login with wrong password
    response = client.post(
        "/token",
        json={"username": "wrongpass", "password": "wrongpass", "email": "wrong@example.com"}
    )
    assert response.status_code == 401

def test_search_lyrics(client):
    response = client.get("/search_lyrics?q=Bohemian%20Rhapsody")
    assert response.status_code == 200
    assert "results" in response.json()

def test_analyze_lyrics(client):
    response = client.get("/analyze_lyrics?record_id=12345&track=Test%20Song&artist=Test%20Artist")
    assert response.status_code == 200
    assert "analysis" in response.json()
    assert "lyrics" in response.json()

def test_create_comment(client, auth_headers, db_session):
    # Create a test song first
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    response = client.post(
        f"/api/songs/{test_song.id}/comments",
        headers=auth_headers,
        json={"content": "Test comment", "song_id": test_song.id}
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Test comment"

def test_increment_view_count(client, auth_headers, db_session):
    # Create a test song first
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    response = client.post(
        f"/api/songs/{test_song.id}/view",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "View count updated successfully"

def test_get_most_discussed(client, db_session):
    # Create test songs with comments
    for i in range(3):
        song = models.Song(
            title=f"Test Song {i}",
            artist="Test Artist",
            lyrics=f"Test lyrics {i}",
            view_count=0
        )
        db_session.add(song)
        db_session.commit()
        
        # Add comments to the song
        for j in range(i + 1):  # Song 0 gets 1 comment, Song 1 gets 2 comments, etc.
            comment = models.Comment(
                song_id=song.id,
                user_id=1,  # Use a valid user ID
                content=f"Test comment {j}"
            )
            db_session.add(comment)
        db_session.commit()
    
    response = client.get("/api/mostDiscussed?page=1&size=10")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()
    assert "size" in response.json()
    assert "pages" in response.json()
    
    # Verify the order (most commented songs first)
    items = response.json()["items"]
    assert len(items) > 0
    assert items[0]["title"] == "Test Song 2"  # Should have the most comments

def test_get_most_viewed(client, db_session):
    # Create test songs with different view counts
    for i in range(3):
        song = models.Song(
            title=f"Test Song {i}",
            artist="Test Artist",
            lyrics=f"Test lyrics {i}",
            view_count=i * 10  # Different view counts
        )
        db_session.add(song)
    db_session.commit()
    
    response = client.get("/api/mostViewed?page=1&size=10")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()
    assert "size" in response.json()
    assert "pages" in response.json()
    
    # Verify the order (most viewed songs first)
    items = response.json()["items"]
    assert len(items) > 0
    assert items[0]["title"] == "Test Song 2"  # Should have the most views

def test_rate_limiting(client):
    # Temporarily enable rate limiting for this test
    os.environ["ENV"] = "development"
    
    # Make multiple requests quickly
    for _ in range(101):  # Exceed the rate limit
        client.get("/")
    
    # The last request should be rate limited
    response = client.get("/")
    assert response.status_code == 429
    
    # Reset environment
    os.environ["ENV"] = "test"

def test_create_anonymous_comment(client, db_session):
    # Create a test song first
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    response = client.post(
        f"/api/songs/{test_song.id}/comments",
        json={"content": "Anonymous comment", "song_id": test_song.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Anonymous comment"
    assert data["user_id"] is None
    assert data["ip_address"] is not None

def test_upvote_comment(client, db_session):
    # Create a test song and comment
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    test_comment = models.Comment(
        song_id=test_song.id,
        content="Test comment",
        upvote_count=0
    )
    db_session.add(test_comment)
    db_session.commit()
    
    # Try to upvote
    response = client.post(f"/api/comments/{test_comment.id}/upvote")
    assert response.status_code == 200
    
    # Try to upvote again (should fail)
    response = client.post(f"/api/comments/{test_comment.id}/upvote")
    assert response.status_code == 400

def test_delete_comment(client, db_session):
    # Create a test song and comment
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    # Create comment with the same IP as the test client
    test_comment = models.Comment(
        song_id=test_song.id,
        content="Test comment",
        ip_address="testclient"  # Use a known IP for testing
    )
    db_session.add(test_comment)
    db_session.commit()
    
    # Try to delete the comment
    response = client.delete(f"/api/comments/{test_comment.id}")
    assert response.status_code == 200
    
    # Verify comment is deleted
    deleted_comment = db_session.query(models.Comment).filter(
        models.Comment.id == test_comment.id
    ).first()
    assert deleted_comment is None

def test_upvote_threshold_trigger(client, db_session):
    # Create a test song and comment
    test_song = models.Song(
        title="Test Song",
        artist="Test Artist",
        lyrics="Test lyrics",
        view_count=0
    )
    db_session.add(test_song)
    db_session.commit()
    
    test_comment = models.Comment(
        song_id=test_song.id,
        content="Test comment",
        upvote_count=9  # One less than threshold
    )
    db_session.add(test_comment)
    db_session.commit()
    
    # Create initial analysis
    initial_analysis = models.Analysis(
        song_id=test_song.id,
        analysis_data='{"overallHeadline": "Test", "songTitle": "Test Song", "artist": "Test Artist", "introduction": "Test", "sectionAnalyses": [], "conclusion": "Test"}',
        version=1
    )
    db_session.add(initial_analysis)
    db_session.commit()
    
    # Upvote to reach threshold
    response = client.post(f"/api/comments/{test_comment.id}/upvote")
    assert response.status_code == 200
    
    # Verify new analysis was created
    new_analysis = db_session.query(models.Analysis).filter(
        models.Analysis.song_id == test_song.id,
        models.Analysis.version == 2
    ).first()
    assert new_analysis is not None 