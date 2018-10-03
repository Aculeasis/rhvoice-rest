#!/usr/bin/env python3

import asyncio
import threading
from shlex import quote
from urllib import parse

from aiohttp import web

from rhvoice_proxy.rhvoice import TTS
from tools.preprocessing.text_prepare import text_prepare

SUPPORT_VOICES = {
    'aleksandr', 'anna', 'elena', 'irina',  # Russian
    'alan', 'bdl', 'clb', 'slt',  # English
    'spomenka',  # Esperanto
    'natia',  # Georgian
    'azamat', 'nazgul',  # Kyrgyz
    'talgat',  # Tatar
    'anatol', 'natalia'  # Ukrainian
}
DEFAULT_VOICE = 'anna'

FORMATS = {'wav': 'audio/wav', 'mp3': 'audio/mpeg', 'opus': 'audio/ogg'}
DEFAULT_FORMAT = 'mp3'


async def say(request):
    text = ' '.join([x for x in parse.unquote(request.rel_url.query.get('text', '')).splitlines() if x])
    voice = request.rel_url.query.get('voice', DEFAULT_VOICE)
    format_ = request.rel_url.query.get('format', DEFAULT_FORMAT)

    err = None
    if voice not in SUPPORT_VOICES:
        err = 'Unknown voice: \'{}\'. Support: {}.'.format(voice, ', '.join(SUPPORT_VOICES))
    elif format_ not in FORMATS:
        err = 'Unknown format: \'{}\'. Support: {}.'.format(format_, ', '.join(FORMATS))
    elif not text:
        err = 'Unset \'text\'.'
    if err:
        raise web.HTTPBadRequest(text=err)

    text = quote(text_prepare(text))
    response = web.StreamResponse()
    response.content_type = FORMATS[format_]
    await response.prepare(request)
    try:
        if tts.process:
            with AsyncAdapter(tts.say, text, voice, format_) as read:
                async for chunk in read:
                    await response.write(chunk)
        else:
            with tts.say(text, voice, format_) as read:
                for chunk in read:
                    await response.write(chunk)
    except ConnectionResetError as e:
        print('{} "{} {} HTTP/{}.{}"'.format(request.remote, request.method, request.path_qs, *request.version))
        print(e)
    else:
        return response


class AsyncAdapter(threading.Thread):
    def __init__(self, say_func, *params):
        super().__init__()
        self._say = say_func
        self._buff = None
        self._wait = threading.Event()
        self._work = False
        self._params = params

    def run(self):
        with self._say(*self._params) as read:
            for chunk in read:
                self._buff = chunk
                self._wait.wait()
                if self._buff is not None or not self._work:
                    break
                self._wait.clear()
        self._work = False

    def __aiter__(self):
        return self

    def __enter__(self):
        self._work = True
        self.start()
        return self

    def __exit__(self, *_):
        if self._work:
            self._work = False
            self._wait.set()
            self.join()

    async def __anext__(self):
        while self._buff is None:
            if not self._work:
                raise StopAsyncIteration
            await asyncio.sleep(0)
        try:
            return self._buff
        finally:
            self._buff = None
            self._wait.set()


def _get_def(any_, test):
    if test not in any_ and len(any_):
        return any_[0]
    return test


if __name__ == "__main__":
    tts = TTS()

    formats = tts.formats
    DEFAULT_FORMAT = _get_def(formats, DEFAULT_FORMAT)
    FORMATS = {key: val for key, val in FORMATS.items() if key in formats}

    SUPPORT_VOICES = tts.voices
    DEFAULT_VOICE = _get_def(SUPPORT_VOICES, DEFAULT_VOICE)
    SUPPORT_VOICES = set(SUPPORT_VOICES)

    app = web.Application()
    app.add_routes([web.get('/say', say)])
    web.run_app(app, host='0.0.0.0', port=8080)

    tts.join()
