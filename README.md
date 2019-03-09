# hass.aioheos.media_player

Denon Heos media player for Home Assistant.

## Install

    > cp heos ~/.homeassistant/custom_components/

## Configuration

    media_player:
        platform: heos
        host: <hostname>
        name: Name of the device
        username: <heos_username>
        password: <heos_password>

## Automation example

    - id: '2019'
      alias: Play radio when coming home
      trigger:
      - entity_id: device_tracker.your_device
          from: not_home
          platform: state
          to: home
      condition: []
      action:
      - data:
          entity_id: media_player.heos_player
          volume_level: '0.14'
        service: media_player.volume_set
      - data:
          entity_id: media_player.heos_player
          media_content_id: 0
          media_content_type: 'music'
        service: media_player.play_media

Where `media_content_id` is the index from you favourites list in you Heos app (zero indexed)