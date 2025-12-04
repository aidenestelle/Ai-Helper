import requests
import config
import settings_manager

def send_query(text, image_bytes, complexity="Mid", session_id=None):
    """
    Sends the text query and image to the n8n webhook.
    
    Args:
        text (str): The user's question.
        image_bytes (bytes): The screenshot image data.
        complexity (str): The complexity level (Low, Mid, High).
        session_id (str): The session ID for context.
        
    Returns:
        str: The response text from the webhook.
    """
    url = settings_manager.get_webhook_url()
    
    files = {}
    if image_bytes:
        files['screenshot'] = ('screenshot.png', image_bytes, 'image/png')
        
    data = {
        'query': text,
        'complexity': complexity,
        'response_format': 'markdown'
    }
    if session_id:
        data['sessionId'] = session_id
    
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        
        # Assuming the webhook returns a JSON with an 'answer' or 'text' field, 
        # or just plain text. Adjust based on actual n8n workflow.
        try:
            json_response = response.json()
            return json_response.get('output', json_response.get('text', str(json_response)))
        except ValueError:
            return response.text
            
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
