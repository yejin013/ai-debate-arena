from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Debate(Base):
    __tablename__ = "debates"
    id = Column(Integer, primary_key=True, autoincrement=True)  # 토론 ID
    topic = Column(String, nullable=False)  # 토론 주제
    date = Column(String, nullable=False)  # 토론 날짜
    rounds = Column(Integer, nullable=False)  # 토론 라운드 수
    messages = Column(Text, nullable=False)  # 토론 메시지
