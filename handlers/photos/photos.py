import io
from telethon import events, TelegramClient
from telethon.events.newmessage import NewMessage

from .yandex_disk_api import SampleReader, YandexDiskApi
from utils import scheduler

def register_photos_handler(client: TelegramClient, config, family):
    storage = YandexDiskApi(config['api_token'])
    sampler = SampleReader(storage, config['photos_directory'])

    @client.on(events.NewMessage(pattern='.*фото.*'))
    async def family_photos(event: NewMessage.Event):
        await send_family_photos(event.chat_id)

    async def send_family_photos(chat_id):
        images = []
        for _ in range(5):
            img_bytes = await sampler.read()
            image = io.BytesIO(img_bytes)
            image.name = 'photo.jpg'
            images.append(image)

        caption_text = 'Жизнь прекрасна!'

        return await client.send_file(
            entity=chat_id,
            file=images,
            caption=caption_text,
            force_document=False,
            album=True
        )

    scheduler.add_job(send_family_photos, 'cron', hour=12, args=[family])
