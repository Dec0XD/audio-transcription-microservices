from typing import List, Optional

from pydantic import BaseModel


class ApiKeysUpdate(BaseModel):
    hf_token: Optional[str] = None
    aai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None


class MeetingMinutesRequest(BaseModel):
    transcription_id: int
    title: Optional[str] = None
    date: Optional[str] = None
    participants: Optional[List[str]] = None
