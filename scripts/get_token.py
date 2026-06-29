"""
RUN THIS ONCE on your own computer to create a YouTube refresh token.

Steps:
  1. Put your credentials.json (from Google Cloud) next to this project.
  2. Run:  python scripts/get_token.py  path\\to\\credentials.json
  3. A browser opens -> sign in with your YouTube channel's Google account.
  4. This prints YT_CLIENT_ID, YT_CLIENT_SECRET, and YT_REFRESH_TOKEN.
  5. Copy those three values into GitHub Secrets.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    creds_path = sys.argv[1] if len(sys.argv) > 1 else "credentials.json"

    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    # Opens a browser and runs a tiny local server to catch the response.
    creds = flow.run_local_server(port=0, prompt="consent")

    with open(creds_path) as f:
        data = json.load(f)
    info = data.get("installed") or data.get("web")

    print("\n=========================================================")
    print(" COPY THESE THREE VALUES INTO GITHUB SECRETS:")
    print("=========================================================")
    print(f"YT_CLIENT_ID     = {info['client_id']}")
    print(f"YT_CLIENT_SECRET = {info['client_secret']}")
    print(f"YT_REFRESH_TOKEN = {creds.refresh_token}")
    print("=========================================================\n")


if __name__ == "__main__":
    main()
