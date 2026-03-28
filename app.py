from flask import Flask, render_template, jsonify, request as flask_request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

# Mail.tm configuration
BASE_URL = 'https://api.mail.tm'
EMAIL_ADDRESS = os.getenv('MAIL_TM_EMAIL')
PASSWORD = os.getenv('MAIL_TM_PASSWORD')


class MailTM:
    def __init__(self, base_url=None, email=None, password=None):
        self.base_url = base_url or BASE_URL
        self.email = email or EMAIL_ADDRESS
        self.password = password or PASSWORD
        self.token = None
        self.account_id = None
        self.authenticate()

    def _auth_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def authenticate(self):
        """POST /token - Authenticate and obtain a bearer token."""
        url = f'{self.base_url}/token'
        payload = {
            'address': self.email,
            'password': self.password
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        self.token = data['token']
        self.account_id = data.get('id')

    def get_domains(self):
        """GET /domains - List available email domains."""
        url = f'{self.base_url}/domains'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['hydra:member']

    def get_account(self):
        """GET /me - Get current account information."""
        url = f'{self.base_url}/me'
        response = requests.get(url, headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    def delete_account(self, account_id):
        """DELETE /accounts/{id} - Delete an account."""
        url = f'{self.base_url}/accounts/{account_id}'
        response = requests.delete(url, headers=self._auth_headers())
        response.raise_for_status()

    def get_messages(self, page=1):
        """GET /messages - List messages with pagination."""
        url = f'{self.base_url}/messages'
        params = {'page': page} if page > 1 else {}
        response = requests.get(url, headers=self._auth_headers(), params=params)
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
                'intro': msg.get('text', '')[:100] + '...' if msg.get('text') else '(No preview available)',
                'seen': msg.get('seen', False)
            })
        return formatted_messages

    def get_message_content(self, message_id):
        """GET /messages/{id} - Get full message content."""
        url = f'{self.base_url}/messages/{message_id}'
        response = requests.get(url, headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    def delete_message(self, message_id):
        """DELETE /messages/{id} - Delete a message."""
        url = f'{self.base_url}/messages/{message_id}'
        response = requests.delete(url, headers=self._auth_headers())
        response.raise_for_status()

    def mark_message_as_read(self, message_id):
        """PATCH /messages/{id} - Mark a message as read."""
        url = f'{self.base_url}/messages/{message_id}'
        response = requests.patch(
            url,
            headers={**self._auth_headers(), 'Content-Type': 'merge-patch+json'},
            json={'seen': True}
        )
        response.raise_for_status()
        return response.json()


def create_app(mail_client=None):
    """Application factory for testing and production use."""
    application = Flask(__name__)
    CORS(application)
    application.secret_key = os.getenv('FLASK_SECRET_KEY')
    application.config['MAIL_TM_EMAIL'] = EMAIL_ADDRESS

    if mail_client is None:
        mail_client = MailTM()  # pragma: no cover
    application.mail_client = mail_client

    @application.route('/')
    def index():
        try:
            messages = application.mail_client.get_messages()
            return render_template('index.html', messages=messages)
        except Exception as e:
            return render_template('error.html', error=str(e))

    @application.route('/message/<message_id>')
    def get_message(message_id):
        try:
            message = application.mail_client.get_message_content(message_id)
            return jsonify(message)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/message/<message_id>', methods=['DELETE'])
    def delete_message(message_id):
        try:
            application.mail_client.delete_message(message_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/message/<message_id>/read', methods=['POST'])
    def mark_message_read(message_id):
        try:
            result = application.mail_client.mark_message_as_read(message_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/refresh')
    def refresh_messages():
        try:
            page = flask_request.args.get('page', 1, type=int)
            messages = application.mail_client.get_messages(page=page)
            return jsonify(messages)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/domains')
    def get_domains():
        try:
            domains = application.mail_client.get_domains()
            return jsonify(domains)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/account')
    def get_account():
        try:
            account = application.mail_client.get_account()
            return jsonify(account)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return application


if __name__ == '__main__':
    mail_client = MailTM()
    app = create_app(mail_client)
    app.run(host='0.0.0.0', port=8000, debug=True) 