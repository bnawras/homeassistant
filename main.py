#!/home/bnawras/Documents/src/notifier/.venv/bin/python
import asyncio
import pickle
import logging.config

from handlers.cards import register_irregular_en_verb_cards
from handlers.common import register_common_handlers
from handlers.photos import register_photos_handler
from handlers.weather import register_weather_handlers
from utils import (
    init_logging,
    load_config,
    build_client,
    deleted_messages,
    deleted_ids_storage,
    create_restore_tasks,
    scheduler,
)

init_logging()
logger = logging.getLogger(__name__)
config = load_config('config.yaml')
client = build_client(config)

register_common_handlers(client)
register_irregular_en_verb_cards(client)
family = config['telegram']['family']
register_weather_handlers(client, config['open-weather'], family)
register_photos_handler(client, config['yandex-disk'], family)


async def start_scheduler():
    while True:
        if client.loop.is_running():
            scheduler.start()
            logger.info('Scheduler started')
            return
        else:
            await asyncio.sleep(1)


family = config['telegram']['family']

try:
    loop = asyncio.get_event_loop()
    loop.create_task(create_restore_tasks(client))
    loop.create_task(start_scheduler())
    client.run_until_disconnected()
finally:
    with open(deleted_ids_storage, 'wb') as file:
        pickle.dump(deleted_messages, file)