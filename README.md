# RNet OAuth Python Library

A Python backend library for integrating **RNet OAuth** and **AI Provider** services. This library allows users to authenticate via RNet and pay for AI model token costs directly using their RNet account.

## Features

- **OAuth2 PKCE Support**: Secure authorization code flow with automatic code verifier and challenge generation.
- **Token Management**: Exchange authorization codes for tokens and refresh expired tokens.
- **UserInfo Endpoint**: Fetch the authenticated user's RNet profile with an access token.
- **AI Integration**: Easy methods to chat with AI models using standard or streaming responses.

## Installation

```bash
pip install rnet-oauth
```

## Quick Start

### 1. Initialize the Clients
```python
from rnet_oauth import RNetAuth, RNetAi

auth = RNetAuth(
    client_id='client-id',
    client_secret='client-secret',
    redirect_uri='redirect-uri'
)
ai = RNetAi()
```

### 2. Generate Authorization URL (OAuth2 PKCE)
```python
# 1. Generate PKCE
pkce = auth.generate_pkce()
verifier = pkce['verifier']
challenge = pkce['challenge']

# 2. Get Authorization URL
# challenge: PKCE code challenge (optional)
# state: An optional string to maintain state between the request and callback (recommended for security)
auth_url = auth.get_authorization_url(challenge, state='optional-state')
```

### 3. Exchange Code for Tokens
```python
# 3. Exchange code for tokens
tokens = auth.exchange_code_for_token(code, verifier)
access_token = tokens['access_token']
```

### 4. Get User Info
```python
user_info = auth.get_user_info(access_token)
print(user_info['email'])
print(user_info['name'])
```

The UserInfo response comes from RNet's `/userinfo` endpoint and may include:
`sub`, `email`, `email_verified`, `name`, `preferred_username`, `user_id`, `role`, and `status`.

### 5. Chat with AI
```python
response = ai.chat({
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Hello!"}]
        }
    ]
}, access_token, "gemini-2.5-flash-lite")
```

### 6. Streaming AI Response (Untested)
```python
for chunk in ai.chat_stream({
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Hello!"}]
        }
    ]
}, access_token, "gemini-2.5-flash-lite"):
    print(chunk)
```

### 7. File Upload (Untested)
```python
with open("document.pdf", "rb") as f:
    file_buffer = f.read()

# Upload to Gemini
gemini_upload = ai.gemini_file_upload(access_token, "gemini-2.5-flash-lite", file_buffer, "application/pdf", "document.pdf")
print(gemini_upload['fileReference']) # Use this in chat payload

# Upload to OpenAI
openai_upload = ai.openai_file_upload(access_token, "gpt-4o", file_buffer, "application/pdf", "document.pdf")
```

### 8. File Deletion (Untested)
```python
# Gemini files auto-delete after 48 hours, so there is no delete method.
# Delete an OpenAI file:
ai.openai_file_delete(access_token, "gpt-4o", openai_upload['fileReference'])
```

### 9. AI Chat with File & Tools (Untested)
```python
payload = {
    "contents": [
        {
            "role": "user",
            "parts": [
                { "text": "Based on this document, what is my name? Also search the web for the current weather in London." },
                { "fileData": { "fileUri": gemini_upload['fileReference'], "mimeType": gemini_upload['mimeType'] } }
            ]
        }
    ],
    "tools": [
        { "googleSearch": {} } # Enable Google Search tool
    ]
}

response = ai.chat(payload, access_token, "gemini-2.5-flash-lite")
print(response)
```

## License
MIT
