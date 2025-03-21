import datetime
import json
import logging
from typing import List, Optional, Tuple, Dict

from database.model import Debate
from database.session import db_session

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    pass


class DebateRepository:

    # Singleton 패턴 적용
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebateRepository, cls).__new__(cls)
        return cls._instance

    # 토론 저장
    def save(self, topic: str, rounds: int, messages: List[Dict]) -> bool:
        try:
            with db_session.get_db_session() as session:
                # 현재 시간 저장 (YYYY-MM-DD HH:MM:SS)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # List[Dict] 형태의 메시지를 JSON string으로 변환
                messages_json = json.dumps(messages, ensure_ascii=False)

                debate = Debate(
                    topic=topic, date=now, rounds=rounds, messages=messages_json
                )
                session.add(debate)
            return True
        except Exception as e:
            logger.error(f"토론 저장 중 오류 발생: {str(e)}")
            raise RepositoryError(f"토론 저장 오류: {str(e)}") from e

    # 토론 이력 조회
    def fetch(self) -> List[Tuple[int, str, str, int]]:
        try:
            with db_session.get_db_session() as session:
                debates = (
                    session.query(Debate.id, Debate.topic, Debate.date, Debate.rounds)
                    .order_by(Debate.date.desc())
                    .all()
                )
                return [(d.id, d.topic, d.date, d.rounds) for d in debates]
        except Exception as e:
            logger.error(f"토론 이력 조회 중 오류 발생: {str(e)}")
            raise RepositoryError(f"토론 이력 조회 오류: {str(e)}") from e

    # id로 토론 조회
    def fetch_by_id(self, debate_id: int) -> Tuple[Optional[str], Optional[List[Dict]]]:
        try:
            with db_session.get_db_session() as session:
                debate = session.query(Debate).filter(Debate.id == debate_id).first()

                if debate:
                    messages = json.loads(debate.messages)
                    return debate.topic, messages
                return None, None
        except json.JSONDecodeError as e:
            logger.error(f"JSON 디코딩 오류: {str(e)}")
            raise RepositoryError(f"토론 데이터 변환 오류: {str(e)}") from e
        except Exception as e:
            logger.error(f"토론 불러오기 중 오류 발생: {str(e)}")
            raise RepositoryError(f"토론 불러오기 오류: {str(e)}") from e

    # id로 토론 삭제
    def delete_by_id(self, debate_id: int) -> bool:
        try:
            with db_session.get_db_session() as session:
                result = session.query(Debate).filter(Debate.id == debate_id).delete()
                return result > 0
        except Exception as e:
            logger.error(f"토론 삭제 중 오류 발생: {str(e)}")
            raise RepositoryError(f"토론 삭제 오류: {str(e)}") from e

    # 전체 토론 삭제
    def delete_all(self) -> int:
        try:
            with db_session.get_db_session() as session:
                result = session.query(Debate).delete()
                return result
        except Exception as e:
            logger.error(f"전체 토론 삭제 중 오류 발생: {str(e)}")
            raise RepositoryError(f"전체 토론 삭제 오류: {str(e)}") from e


debate_repository = DebateRepository()
