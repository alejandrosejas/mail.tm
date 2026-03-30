from flask import Flask, render_template, jsonify, request as flask_request, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import secrets
import string


# Load environment variables
load_dotenv()

# Mail.tm configuration
BASE_URL = 'https://api.mail.tm'


class MailTM:
    """Stateless wrapper around the Mail.tm API. Requires a token for authenticated calls."""

    def __init__(self, base_url=None, token=None):
        self.base_url = base_url or BASE_URL
        self.token = token

    def _auth_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    @staticmethod
    def get_domains(base_url=None):
        """GET /domains - List available email domains (no auth required)."""
        url = f'{base_url or BASE_URL}/domains'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['hydra:member']

    @staticmethod
    def create_account(address, password, base_url=None):
        """POST /accounts - Create a new account."""
        url = f'{base_url or BASE_URL}/accounts'
        response = requests.post(url, json={'address': address, 'password': password})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def authenticate(address, password, base_url=None):
        """POST /token - Authenticate and obtain a bearer token."""
        url = f'{base_url or BASE_URL}/token'
        response = requests.post(url, json={'address': address, 'password': password})
        response.raise_for_status()
        data = response.json()
        return data['token'], data.get('id')

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

        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg['id'],
                'subject': msg['subject'],
                'from': msg['from']['address'],
                'date': msg['createdAt'],
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


def _get_mail_client():
    """Build a MailTM client from the current session token."""
    token = session.get('token')
    if not token:
        return None
    return MailTM(token=token)


def _generate_password(length=16):
    """Generate a random password for new accounts."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def create_app():
    """Application factory."""
    application = Flask(__name__)
    CORS(application)
    application.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

    # --- Auth routes ---

    @application.route('/login', methods=['GET'])
    def login_page():
        if session.get('token'):
            return redirect(url_for('index'))
        return render_template('login.html')

    @application.route('/auth/domains', methods=['GET'])
    def auth_domains():
        """Return available domains for account creation."""
        try:
            domains = MailTM.get_domains()
            return jsonify(domains)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/auth/register', methods=['POST'])
    def auth_register():
        """Create a new Mail.tm account and log in."""
        data = flask_request.get_json()
        address = data.get('address', '').strip().lower()
        password = data.get('password') or _generate_password()

        if not address:
            return jsonify({'error': 'Email address is required'}), 400

        try:
            MailTM.create_account(address, password)
            token, account_id = MailTM.authenticate(address, password)
            session['token'] = token
            session['email'] = address
            session['account_id'] = account_id
            session['password'] = password
            return jsonify({'success': True, 'email': address})
        except requests.exceptions.HTTPError as e:
            error_msg = 'Account creation failed'
            try:
                error_data = e.response.json()
                if 'violations' in error_data:
                    error_msg = error_data['violations'][0].get('message', error_msg)
                elif 'detail' in error_data:
                    error_msg = error_data['detail']
            except (ValueError, KeyError, IndexError):
                pass
            return jsonify({'error': error_msg}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/auth/login', methods=['POST'])
    def auth_login():
        """Log in with existing Mail.tm credentials."""
        data = flask_request.get_json()
        address = data.get('address', '').strip().lower()
        password = data.get('password', '')

        if not address or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        try:
            token, account_id = MailTM.authenticate(address, password)
            session['token'] = token
            session['email'] = address
            session['account_id'] = account_id
            session['password'] = password
            return jsonify({'success': True, 'email': address})
        except requests.exceptions.HTTPError:
            return jsonify({'error': 'Invalid email or password'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/auth/logout', methods=['POST'])
    def auth_logout():
        session.clear()
        return jsonify({'success': True})

    # --- App routes (require auth) ---

    @application.route('/')
    def index():
        if not session.get('token'):
            return redirect(url_for('login_page'))
        try:
            client = _get_mail_client()
            messages = client.get_messages()
            return render_template('index.html', messages=messages, email=session.get('email'), password=session.get('password', ''))
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                session.clear()
                return redirect(url_for('login_page'))
            return render_template('error.html', error=str(e))
        except Exception as e:
            return render_template('error.html', error=str(e))

    @application.route('/message/<message_id>')
    def get_message(message_id):
        client = _get_mail_client()
        if not client:
            return jsonify({'error': 'Not authenticated'}), 401
        try:
            message = client.get_message_content(message_id)
            return jsonify(message)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/message/<message_id>', methods=['DELETE'])
    def delete_message(message_id):
        client = _get_mail_client()
        if not client:
            return jsonify({'error': 'Not authenticated'}), 401
        try:
            client.delete_message(message_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/message/<message_id>/read', methods=['POST'])
    def mark_message_read(message_id):
        client = _get_mail_client()
        if not client:
            return jsonify({'error': 'Not authenticated'}), 401
        try:
            result = client.mark_message_as_read(message_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/refresh')
    def refresh_messages():
        client = _get_mail_client()
        if not client:
            return jsonify({'error': 'Not authenticated'}), 401
        try:
            page = flask_request.args.get('page', 1, type=int)
            messages = client.get_messages(page=page)
            return jsonify(messages)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/domains')
    def get_domains():
        try:
            domains = MailTM.get_domains()
            return jsonify(domains)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @application.route('/account')
    def get_account():
        client = _get_mail_client()
        if not client:
            return jsonify({'error': 'Not authenticated'}), 401
        try:
            account = client.get_account()
            return jsonify(account)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return application


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
