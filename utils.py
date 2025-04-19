import os
import pickle
import asyncio
import logging
from datetime import datetime
from collections import defaultdict
import logging.config

import yaml
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
print('=' * 60)
scheduler = AsyncIOScheduler()

def init_logging():
    with open('logging.yaml', 'r') as logging_file:
        logging_config = yaml.load(logging_file, Loader=yaml.FullLoader)
        logging.config.dictConfig(logging_config)

def load_config(path):
    with open(path, 'r') as config_file:
        return yaml.load(config_file, Loader=yaml.FullLoader)

def build_client(config):
    app = TelegramClient(
        session='home-assistant',
        api_id=config['telegram']['api_id'],
        api_hash=config['telegram']['api_hash'],
    )
    return app.start(bot_token=config['telegram']['api_token'])

deleted_messages = defaultdict(set)
async def delete_message(client, deletion_date, chat_id, message_id):
    message_data = (deletion_date, message_id)
    deleted_messages[chat_id].add(message_data)

    today = datetime.today()
    delay = (deletion_date - today).total_seconds()
    logger.info(f'planned deletion: {message_id}')
    await asyncio.sleep(delay)

    await client.delete_messages(chat_id, message_id)
    deleted_messages[chat_id].discard(message_data)


deleted_ids_storage = '.deleted_images.pickle'
async def create_restore_tasks(client):
    if not os.path.exists(deleted_ids_storage):
        return

    with open(deleted_ids_storage, 'rb') as file:
        undeleted_messages = pickle.load(file)

    for chat_id, messages_date in undeleted_messages.items():
        for date, message_id in messages_date:
            task = delete_message(client, date, chat_id, message_id)
            client.loop.create_task(task)
