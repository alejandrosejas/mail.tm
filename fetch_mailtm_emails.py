import requests

# Your Mail.tm account credentials
EMAIL_ADDRESS = 'test1743440755@ptct.net'
PASSWORD = 'Test123!@#'

# Base URL for the Mail.tm API
BASE_URL = 'https://api.mail.tm'

# Authenticate and obtain a bearer token
def get_token(email, password):
    url = f'{BASE_URL}/token'
    payload = {
        'address': email,
        'password': password
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()['token']

# Retrieve a list of messages
def get_messages(token):
    url = f'{BASE_URL}/messages'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['hydra:member']

# Retrieve the content of a specific message
def get_message_content(token, message_id):
    url = f'{BASE_URL}/messages/{message_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Main function to authenticate and fetch emails
def main():
    try:
        # Authenticate and get token
        token = get_token(EMAIL_ADDRESS, PASSWORD)
        print(f'Authenticated successfully. Token: {token}')

        # Get list of messages
        messages = get_messages(token)
        if not messages:
            print('No messages found.')
            return

        print(f'Found {len(messages)} message(s):')
        for msg in messages:
            print(f"- ID: {msg['id']}, Subject: {msg['subject']}")

        # Optionally, fetch and display content of the first message
        first_message_id = messages[0]['id']
        message_content = get_message_content(token, first_message_id)
        print(f"\nContent of the first message (ID: {first_message_id}):")
        print(message_content['text'] or message_content['html'])

    except requests.exceptions.RequestException as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    main()
