# sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint, ForeignKey, DateTime
from sqlalchemy import select, or_
from sqlalchemy.orm import relationship
# db
from chat_api.conf import Base
import typing
from datetime import datetime

if typing.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ConversationThrough(Base):
    __tablename__ = 'users2conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    user_power = Column(Integer)
    user = relationship(
        'User'
    )
    conversation = relationship(
        'ConversationModel'
    )


class User(Base):
    __tablename__ = 'users'
    __table_args__ = UniqueConstraint('email', 'login'), {'extend_existing': True}
    extend_existing = True
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    login = Column(String)
    is_active = Column(Boolean, index=True, default=True)
    participants = relationship(
        'ConversationThrough',
        back_populates='user',
        cascade='all, delete-orphan'
    )


class ConversationModel(Base):
    """
    Main Conversation model
    """
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    users = relationship(
        'User',
        secondary='users2conversations',
        cascade="all, delete",
        viewonly=True
    )
    participants = relationship(
        'ConversationThrough',
        back_populates='conversation',
        cascade="all, delete"
    )
    host_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    conversation_name = Column(String, default='')
    last_updated = Column(DateTime, default=datetime.now())

    @classmethod
    async def query_conversation_by_user(cls, async_ses: 'AsyncSession', user_id):
        stmt = select(cls)\
            .join(cls.participants)\
            .filter_by(user_id=user_id).distinct()
        return await async_ses.scalars(stmt)
