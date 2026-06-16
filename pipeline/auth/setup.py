"""
OAuth setup CLI for platforms that require browser-based authorization.
Usage: python -m pipeline.auth.setup --platform youtube
       python -m pipeline.auth.setup --platform linkedin
       python -m pipeline.auth.setup --platform tiktok
"""
import argparse
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)


def setup_youtube():
    from google_auth_oauthlib.flow import InstalledAppFlow
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "credentials/youtube_client_secret.json")
    token_file = os.getenv("YOUTUBE_TOKEN_FILE", "credentials/youtube_token.json")
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    flow = InstalledAppFlow.from_client_secrets_file(client_secret, scopes)
    creds = flow.run_local_server(port=8080)
    with open(token_file, "w") as f:
        f.write(creds.to_json())
    print(f"YouTube token saved to {token_file}")


def setup_linkedin():
    import urllib.parse

    client_id = os.environ["LINKEDIN_CLIENT_ID"]
    client_secret = os.environ["LINKEDIN_CLIENT_SECRET"]
    redirect_uri = "http://localhost:8080/callback"
    scopes = "openid profile email w_member_social"
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code&client_id={client_id}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&scope={urllib.parse.quote(scopes)}"
    )
    print(f"Open this URL in your browser:\n{auth_url}\n")
    code = input("Paste the 'code' parameter from the redirect URL: ").strip()

    import requests
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    token_data = resp.json()
    token_file = "credentials/linkedin_token.json"
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"LinkedIn token saved to {token_file}")
    print(f"Access token: {token_data.get('access_token', 'ERROR — check response')[:20]}...")


def setup_tiktok():
    import secrets
    import base64
    import hashlib
    import urllib.parse

    client_key = os.environ["TIKTOK_CLIENT_KEY"]
    redirect_uri = "http://localhost:8080/tiktok/callback"
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&response_type=code"
        f"&scope=video.upload,video.publish"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    print(f"Open this URL in your browser:\n{auth_url}\n")
    code = input("Paste the 'code' parameter from the redirect URL: ").strip()

    import requests
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key": client_key,
            "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
    )
    token_data = resp.json()
    token_file = "credentials/tiktok_token.json"
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"TikTok token saved to {token_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=["youtube", "linkedin", "tiktok"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    {"youtube": setup_youtube, "linkedin": setup_linkedin, "tiktok": setup_tiktok}[args.platform]()
