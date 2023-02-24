# local staff
from .serializers import ConversationInput, ConversationSerializer
from .utils import authenticate
# fastapi staff
from fastapi import Request, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
# conf
from chat_api.conf.db import get_async_ses
from chat_api.conf import app
# shortcuts
from shortcuts.encryption.encryption import JWT, JWTException, DecodeError
# models staff
from .models import ConversationModel, ConversationThrough
# python staff
import typing
from typing import List

if typing.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ConversationRoom:
    allow_creation: bool = True
    host_id: typing.Optional[int]
    host_power: int = 0
    _is_chat: bool

    def __init__(self, host_data, user_ids: set, conv_name: str):
        prepared_host = self.get_host(host_data)
        user_ids = user_ids - {prepared_host}
        self.is_chat = len(user_ids) + 1
        self.conversation_name = conv_name
        self.host_id = prepared_host
        if self.allow_creation is False:
            raise HTTPException(status_code=400, detail={'error': 'Minimum required user count - 2!'})
        self.chat_users = self.prepare_users(user_ids)

    @staticmethod
    def get_host(host_data):
        return host_data.get('id')

    async def asave(self, db_ses: 'AsyncSession'):
        db_room = ConversationModel(
            conversation_name=self.conversation_name
        )

        for user_dict in self.chat_users:
            participant = ConversationThrough(**user_dict)
            db_room.participants += [participant]
            db_ses.add(participant)

        host_participant = ConversationThrough(
            user_id=self.host_id,
            user_power=self.host_power
        )
        db_ses.add(host_participant)
        db_room.participants.append(
            host_participant
        )

        if self.is_chat:
            db_room.host_id = self.host_id

        db_ses.add(db_room)
        await db_ses.flush()
        return db_room


    @staticmethod
    def prepare_users(user_set: set):
        user_list = []
        for user_id in user_set:
            user_list.append(
                {'user_id': user_id, 'user_power': 0}
            )
        return user_list

    @property
    def is_chat(self):
        return self._is_chat

    @is_chat.setter
    def is_chat(self, user_count):
        if user_count == 1:
            self.allow_creation = False
        elif user_count == 2:
            self._is_chat = False
            self.host_power = 0
        else:
            self.host_power = 100
            self._is_chat = True


@app.post(
    path='/conversation/create/'
)
async def conversation_creation(
        conversation_data: ConversationInput,
        ses=Depends(get_async_ses),
        user_data: dict = Depends(authenticate)
):
    room_prepared = ConversationRoom(host_data=user_data, **conversation_data.dict())
    db_room = await room_prepared.asave(ses)
    ret_id = db_room.id
    await ses.commit()
    return JSONResponse(content={'id': ret_id}, status_code=201)


@app.get(
    path='/conversation/list/',
    response_model=List[ConversationSerializer]
)
async def conversation_list(
        user_data: dict = Depends(authenticate),
        async_ses=Depends(get_async_ses)
):
    async_ses: 'AsyncSession'
    conversations = await ConversationModel.query_conversation_by_user(async_ses, user_data.get('id'))
    conversations: List[ConversationModel]
    return ConversationSerializer.from_orm(instances=conversations, many=True)

