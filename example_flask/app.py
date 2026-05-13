"""
RNet OAuth Example — Flask Backend
=================================
Run:
    pip install flask
    python app.py

Then open:  http://localhost:5000
"""

import sys
import os

# Allow importing rnet_oauth from the sibling package folder during development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, redirect, request, session, jsonify, url_for
from rnet_oauth import RNetAuth, RNetAi

app = Flask(__name__)
app.secret_key = "change-me-in-production"  # Required for session

# ── Initialise the RNet OAuth client ───────────────────────────────────────────

client = RNetAuth(
    client_id="rnet-xxxxxxxxx",         # replace with your Client ID
    client_secret="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # replace with your Client Secret
    redirect_uri="http://localhost:5000/callback"
)

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Landing page — shows a login link or the acquired tokens."""
    tokens = session.get("tokens")
    if tokens:
        return f"""
        <h2>Authenticated!</h2>
        <pre>{__import__('json').dumps(tokens, indent=2)}</pre>
        <form method="POST" action="/refresh">
            <button type="submit">Refresh Token</button>
        </form>
        <a href="/logout">Logout</a>
        """
    return '<a href="/login"><button>Login with RNet</button></a>'


@app.route("/login")
def login():
    """Generate PKCE, save verifier in session, redirect to RNet login page."""
    pkce = client.generate_pkce()
    session["pkce_verifier"] = pkce["verifier"]

    auth_url = client.get_login_url(challenge=pkce["challenge"])
    print(f"Redirecting to: {auth_url}")
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Handle the OAuth2 redirect. Exchange the code for tokens."""
    error = request.args.get("error")
    if error:
        desc = request.args.get("error_description", "")
        return f"<h2>Authentication failed</h2><p>{error}: {desc}</p>", 400

    code = request.args.get("code")
    if not code:
        return "<h2>Error</h2><p>No authorization code received.</p>", 400

    try:
        verifier = session.pop("pkce_verifier", None)
        tokens = client.exchange_token(code, code_verifier=verifier)
        session["tokens"] = tokens
        return redirect(url_for("index"))
    except RuntimeError as exc:
        return f"<h2>Token exchange failed</h2><p>{exc}</p>", 500


@app.route("/refresh", methods=["POST"])
def refresh():
    """Use the stored refresh token to get a new access token."""
    tokens = session.get("tokens", {})
    rt = tokens.get("refresh_token")
    if not rt:
        return "<p>No refresh token available.</p>", 400

    try:
        new_tokens = client.refresh_token(rt)
        # Merge: keep any fields not returned by refresh response
        session["tokens"] = {**tokens, **new_tokens}
        return redirect(url_for("index"))
    except RuntimeError as exc:
        return f"<h2>Refresh failed</h2><p>{exc}</p>", 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(port=5000, debug=True)
