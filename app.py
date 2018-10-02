#!/usr/bin/env python3

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
    print(request)
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
        with tts.say(text, voice, format_) as read:
            for chunk in read:
                await response.write(chunk)
    except ConnectionResetError as e:
        print(e)
    else:
        return response


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
