"""
Denon Heos notification service.
"""
import asyncio

import re
import logging
import voluptuous as vol

from homeassistant.components.media_player import (MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import ( # pylint: disable=no-name-in-module
    MEDIA_TYPE_MUSIC,
    SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET, # SUPPORT_VOLUME_STEP,
    SUPPORT_STOP, SUPPORT_PAUSE, SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK, SUPPORT_SEEK,
    SUPPORT_PLAY)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_USERNAME, CONF_PASSWORD, STATE_PAUSED, STATE_PLAYING, STATE_UNKNOWN, STATE_OFF)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/Lampy09/aioheos/archive/v0.1.7.zip#aioheos==0.1.7']

DEFAULT_NAME = 'HEOS Player'

SUPPORT_HEOS = SUPPORT_PLAY | SUPPORT_STOP | SUPPORT_PAUSE | SUPPORT_PLAY_MEDIA | \
        SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | \
        SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | SUPPORT_SEEK

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
})

_LOGGER = logging.getLogger(__name__)

# from aioheos import AioHeos, AioHeosException
#from aioheos import AioHeos # pylint: disable=wrong-import-position

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discover_info=None):
    # pylint: disable=unused-argument
    """Setup the HEOS platform."""

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    hass.loop.set_debug(False)
    heos = HeosMediaPlayer(hass, host, name, username, password)

    yield from heos.heos.connect(
        host=host,
        callback=heos.async_update_ha_state
        )

    async_add_devices([heos])


class HeosMediaPlayer(MediaPlayerDevice):
    """ The media player ."""
    # pylint: disable=abstract-method
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    def __init__(self, hass, host, name, username, password):
        """Initialize"""
        from aioheos import AioHeos
        if host is None:
            _LOGGER.info('No host provided, will try to discover...')
        self._hass = hass
        self.heos = AioHeos(loop=hass.loop, host=host, username=username, password=password, verbose=True)
        self._name = name
        self._state = None

    @asyncio.coroutine
    def async_update(self):
        """Retrieve latest state."""
        self.heos.request_play_state()
        self.heos.request_mute_state()
        self.heos.request_volume()
        self.heos.request_now_playing_media()
        return True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def volume_level(self):
        """Volume level of the device (0..1)."""
        volume = self.heos.get_volume()
        return float(volume) / 100.0

    @property
    def state(self):
        self._state = self.heos.get_play_state()
        if self._state == 'stop':
            return STATE_OFF
        elif self._state == 'pause':
            return STATE_PAUSED
        elif self._state == 'play':
            return STATE_PLAYING
        else:
            return STATE_UNKNOWN

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MEDIA_TYPE_MUSIC

    @property
    def media_artist(self):
        """Artist of current playing media."""
        return self.heos.get_media_artist()

    @property
    def media_title(self):
        """Album name of current playing media."""
        return self.heos.get_media_song()

    @property
    def media_album_name(self):
        """Album name of current playing media."""
        return self.heos.get_media_album()

    @property
    def media_image_url(self):
        """Return the image url of current playing media."""
        return self.heos.get_media_image_url()

    @property
    def media_content_id(self):
        """Return the content ID of current playing media."""
        return self.heos.get_media_id()

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        muted_state = self.heos.get_mute_state()
        return muted_state == 'on'

    @asyncio.coroutine
    def async_mute_volume(self, mute): # pylint: disable=unused-argument
        """Mute volume"""
        self.heos.toggle_mute()

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self.heos.get_duration()/1000.0

    @property
    def media_position_updated_at(self):
        return self.heos.get_position_updated_at()

    @property
    def media_position(self):
        return self.heos.get_position()/1000.0

    @asyncio.coroutine
    def async_media_next_track(self):
        """Go TO next track."""
        self.heos.request_play_next()

    @asyncio.coroutine
    def async_media_previous_track(self):
        """Go TO previous track."""
        self.heos.request_play_previous()

    @asyncio.coroutine
    def async_media_seek(self, position):
        # pylint: disable=no-self-use
        """Seek to posistion."""
        print('MEDIA SEEK', position)

    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HEOS

    @asyncio.coroutine
    def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self.heos.set_volume(volume * 100)

    @asyncio.coroutine
    def async_media_play(self):
        """Play media player."""
        self.heos.play()

    @asyncio.coroutine
    def async_media_stop(self):
        """Stop media player."""
        self.heos.stop()

    @asyncio.coroutine
    def async_media_pause(self):
        """Pause media player."""
        self.heos.pause()

    @asyncio.coroutine
    def async_media_play_pause(self):
        """Play or pause the media player."""
        if self._state == 'play':
            yield from self.async_media_pause()
        else:
            yield from self.async_media_play()

    @asyncio.coroutine
    def async_play_media(self, media_type, media_id, **kwargs):
        # URL
        if re.match(r'http?://', str(media_id)):
            self.heos.play_content(media_id)
        # FAVOURITE
        else:
            favourites = self.heos.get_favourites()
            index = int(media_id)
            if index < len(favourites):
                mid = favourites[index]['mid']
                self.heos.play_favourite(mid)