import unittest
from unittest.mock import patch
from app import get_lyrics_by_id

class TestGetLyricsById(unittest.TestCase):
    @patch('app.requests.get')
    def test_valid_id(self, mock_get):
        # Simulate a successful API response
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plainLyrics": "Sample lyrics here...",
            "html": "<p>Sample lyrics here...</p>"
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
        # Simulate a 400 Bad Request response
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 400
        mock_response.text = '{"message":"Invalid ID"}'
        mock_get.return_value = mock_response

        song_id = -1
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 400 from Genius lyrics API", str(context.exception))

    @patch('app.requests.get')
    def test_nonexistent_id(self, mock_get):
        # Simulate a 404 Not Found response
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 404
        mock_response.text = '{"message":"Lyrics not found"}'
        mock_get.return_value = mock_response

        song_id = 999999  # Assuming this ID does not exist
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 404 from Genius lyrics API", str(context.exception))

    @patch('app.requests.get')
    def test_rate_limit_exceeded(self, mock_get):
        # Simulate a 429 Too Many Requests response
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 429
        mock_response.text = '{"message":"Too many requests"}'
        mock_get.return_value = mock_response

        song_id = 12345
        with self.assertRaises(Exception) as context:
            get_lyrics_by_id(song_id)
        self.assertIn("Error 429 from Genius lyrics API", str(context.exception))

if __name__ == '__main__':
    unittest.main()