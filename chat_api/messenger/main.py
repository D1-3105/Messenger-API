import uvicorn
from chat_api import messenger

if __name__ == '__main__':
    uvicorn.run(messenger.app, host='0.0.0.0', port=8002)
