"""
Step 3-1: 박사님 유튜브 채널(@jangsanbrain) 영상 자막 수집
youtube-transcript-api 사용, 영상 ID만 입력하면 자막 텍스트 반환.
"""
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class TranscriptItem:
    text: str
    start: float
    duration: float


def get_transcript(video_id: str) -> Optional[str]:
    """
    유튜브 영상 ID로 자막 텍스트를 가져옵니다.
    video_id: 예) 'dQw4w9WgXcQ' (URL의 v= 파라미터)
    반환: 전체 자막을 한 문자열로 합친 것. 실패 시 None.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return None

    if not transcript_list:
        return None

    parts = []
    for item in transcript_list:
        text = item.get("text") or ""
        if isinstance(text, str):
            parts.append(text.strip())
    return " ".join(parts).strip() if parts else None


def get_transcript_with_timestamps(video_id: str) -> Optional[List[TranscriptItem]]:
    """
    영상 ID로 자막을 시작 시간·길이와 함께 가져옵니다.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        return None

    if not transcript_list:
        return None

    return [
        TranscriptItem(
            text=(item.get("text") or "").strip(),
            start=float(item.get("start", 0)),
            duration=float(item.get("duration", 0)),
        )
        for item in transcript_list
    ]
