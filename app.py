from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Mail.tm configuration
BASE_URL = 'https://api.mail.tm'
EMAIL_ADDRESS = os.getenv('MAIL_TM_EMAIL')
PASSWORD = os.getenv('MAIL_TM_PASSWORD')

class MailTM:
    def __init__(self):
        self.token = None
        self.authenticate()

    def authenticate(self):
        url = f'{BASE_URL}/token'
        payload = {
            'address': EMAIL_ADDRESS,
            'password': PASSWORD
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        self.token = response.json()['token']

    def get_messages(self):
        url = f'{BASE_URL}/messages'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        messages = response.json()['hydra:member']
        
        # Format messages for display
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg['id'],
                'subject': msg['subject'],
                'from': msg['from']['address'],
                'date': datetime.fromisoformat(msg['createdAt'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'),
                'intro': msg.get('text', '')[:100] + '...' if msg.get('text') else '(No preview available)'
            })
        return formatted_messages

    def get_message_content(self, message_id):
        url = f'{BASE_URL}/messages/{message_id}'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

# Initialize MailTM
mail_client = MailTM()

@app.route('/')
def index():
    try:
        messages = mail_client.get_messages()
        return render_template('index.html', messages=messages)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/message/<message_id>')
def get_message(message_id):
    try:
        message = mail_client.get_message_content(message_id)
        return jsonify(message)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/refresh')
def refresh_messages():
    try:
        messages = mail_client.get_messages()
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 