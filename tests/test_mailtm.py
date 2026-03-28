import json
import unittest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from app import MailTM, create_app


# Sample API response fixtures
SAMPLE_TOKEN_RESPONSE = {
    'token': 'fake-jwt-token-123',
    'id': 'account-id-456'
}

SAMPLE_DOMAINS_RESPONSE = {
    'hydra:member': [
        {'id': 'domain-1', 'domain': 'ptct.net', 'isActive': True},
        {'id': 'domain-2', 'domain': 'examp.net', 'isActive': True}
    ]
}

SAMPLE_ACCOUNT_RESPONSE = {
    'id': 'account-id-456',
    'address': 'test@ptct.net',
    'quota': 40000000,
    'used': 1024,
    'isDisabled': False,
    'isDeleted': False,
    'createdAt': '2025-01-01T00:00:00+00:00'
}

SAMPLE_MESSAGES_RESPONSE = {
    'hydra:member': [
        {
            'id': 'msg-1',
            'subject': 'Test Subject',
            'from': {'address': 'sender@example.com', 'name': 'Sender'},
            'to': [{'address': 'test@ptct.net', 'name': ''}],
            'createdAt': '2025-06-15T10:30:00+00:00',
            'text': 'Hello, this is a test email with enough content to test truncation in the preview.',
            'seen': False
        },
        {
            'id': 'msg-2',
            'subject': 'Another Email',
            'from': {'address': 'other@example.com', 'name': 'Other'},
            'to': [{'address': 'test@ptct.net', 'name': ''}],
            'createdAt': '2025-06-14T08:00:00+00:00',
            'text': None,
            'seen': True
        }
    ]
}

SAMPLE_MESSAGE_CONTENT = {
    'id': 'msg-1',
    'subject': 'Test Subject',
    'from': {'address': 'sender@example.com', 'name': 'Sender'},
    'to': [{'address': 'test@ptct.net', 'name': ''}],
    'createdAt': '2025-06-15T10:30:00+00:00',
    'text': 'Hello, this is a test email.',
    'html': ['<p>Hello, this is a test email.</p>'],
    'seen': True
}

SAMPLE_MARK_READ_RESPONSE = {
    'id': 'msg-1',
    'seen': True
}


