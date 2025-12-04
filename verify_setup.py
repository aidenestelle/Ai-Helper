import screenshot_utils
import n8n_client
import config
from unittest.mock import patch, MagicMock
import sys

def test_screenshot():
    print("Testing screenshot capture...")
    try:
        img = screenshot_utils.capture_screen()
        print(f"Screenshot captured successfully. Size: {img.size}")
        
        img_bytes = screenshot_utils.capture_screen_bytes()
        print(f"Screenshot bytes captured. Length: {len(img_bytes)}")
    except Exception as e:
        print(f"FAILED: Screenshot capture failed: {e}")
        return False
    return True

def test_n8n_client_mock():
    print("\nTesting n8n client (Mocked)...")
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'output': 'This is a mocked response from n8n.'}
        mock_post.return_value = mock_response
        
        response = n8n_client.send_query("Test query", b"fake_image_data")
        
        if response == 'This is a mocked response from n8n.':
            print("n8n client logic verified (Mocked).")
        else:
            print(f"FAILED: Unexpected response: {response}")
            return False
    return True

if __name__ == "__main__":
    print("Running verification checks...")
    if test_screenshot() and test_n8n_client_mock():
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed.")
