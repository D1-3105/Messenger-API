import unittest
from conf.db import engine
from conf.config import AUTH_URL, OBTAIN_USER_PROFILE_URL
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from .controllers import ConversationRoom
from messenger import app
from .models import User, ConversationModel
from shortcuts.encryption.encryption import JWT
import aiohttp
import asyncio


async def create_user(credentials, ses):
    async with ses.post(AUTH_URL, json=credentials) as resp:
        assert resp.status == 201 or resp.status == 200
        return (await resp.json()).get('token', 'ERROR')


class TestConversationCreation(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        """
        set up
        :return:
        """
        self.async_ses = AsyncSession(engine, expire_on_commit=False)
        self.client = TestClient(app)
        test_host_credentials = {
            'email': '123456789@gmail.com',
            'password': '12345678910'
        }
        test_user_credentials = [
            {'email': f'{_}@something777.com', 'password': '12345678910'}
            for _ in range(2)
        ]
        tasks = []
        auth_ses = aiohttp.ClientSession()
        tasks.append(
            create_user(test_host_credentials, auth_ses)
        )
        for usr_cr in test_user_credentials:
            tasks.append(
                create_user(usr_cr, auth_ses)
            )
        self.host_jwt, *tokens = (await asyncio.gather(*tasks))
        await auth_ses.close()
        self.conv_users = []
        for token in tokens:
            self.conv_users.append(JWT.decrypt(token).get('user_id'))
        assert None not in self.conv_users

    async def test_create_conversation_room_endpoint(self):
        register_response = self.client.post(
            '/conversation/create/',
            headers={'Authorization': f'Bearer {self.host_jwt}'},
            json={
                'user_ids': self.conv_users,
                'conv_name': 'Test conversation'
            }
        )
        self.assertTrue(isinstance(register_response.json(), dict))
        self.assertIn('id', register_response.json())
        self.addAsyncCleanup(
            self.delete_conversation,
            register_response.json().get('id')
        )

    async def test_request_users_chats(self):
        """
            requests chat list
            :return:
        """
        async with aiohttp.ClientSession() as ses:
            host_resp = await ses.get(
                url=OBTAIN_USER_PROFILE_URL,
                headers={'Authorization': f'Bearer {self.host_jwt}'}
            )
        conv_prep = ConversationRoom(
            host_data=await host_resp.json(),
            user_ids=set(self.conv_users),
            conv_name='TEST 1'
        )
        conversation = await conv_prep.asave(self.async_ses)
        await self.async_ses.commit()
        self.assertIsNotNone(conversation.id)
        response = self.client.get(
            '/conversation/list/',
            headers={'Authorization': f'Bearer {self.host_jwt}'},
        )
        self.assertIsInstance(response.json(), list)
        self.assertTrue(len(response.json()) > 0)
        self.assertEqual(response.json()[0].get('id'), conversation.id)
        self.addAsyncCleanup(
            self.delete_conversation,
            conversation.id
        )

    async def delete_conversation(self, conv_id):
        rollback_conv_ses = AsyncSession(bind=engine, expire_on_commit=True)
        instance = await rollback_conv_ses.get(
            ConversationModel,
            {'id': conv_id}
        )
        await rollback_conv_ses.delete(
            instance
        )
        await rollback_conv_ses.commit()
        await rollback_conv_ses.close()

    async def asyncTearDown(self) -> None:
        all_users = self.conv_users
        all_users.append(JWT.decrypt(self.host_jwt).get('user_id'))
        for user_id in all_users:
            instance = await self.async_ses.get(
                User, {'id': user_id}
            )
            if instance is not None:
                await self.async_ses.delete(
                    instance
                )
        await self.async_ses.commit()
        await self.async_ses.close()
