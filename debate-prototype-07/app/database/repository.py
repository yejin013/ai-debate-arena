import datetime
import json
import logging
from typing import List, Optional, Tuple, Dict, Union

from database.model import Debate
from database.session import get_db_session

logger = logging.getLogger(__name__)


def save_debate_to_db(
    topic: str, rounds: int, messages: List[Dict], retrieved_docs: Optional[Dict] = None
) -> Union[int, None]:
    try:
        with get_db_session() as session:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            messages_json = json.dumps(messages, ensure_ascii=False)

            docs_json = (
                json.dumps(retrieved_docs, ensure_ascii=False)
                if retrieved_docs
                else None
            )

            debate = Debate(
                topic=topic,
                date=now,
                rounds=rounds,
                messages=messages_json,
                retrieved_docs=docs_json,
            )

            session.add(debate)
            session.commit()
            return debate.id  # 생성된 ID 반환
    except Exception as e:
        logger.error(f"토론 저장 중 오류 발생: {str(e)}")
        return None


def fetch_debate_history() -> Optional[List[Tuple[int, str, str, int]]]:
    try:
        with get_db_session() as session:
            debates = (
                session.query(Debate.id, Debate.topic, Debate.date, Debate.rounds)
                .order_by(Debate.date.desc())
                .all()
            )
            return [(d.id, d.topic, d.date, d.rounds) for d in debates]
    except Exception as e:
        logger.error(f"토론 이력 조회 중 오류 발생: {str(e)}")
        return None


def fetch_debate_by_id(
    debate_id: int,
) -> Tuple[Optional[str], Optional[List[Dict]], Optional[Dict]]:
    try:
        with get_db_session() as session:
            debate = session.query(Debate).filter(Debate.id == debate_id).first()

            if debate:
                messages = json.loads(debate.messages)
                retrieved_docs = (
                    json.loads(debate.retrieved_docs) if debate.retrieved_docs else {}
                )
                return debate.topic, messages, retrieved_docs
            logger.warning(f"ID {debate_id}에 해당하는 토론을 찾을 수 없습니다.")
            return None, None, None
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코딩 오류: {str(e)}")
        return None, None, None
    except Exception as e:
        logger.error(f"토론 불러오기 중 오류 발생: {str(e)}")
        return None, None, None


def delete_debate_by_id(debate_id: int) -> bool:
    try:
        with get_db_session() as session:
            result = session.query(Debate).filter(Debate.id == debate_id).delete()
            session.commit()  # commit 추가
            if result == 0:
                logger.warning(
                    f"ID {debate_id}에 해당하는 토론이 없어 삭제할 수 없습니다."
                )
            return result > 0
    except Exception as e:
        logger.error(f"토론 삭제 중 오류 발생: {str(e)}")
        return False


def delete_all_debates() -> Optional[int]:
    try:
        with get_db_session() as session:
            result = session.query(Debate).delete()
            session.commit()  # commit 추가
            return result
    except Exception as e:
        logger.error(f"전체 토론 삭제 중 오류 발생: {str(e)}")
        return None
