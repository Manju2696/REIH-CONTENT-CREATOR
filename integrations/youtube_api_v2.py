"""Fresh YouTube integration layer."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

import database.db_setup as db

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request

    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


# OAuth 2.0 scopes - only use youtube.upload for video uploads
# NOTE: Additional scopes require configuration in Google Cloud Console OAuth consent screen
SCOPES: List[str] = [
    "https://www.googleapis.com/auth/youtube.upload",
]

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_DIR.mkdir(exist_ok=True)
TOKEN_FILE = CREDENTIALS_DIR / "youtube_tokens.json"


# -----------------------------------------------------------------------------
# Environment helpers
# -----------------------------------------------------------------------------


def _is_streamlit_cloud() -> bool:
    try:
        import streamlit as st  # type: ignore

        if hasattr(st, "secrets") and st.secrets:
            return True
    except Exception:
        pass
    return bool(os.getenv("STREAMLIT_CLOUD"))


def _get_streamlit_secrets() -> Dict[str, Any]:
    if not _is_streamlit_cloud():
        return {}
    try:
        import streamlit as st  # type: ignore

        return dict(st.secrets.get("YouTube") or st.secrets.get("youtube") or {})
    except Exception:
        return {}


def get_redirect_uri() -> str:
    if _is_streamlit_cloud():
        streamlit_url = os.getenv("STREAMLIT_APP_URL")
        if streamlit_url:
            return f"{streamlit_url.rstrip('/')}/youtube_callback"
        return "https://reih-content-creator-4leuhlnaasfsjsxztqu5wj.streamlit.app/youtube_callback"
    return "http://localhost:8501/youtube_callback"


def _load_client_credentials() -> Optional[Dict[str, str]]:
    secrets = _get_streamlit_secrets()
    client_id = secrets.get("CLIENT_ID") or secrets.get("client_id")
    client_secret = secrets.get("CLIENT_SECRET") or secrets.get("client_secret")

    if not (client_id and client_secret):
        client_id = os.getenv("YOUTUBE_CLIENT_ID", client_id)
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET", client_secret)

    config_file = BASE_DIR / "config.json"
    if (not client_id or not client_secret) and config_file.exists():
        try:
            cfg = json.loads(config_file.read_text())
            yt_cfg = cfg.get("youtube", {})
            client_id = yt_cfg.get("client_id", client_id)
            client_secret = yt_cfg.get("client_secret", client_secret)
        except Exception:
            pass

    if client_id and client_secret:
        return {"client_id": client_id, "client_secret": client_secret}
    return None


def _client_config() -> Optional[Dict[str, Any]]:
    creds = _load_client_credentials()
    if not creds:
        return None
    return {
        "web": {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [get_redirect_uri()],
        }
    }


# -----------------------------------------------------------------------------
# Token helpers
# -----------------------------------------------------------------------------


def _load_local_tokens() -> Optional[Dict[str, Any]]:
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except Exception:
        return None


def _save_local_tokens(data: Dict[str, Any]) -> None:
    TOKEN_FILE.write_text(json.dumps(data, indent=2))


def _cloud_tokens() -> Dict[str, Any]:
    secrets = _get_streamlit_secrets()
    return {
        "token": secrets.get("ACCESS_TOKEN") or secrets.get("access_token"),
        "refresh_token": secrets.get("REFRESH_TOKEN") or secrets.get("refresh_token"),
    }


def _stash_tokens_for_user(creds: Credentials) -> None:
    try:
        import streamlit as st  # type: ignore

        st.session_state["youtube_new_tokens"] = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception:
        pass


def _persist_credentials(creds: Credentials) -> None:
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    if _is_streamlit_cloud():
        _stash_tokens_for_user(creds)
    else:
        _save_local_tokens(data)


def clear_credentials() -> bool:
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    try:
        import streamlit as st  # type: ignore

        if "youtube_new_tokens" in st.session_state:
            del st.session_state["youtube_new_tokens"]
    except Exception:
        pass
    return True


# -----------------------------------------------------------------------------
# OAuth entry points
# -----------------------------------------------------------------------------


def get_authorization_url() -> Optional[str]:
    if not GOOGLE_LIBS_AVAILABLE:
        return None
    config = _client_config()
    if not config:
        return None
    flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=get_redirect_uri())
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return url


def exchange_code_for_credentials(code: str) -> Optional[Credentials]:
    if not GOOGLE_LIBS_AVAILABLE:
        return None
    config = _client_config()
    if not config:
        return None
    flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=get_redirect_uri())
    flow.fetch_token(code=code)
    creds = flow.credentials
    if creds:
        _persist_credentials(creds)
    return creds


# -----------------------------------------------------------------------------
# Credential access / YouTube service
# -----------------------------------------------------------------------------


def _build_creds_from_info(info: Dict[str, Any]) -> Optional[Credentials]:
    client = _load_client_credentials()
    if not client:
        return None
    try:
        return Credentials(
            token=info.get("token"),
            refresh_token=info.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client["client_id"],
            client_secret=client["client_secret"],
            scopes=SCOPES,
        )
    except Exception:
        return None


def _load_credentials() -> Optional[Credentials]:
    if not GOOGLE_LIBS_AVAILABLE:
        return None

    if _is_streamlit_cloud():
        creds = _build_creds_from_info(_cloud_tokens())
    else:
        info = _load_local_tokens()
        creds = Credentials.from_authorized_user_info(info, SCOPES) if info else None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _persist_credentials(creds)
        except Exception:
            return None
    return creds


def get_credentials() -> Optional[Credentials]:
    return _load_credentials()


def is_youtube_authenticated() -> bool:
    creds = get_credentials()
    return bool(creds and creds.valid)


def get_youtube_service():
    creds = get_credentials()
    if not creds:
        return None
    return build("youtube", "v3", credentials=creds)


# -----------------------------------------------------------------------------
# Upload helpers
# -----------------------------------------------------------------------------


def _download_temp(url: str, suffix: str) -> Optional[str]:
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp.write(chunk)
        temp.close()
        return temp.name
    except Exception:
        return None


def _prepare_tags(keywords: Any) -> List[str]:
    if not keywords or keywords == "N/A":
        return []
    if isinstance(keywords, str):
        return [tag.strip() for tag in keywords.split(",") if tag.strip()]
    if isinstance(keywords, list):
        return [str(tag).strip() for tag in keywords if tag]
    return []


def upload_video_to_youtube(
    video_file_path: str,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    category_id: str = "22",
    privacy_status: str = "unlisted",
    thumbnail_file_path: Optional[str] = None,
) -> Dict[str, Any]:
    if not GOOGLE_LIBS_AVAILABLE:
        return {"success": False, "error": "Google API libraries not installed."}

    youtube = get_youtube_service()
    if not youtube:
        return {"success": False, "error": "YouTube account not authenticated."}

    temp_video = None
    usable_path = video_file_path
    if isinstance(video_file_path, str) and video_file_path.startswith("http"):
        temp_video = _download_temp(video_file_path, ".mp4")
        usable_path = temp_video

    if not usable_path or not os.path.exists(usable_path):
        return {"success": False, "error": "Video file not found."}

    title = (title or "Untitled Video").strip()[:100]
    description = (description or "").strip()[:5000]
    tag_list = tags if tags is not None else _prepare_tags(tags)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id or "22",
        },
        "status": {
            "privacyStatus": privacy_status if privacy_status in {"public", "private", "unlisted"} else "unlisted",
            "selfDeclaredMadeForKids": False,
        },
    }
    if tag_list:
        body["snippet"]["tags"] = tag_list[:10]

    media = MediaFileUpload(usable_path, chunksize=-1, resumable=True, mimetype="video/*")

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()

        video_id = response.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        if thumbnail_file_path:
            _upload_thumbnail(youtube, video_id, thumbnail_file_path)

        track_youtube_upload_success()
        return {"success": True, "video_id": video_id, "video_url": video_url}
    except HttpError as error:
        if error.resp.status in (401, 403):
            return {
                "success": False,
                "error": "Permission denied. Re-run authentication and ensure your Google account has a YouTube channel.",
            }
        return {"success": False, "error": f"YouTube API Error: {error}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        if temp_video and os.path.exists(temp_video):
            os.unlink(temp_video)


def _upload_thumbnail(youtube, video_id: str, thumbnail_path: str) -> None:
    temp_thumb = None
    path_to_use = thumbnail_path
    if thumbnail_path and thumbnail_path.startswith("http"):
        temp_thumb = _download_temp(thumbnail_path, ".jpg")
        path_to_use = temp_thumb

    if not path_to_use or not os.path.exists(path_to_use):
        return

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(path_to_use, mimetype="image/jpeg", resumable=False),
        ).execute()
    except Exception as exc:
        print(f"[WARNING] Thumbnail upload failed: {exc}")
    finally:
        if temp_thumb and os.path.exists(temp_thumb):
            os.unlink(temp_thumb)


# -----------------------------------------------------------------------------
# Account / quota helpers
# -----------------------------------------------------------------------------


def check_youtube_account_status() -> Dict[str, Any]:
    youtube = get_youtube_service()
    if not youtube:
        return {"error": "Not authenticated."}
    try:
        resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()
        if resp.get("items"):
            channel = resp["items"][0]
            return {
                "success": True,
                "channel_id": channel.get("id"),
                "channel_title": channel.get("snippet", {}).get("title"),
                "subscriber_count": channel.get("statistics", {}).get("subscriberCount"),
                "video_count": channel.get("statistics", {}).get("videoCount"),
            }
        return {"error": "YouTube channel not found for this account."}
    except HttpError as error:
        return {"error": f"YouTube API error: {error}"}


def track_youtube_upload_success() -> None:
    try:
        today = date.today().isoformat()
        existing = db.execute_query(
            "SELECT id FROM youtube_upload_tracking WHERE upload_date = ?", (today,)
        )
        if existing:
            db.execute_update(
                """
                UPDATE youtube_upload_tracking
                SET upload_count = upload_count + 1,
                    last_upload_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (existing[0]["id"],),
            )
        else:
            db.execute_insert(
                """
                INSERT INTO youtube_upload_tracking (upload_date, upload_count, daily_limit, created_at, updated_at)
                VALUES (?, 1, 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (today,),
            )
    except Exception as exc:
        print(f"[WARNING] Failed to track YouTube upload: {exc}")


def track_youtube_upload_limit_reached() -> None:
    try:
        today = date.today().isoformat()
        db.execute_insert(
            """
            INSERT INTO youtube_upload_tracking (upload_date, upload_count, daily_limit, created_at, updated_at)
            VALUES (?, 6, 6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(upload_date)
            DO UPDATE SET upload_count = 6, updated_at = CURRENT_TIMESTAMP
        """,
            (today,),
        )
    except Exception as exc:
        print(f"[WARNING] Failed to track upload limit: {exc}")


def get_youtube_upload_status() -> Dict[str, Any]:
    try:
        today = date.today().isoformat()
        record = db.execute_query(
            """
            SELECT upload_count, daily_limit, last_upload_at
            FROM youtube_upload_tracking
            WHERE upload_date = ?
        """,
            (today,),
        )
        if record:
            data = record[0]
            limit = data.get("daily_limit", 6) or 6
            count = data.get("upload_count", 0) or 0
            return {
                "today": today,
                "upload_count": count,
                "daily_limit": limit,
                "remaining": max(0, limit - count),
                "limit_reached": count >= limit,
                "last_upload_at": data.get("last_upload_at"),
            }
        return {
            "today": today,
            "upload_count": 0,
            "daily_limit": 6,
            "remaining": 6,
            "limit_reached": False,
            "last_upload_at": None,
        }
    except Exception as exc:
        return {
            "today": date.today().isoformat(),
            "upload_count": 0,
            "daily_limit": 6,
            "remaining": 6,
            "limit_reached": False,
            "error": str(exc),
        }

