import hashlib
import os
import base64
import json
import urllib.request
import urllib.error
from urllib.parse import urlencode
from typing import Optional, Dict, Any, Generator

class RNetAuth:
    """
    RNet Auth Python Library
    A backend library to verify and exchange OAuth2 tokens and interact with rNet Ai.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        if not all([client_id, client_secret, redirect_uri]):
            raise ValueError("client_id, client_secret, and redirect_uri are required")

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.issuer = "https://central-backend.rnetai.org"
        self.ai_provider = "https://ai-provider.rnetai.org"

    def generate_pkce(self) -> Dict[str, str]:
        """Generates a PKCE code_verifier and code_challenge."""
        verifier_bytes = os.urandom(32)
        verifier = base64.urlsafe_b64encode(verifier_bytes).decode('utf-8').replace('=', '')
        
        challenge_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(challenge_hash).decode('utf-8').replace('=', '')
        
        return {"verifier": verifier, "challenge": challenge}

    def get_authorization_url(self, challenge: Optional[str] = None, state: Optional[str] = None) -> str:
        """Generates the authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email"
        }

        if challenge:
            params["code_challenge"] = challenge
            params["code_challenge_method"] = "S256"
            
        if state:
            params["state"] = state

        return f"{self.issuer}/oauth2/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, code_verifier: Optional[str] = None) -> Dict[str, Any]:
        """Exchanges an authorization code for tokens."""
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        if code_verifier:
            payload["code_verifier"] = code_verifier

        return self._post_token(payload)

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Renews tokens using a refresh token."""
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        return self._post_token(payload)

    def _post_token(self, payload: Dict[str, str]) -> Dict[str, Any]:
        url = f"{self.issuer}/oauth2/token"
        data = urlencode(payload).encode('utf-8')
        
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode('utf-8')).decode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {auth}'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            self._handle_error(e)

    def _handle_error(self, e: urllib.error.HTTPError):
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            msg = error_data.get("error", str(e))
        except:
            msg = str(e)
        raise RuntimeError(f"Request failed: {e.code} - {msg}")

class RNetAi:
    """
    rNet Ai Python Library
    Interaction with rNet Ai services.
    """

    def __init__(self):
        self.ai_provider = "https://ai-provider.rnetai.org"

    def chat(self, body: Dict[str, Any], access_token: str, model: str) -> Dict[str, Any]:
        """Calls the rNet Ai Provider API."""
        if not access_token: raise ValueError("access_token is required")
        if not model: raise ValueError("model is required")

        query = urlencode({"access_token": access_token, "model": model})
        url = f"{self.ai_provider}/ai?{query}"
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            self._handle_error(e)

    def chat_stream(self, body: Dict[str, Any], access_token: str, model: str) -> Generator[str, None, None]:
        """Calls the rNet Ai Provider API and returns a generator for the response stream."""
        if not access_token: raise ValueError("access_token is required")
        if not model: raise ValueError("model is required")

        query = urlencode({"access_token": access_token, "model": model})
        url = f"{self.ai_provider}/ai/stream?{query}"
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            response = urllib.request.urlopen(req)
            for line in response:
                yield line.decode('utf-8')
        except urllib.error.HTTPError as e:
            self._handle_error(e)

    def _handle_error(self, e: urllib.error.HTTPError):
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            msg = error_data.get("error", str(e))
        except:
            msg = str(e)
        raise RuntimeError(f"Request failed: {e.code} - {msg}")
