from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class PollOptionCreate(BaseModel):
    option_text: str


class PollCreate(BaseModel):
    session_id: Optional[int] = None
    question: str
    options: List[PollOptionCreate] = Field(..., min_length=2)


class PollOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_text: str


class PollOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[int] = None
    question: str
    is_active: bool
    created_at: datetime
    options: List[PollOptionOut] = []


class PollResultOption(BaseModel):
    option_id: int
    option_text: str
    vote_count: int


class PollResultsOut(BaseModel):
    poll_id: int
    question: str
    total_votes: int
    results: List[PollResultOption]


class QuestionCreate(BaseModel):
    question_text: str


class QuestionOut(BaseModel):
    id: int
    session_id: int
    user_id: int
    question_text: str
    is_answered: bool
    created_at: datetime
    upvote_count: int = 0


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    user_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class FeedbackSummaryOut(BaseModel):
    session_id: int
    average_rating: float
    total_responses: int

