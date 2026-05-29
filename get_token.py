"""
Run this ONCE locally to get your Gmail OAuth refresh token.
Paste CLIENT_ID and CLIENT_SECRET from Google Cloud Console below, then run:
    python get_token.py
Copy the printed refresh token into Render as GMAIL_REFRESH_TOKEN.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_ID = "PASTE_YOUR_CLIENT_ID_HERE"
CLIENT_SECRET = "PASTE_YOUR_CLIENT_SECRET_HERE"

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    },
    scopes=["https://www.googleapis.com/auth/gmail.send"],
)

creds = flow.run_local_server(port=0)
print("\n--- COPY THESE INTO RENDER ENVIRONMENT VARIABLES ---")
print(f"GMAIL_CLIENT_ID     = {CLIENT_ID}")
print(f"GMAIL_CLIENT_SECRET = {CLIENT_SECRET}")
print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
print("----------------------------------------------------\n")
