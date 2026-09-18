from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.connections import get_db
from app.schemas.engagement import (
    PollCreate,
    PollOut,
    PollResultsOut,
    QuestionCreate,
    QuestionOut,
    FeedbackCreate,
    FeedbackOut,
    FeedbackSummaryOut,
)
from app.services import (
    create_poll,
    get_poll,
    list_polls,
    cast_poll_vote,
    get_poll_results,
    create_question,
    get_questions_for_session,
    get_question_by_id,
    upvote_question,
    mark_question_answered,
    submit_feedback,
    get_feedback_summary,
    get_session,
)
from app.utils import get_current_user, require_roles
from app.models.user import User, RoleEnum

router = APIRouter(prefix="/engagement", tags=["Networking, Polls, Q&A & Feedback"])


# ---- Polls ----

@router.post(
    "/polls",
    response_model=PollOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleEnum.organiser, RoleEnum.speaker))],
)
def add_poll(
    data: PollCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    return create_poll(db, data, created_by=current_user.id)


@router.get("/polls", response_model=List[PollOut])
def read_polls(session_id: Optional[int] = None, db: DBSession = Depends(get_db)):
    return list_polls(db, session_id=session_id)


@router.post("/polls/{poll_id}/vote/{option_id}", status_code=status.HTTP_201_CREATED)
def vote_on_poll(
    poll_id: int,
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    poll = get_poll(db, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if not any(o.id == option_id for o in poll.options):
        raise HTTPException(status_code=400, detail="That option doesn't belong to this poll")

    cast_poll_vote(db, poll_id=poll_id, poll_option_id=option_id, user_id=current_user.id)
    return {"detail": "Vote recorded"}


@router.get("/polls/{poll_id}/results", response_model=PollResultsOut)
def poll_results(poll_id: int, db: DBSession = Depends(get_db)):
    poll = get_poll(db, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return get_poll_results(db, poll)


# ---- Q&A ----

@router.post(
    "/sessions/{session_id}/questions",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
)
def ask_question(
    session_id: int,
    data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return create_question(
        db, session_id=session_id, user_id=current_user.id, question_text=data.question_text
    )


@router.get("/sessions/{session_id}/questions", response_model=List[QuestionOut])
def read_questions(session_id: int, db: DBSession = Depends(get_db)):
    return get_questions_for_session(db, session_id)


@router.post("/questions/{question_id}/upvote", status_code=status.HTTP_201_CREATED)
def upvote(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    question = get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    upvote_question(db, question_id=question_id, user_id=current_user.id)
    return {"detail": "Upvote recorded"}


@router.patch(
    "/questions/{question_id}/answer",
    response_model=QuestionOut,
    dependencies=[Depends(require_roles(RoleEnum.speaker, RoleEnum.organiser))],
)
def answer_question(question_id: int, db: DBSession = Depends(get_db)):
    question = get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return mark_question_answered(db, question)


# ---- Feedback ----

@router.post(
    "/sessions/{session_id}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def add_feedback(
    session_id: int,
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return submit_feedback(
        db, session_id=session_id, user_id=current_user.id, rating=data.rating, comment=data.comment
    )


@router.get(
    "/sessions/{session_id}/feedback/summary",
    response_model=FeedbackSummaryOut,
    dependencies=[Depends(require_roles(RoleEnum.speaker, RoleEnum.organiser))],
)
def feedback_summary(session_id: int, db: DBSession = Depends(get_db)):
    return get_feedback_summary(db, session_id)

