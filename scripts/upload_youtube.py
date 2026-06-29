"""
Uploads a video to YouTube, marked Made for Kids, scheduled to publish at 8am.

Authentication uses a refresh token stored in environment variables (GitHub
Secrets), so it runs unattended with no browser:
    YT_CLIENT_ID
    YT_CLIENT_SECRET
    YT_REFRESH_TOKEN
Create the refresh token once by running get_token.py on your computer.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _client():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"].strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"].strip(),
        client_secret=os.environ["YT_CLIENT_SECRET"].strip(),
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title, description, tags, publish_at_iso,
                 thumbnail_path=None):
    """
    publish_at_iso: ISO-8601 UTC time like '2026-06-30T12:00:00Z'.
    The video is uploaded as private and auto-publishes at that time.
    """
    youtube = _client()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_iso,
            "selfDeclaredMadeForKids": True,
            "madeForKids": True,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"  Uploaded video id: {video_id}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path),
            ).execute()
            print("  Thumbnail set.")
        except Exception as e:  # noqa: BLE001
            print(f"  (Thumbnail skipped: {e})")

    return video_id
