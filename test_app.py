import unittest
from unittest.mock import patch, Mock
from app import get_lyrics_by_id  # Ensure this is the correct import from your app

class TestGetLyricsById(unittest.TestCase):
    
    @patch('app.requests.get')
    def test_valid_id(self, mock_get):
        """Test API response for a valid song ID"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "lyrics": {  # Check if "lyrics" is the correct key in your API response
                "plainLyrics": "Sample lyrics here...",
                "html": "<p>Sample lyrics here...</p>"
            }
        }
        mock_get.return_value = mock_response

        song_id = 12345
        result = get_lyrics_by_id(song_id)

        self.assertIn('plainLyrics', result)
        self.assertIn('html', result)
        self.assertEqual(result['plainLyrics'], "Sample lyrics here...")
        self.assertEqual(result['html'], "<p>Sample lyrics here...</p>")

    @patch('app.requests.get')
    def test_invalid_id(self, mock_get):
        """Test API response for an invalid song ID (400 Bad Request)"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"message":"Invalid ID"}'
        mock_get.return_value = mock_response

        song_id = -1
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 400 from Genius lyrics API", str(context.exception))

    @patch('app.requests.get')
    def test_nonexistent_id(self, mock_get):
        """Test API response for a nonexistent song ID (404 Not Found)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = '{"message":"Lyrics not found"}'
        mock_get.return_value = mock_response

        song_id = 999999  # Assuming this ID does not exist
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 404 from Genius lyrics API", str(context.exception))

    @patch('app.requests.get')
    def test_rate_limit_exceeded(self, mock_get):
        """Test API response when rate limit is exceeded (429 Too Many Requests)"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = '{"message":"Too many requests"}'
        mock_get.return_value = mock_response

        song_id = 12345
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 429 from Genius lyrics API", str(context.exception))

    @patch('app.requests.get')
    def test_unexpected_response_format(self, mock_get):
        """Test API response when the format is incorrect"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"unexpectedKey": "unexpectedValue"}  # Simulate unexpected response

        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(12345)

        self.assertIn("Unexpected response format", str(context.exception))  # ✅ Updated assertion


if __name__ == '__main__':
    unittest.main()
