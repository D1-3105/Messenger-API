from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from conf.config import OBTAIN_USER_PROFILE_URL
import aiohttp


async def authenticate(request: Request):
    """
    Authenticates user with auth service
    :param request: Headers: {'Authorization': 'Bearer ...'}
    :return: user_data
    """
    token = request.headers.get('Authorization')
    async with aiohttp.ClientSession() as async_ses:
        user_response = await async_ses.get(
            url=OBTAIN_USER_PROFILE_URL,
            headers={'Authorization': token}
        )
        if user_response.status != 200:
            raise HTTPException(status_code=403)
        return await user_response.json()
