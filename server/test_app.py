# In server/test_app.py


import pytest
from unittest.mock import MagicMock
from server.app import app

def test_health_check():
    """
    Tests the /api/health endpoint to ensure it returns a 200 OK status
    and a JSON response with a 'status' of 'healthy'.
    """
    # Create a test client using the Flask application
    client = app.test_client()

    # Make a GET request to the health check endpoint
    response = client.get('/api/health')

    # Assert that the HTTP status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response is JSON
    assert response.is_json

    # Parse the JSON response
    data = response.get_json()

    # Assert that the 'status' key in the JSON is 'healthy'
    assert data['status'] == 'healthy'
    
    def test_get_hotels(mocker):
        """
        Tests the GET /api/hotels endpoint, mocking the database connection.
        """
        # 1. Define the fake data we want our mock database to return.
        #    It must match the structure of a real database row.
        mock_hotel_data = {
            'id': 1,
            'hotel_name': 'Test Hotel',
            'location': 'Testville, USA',
            'total_rooms': 150,
            'base_occupancy': 75,
            'min_price': 100,
            'max_price': 400,
            'star_rating': 4,
            'auto_mode': 1,
            'created_at': '2025-01-01 12:00:00'
        }
    
        # 2. Use the 'mocker' fixture to find the REAL get_db_connection
        #    in your app and replace it with a mock object.
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [mock_hotel_data]  # Tell the mock cursor what to return
        mock_conn.cursor.return_value = mock_cursor
    
        # The 'patch' function is the key to mocking.
        mocker.patch('server.app.get_db_connection', return_value=mock_conn)
    
        # 3. Now, run the test. When the code inside manage_hotels calls
        #    get_db_connection, it will get our MOCK instead of the real one.
        client = app.test_client()
        response = client.get('/api/hotels')
    
        # 4. Assert that the response is correct based on our mock data.
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['hotels']) == 1
        assert data['hotels'][0]['hotelName'] == 'Test Hotel'
        assert data['hotels'][0]['totalRooms'] == 150