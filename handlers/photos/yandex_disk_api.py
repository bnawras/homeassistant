import logging
import os
import queue
import random
import asyncio

import httpx


class YandexDiskApi:
    _base_url = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def __init__(self, token):
        headers = {'Authorization': f'OAuth {token}'}
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(headers=headers, transport=transport)

        response_fields = ['name', 'path', 'type', 'mime_type', 'created']
        self._params = dict(
            limit=50,
            offset=0,
            fields=','.join([f'_embedded.items.{i}' for i in response_fields])
        )

    async def get_files_paths(self, folder):
        folders = queue.Queue()
        folders.put(folder)

        files_paths = set()
        while not folders.empty():
            self._params['path'] = folders.get()
            self._params['offset'] = 0

            while True:
                response = await self._client.get(self._base_url, params=self._params)
                response.raise_for_status()
                files = response.json().get('_embedded').get('items')

                # TODO: add filters
                for file in files:
                    if file['type'] == 'dir':
                        folders.put(file['path'])
                        continue

                    if any([i in file['mime_type'] for i in ['jpeg', 'jpg', 'png']]):
                        files_paths.add(file['path'])

                if len(files) < self._params['limit']:
                    break

                self._params['offset'] += self._params['limit']

        return files_paths

    async def download_file(self, path):
        response = await self._client.get(f'{self._base_url}download', params=dict(path=path))

        response.raise_for_status()

        file = await self._client.get(response.json()['href'], follow_redirects=True)
        return file.read()


class SampleReader:
    def __init__(self, storage_api, storage_folder_path, excluded_files_path='.excluded_files.txt'):
        self._excluded_files_path = excluded_files_path
        self._storage_api = storage_api
        self._storage_folder_path = storage_folder_path
        self._excluded_files_cache = []
        self._files = None

    async def read(self):
        if self._files is None:
            logging.info('Индексация фотографий...')
            self._files = await self._index_files(self._excluded_files_path)
            logging.info(f'Проиндексировано {len(self._files)} фотографий...')
        elif not len(self._files):
            self._files = await self._index_files()

        if not self._files:
            raise StopAsyncIteration('Files not found')

        file_path = random.sample(self._files, 1)[0]
        self._files.remove(file_path)
        self._excluded_files_cache.append(file_path)

        if len(self._excluded_files_cache) > 50:
            self._update_excluded(self._excluded_files_cache)
            self._excluded_files_cache.clear()

        return await self._storage_api.download_file(file_path)

    async def _index_files(self, excluded_files_path=None):
        files = await self._storage_api.get_files_paths(self._storage_folder_path)

        if not excluded_files_path or not os.path.exists(excluded_files_path):
            return files

        with open(excluded_files_path) as file:
            excluded = set(file.readlines())

        return list(files - excluded)

    def _update_excluded(self, sample):
        with open(self._excluded_files_path, 'a') as file:
            file.writelines(sample)