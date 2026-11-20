"""Run this ONCE on your own PC (not in the cloud) to get the GTA channel's YouTube refresh token.

    pip install google-auth-oauthlib google-api-python-client
    python get_youtube_token.py path/to/client_secret.json

A browser opens: sign in with the account that owns the GTA channel and, if asked, pick the
GTA channel (not FramedFacts). The script then prints which channel it connected to and the
three values to type into the "gta-repo" cloud environment's settings yourself:
YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Never paste them into chat or commit them.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Same scopes as phase5_upload.py, so the uploader never has to ask again.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python get_youtube_token.py path/to/client_secret.json")
    path = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(path, SCOPES)
    # offline + consent guarantees Google returns a refresh token.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        sys.exit("Google returned no refresh token. Remove the app's access at "
                 "myaccount.google.com/permissions and run this again.")

    yt = build("youtube", "v3", credentials=creds)
    items = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    if not items:
        sys.exit("This login has no YouTube channel. Create the channel first, then run again.")
    ch = items[0]
    print(f"\nConnected channel: {ch['snippet']['title']}  (channel ID {ch['id']})")
    print("If that is NOT the GTA channel, stop and run again choosing the right channel.\n")

    with open(path) as f:
        info = json.load(f)
    info = info.get("installed") or info.get("web") or {}
    print("Type these into the gta-repo environment settings (Environment variables):")
    print(f"YT_CLIENT_ID={info.get('client_id', '')}")
    print(f"YT_CLIENT_SECRET={info.get('client_secret', '')}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
    print(f"YOUTUBE_CHANNEL_ID={ch['id']}")


if __name__ == "__main__":
    main()