def _mock_response(json_data=None, status_code=200, raise_for_status=None):
    """Helper to create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    if raise_for_status:
        mock.raise_for_status.side_effect = raise_for_status
    return mock


class TestMailTMClass(unittest.TestCase):
    """Tests for the MailTM API wrapper class."""

    @patch('app.requests.post')
    def _create_client(self, mock_post):
        """Helper to create a MailTM client with mocked authentication."""
        mock_post.return_value = _mock_response(SAMPLE_TOKEN_RESPONSE)
        client = MailTM(base_url='https://api.mail.tm', email='test@ptct.net', password='pass123')
        return client

    @patch('app.requests.post')
    def test_authenticate_success(self, mock_post):
        mock_post.return_value = _mock_response(SAMPLE_TOKEN_RESPONSE)
        client = MailTM(base_url='https://api.mail.tm', email='test@ptct.net', password='pass123')

        self.assertEqual(client.token, 'fake-jwt-token-123')
        self.assertEqual(client.account_id, 'account-id-456')
        mock_post.assert_called_once_with(
            'https://api.mail.tm/token',
            json={'address': 'test@ptct.net', 'password': 'pass123'}
        )

    @patch('app.requests.post')
    def test_authenticate_failure(self, mock_post):
        mock_post.return_value = _mock_response(
            status_code=401,
            raise_for_status=HTTPError('401 Unauthorized')
        )
        with self.assertRaises(HTTPError):
            MailTM(base_url='https://api.mail.tm', email='bad@test.com', password='wrong')

    @patch('app.requests.get')
    def test_get_domains(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_DOMAINS_RESPONSE)

        domains = client.get_domains()

        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['domain'], 'ptct.net')
        mock_get.assert_called_once_with('https://api.mail.tm/domains')

    @patch('app.requests.get')
    def test_get_account(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_ACCOUNT_RESPONSE)

        account = client.get_account()

        self.assertEqual(account['address'], 'test@ptct.net')
        mock_get.assert_called_once_with(
            'https://api.mail.tm/me',
            headers={'Authorization': 'Bearer fake-jwt-token-123'}
        )

    @patch('app.requests.get')
    def test_get_messages(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_MESSAGES_RESPONSE)

        messages = client.get_messages()

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['id'], 'msg-1')
        self.assertEqual(messages[0]['subject'], 'Test Subject')
        self.assertEqual(messages[0]['from'], 'sender@example.com')
        self.assertEqual(messages[0]['date'], '2025-06-15 10:30:00')
        self.assertIn('Hello', messages[0]['intro'])
        self.assertFalse(messages[0]['seen'])

    @patch('app.requests.get')
    def test_get_messages_no_text_preview(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_MESSAGES_RESPONSE)

        messages = client.get_messages()

        # Second message has text=None
        self.assertEqual(messages[1]['intro'], '(No preview available)')

    @patch('app.requests.get')
    def test_get_messages_pagination(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_MESSAGES_RESPONSE)

        client.get_messages(page=2)

        mock_get.assert_called_once_with(
            'https://api.mail.tm/messages',
            headers={'Authorization': 'Bearer fake-jwt-token-123'},
            params={'page': 2}
        )

    @patch('app.requests.get')
    def test_get_message_content(self, mock_get):
        client = self._create_client()
        mock_get.return_value = _mock_response(SAMPLE_MESSAGE_CONTENT)

        message = client.get_message_content('msg-1')

        self.assertEqual(message['id'], 'msg-1')
        self.assertEqual(message['text'], 'Hello, this is a test email.')
        mock_get.assert_called_once_with(
            'https://api.mail.tm/messages/msg-1',
            headers={'Authorization': 'Bearer fake-jwt-token-123'}
        )

    @patch('app.requests.delete')
    def test_delete_message(self, mock_delete):
        client = self._create_client()
        mock_delete.return_value = _mock_response(status_code=204)

        client.delete_message('msg-1')

        mock_delete.assert_called_once_with(
            'https://api.mail.tm/messages/msg-1',
            headers={'Authorization': 'Bearer fake-jwt-token-123'}
        )

    @patch('app.requests.patch')
    def test_mark_message_as_read(self, mock_patch):
        client = self._create_client()
        mock_patch.return_value = _mock_response(SAMPLE_MARK_READ_RESPONSE)

        result = client.mark_message_as_read('msg-1')

        self.assertTrue(result['seen'])
        mock_patch.assert_called_once_with(
            'https://api.mail.tm/messages/msg-1',
            headers={
                'Authorization': 'Bearer fake-jwt-token-123',
                'Content-Type': 'merge-patch+json'
            },
            json={'seen': True}
        )

    @patch('app.requests.delete')
    def test_delete_account(self, mock_delete):
        client = self._create_client()
        mock_delete.return_value = _mock_response(status_code=204)

        client.delete_account('account-id-456')

        mock_delete.assert_called_once_with(
            'https://api.mail.tm/accounts/account-id-456',
            headers={'Authorization': 'Bearer fake-jwt-token-123'}
        )


class TestFlaskRoutes(unittest.TestCase):
    """Tests for Flask route handlers."""

    def setUp(self):
        self.mock_client = MagicMock(spec=MailTM)
        self.app = create_app(mail_client=self.mock_client)
        self.app.config['TESTING'] = True
        self.app.config['MAIL_TM_EMAIL'] = 'test@ptct.net'
        self.client = self.app.test_client()

    def test_index_renders_messages(self):
        self.mock_client.get_messages.return_value = [
            {
                'id': 'msg-1',
                'subject': 'Test',
                'from': 'sender@example.com',
                'date': '2025-06-15 10:30:00',
                'intro': 'Hello...',
                'seen': False
            }
        ]
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test', response.data)

    def test_index_error_renders_error_page(self):
        self.mock_client.get_messages.side_effect = Exception('API down')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'API down', response.data)

    def test_get_message(self):
        self.mock_client.get_message_content.return_value = SAMPLE_MESSAGE_CONTENT
        response = self.client.get('/message/msg-1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], 'msg-1')

    def test_get_message_error(self):
        self.mock_client.get_message_content.side_effect = Exception('Not found')
        response = self.client.get('/message/bad-id')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_delete_message(self):
        self.mock_client.delete_message.return_value = None
        response = self.client.delete('/message/msg-1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_delete_message_error(self):
        self.mock_client.delete_message.side_effect = Exception('Forbidden')
        response = self.client.delete('/message/msg-1')
        self.assertEqual(response.status_code, 500)

    def test_mark_message_read(self):
        self.mock_client.mark_message_as_read.return_value = SAMPLE_MARK_READ_RESPONSE
        response = self.client.post('/message/msg-1/read')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['seen'])

    def test_refresh_messages(self):
        self.mock_client.get_messages.return_value = [
            {
                'id': 'msg-1',
                'subject': 'Test',
                'from': 'sender@example.com',
                'date': '2025-06-15 10:30:00',
                'intro': 'Hello...',
                'seen': False
            }
        ]
        response = self.client.get('/refresh')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)

    def test_refresh_messages_with_pagination(self):
        self.mock_client.get_messages.return_value = []
        response = self.client.get('/refresh?page=2')
        self.assertEqual(response.status_code, 200)
        self.mock_client.get_messages.assert_called_with(page=2)

    def test_refresh_messages_error(self):
        self.mock_client.get_messages.side_effect = Exception('Timeout')
        response = self.client.get('/refresh')
        self.assertEqual(response.status_code, 500)

    def test_get_domains(self):
        self.mock_client.get_domains.return_value = SAMPLE_DOMAINS_RESPONSE['hydra:member']
        response = self.client.get('/domains')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['domain'], 'ptct.net')

    def test_get_domains_error(self):
        self.mock_client.get_domains.side_effect = Exception('Service unavailable')
        response = self.client.get('/domains')
        self.assertEqual(response.status_code, 500)

    def test_get_account(self):
        self.mock_client.get_account.return_value = SAMPLE_ACCOUNT_RESPONSE
        response = self.client.get('/account')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['address'], 'test@ptct.net')

    def test_get_account_error(self):
        self.mock_client.get_account.side_effect = Exception('Unauthorized')
        response = self.client.get('/account')
        self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
