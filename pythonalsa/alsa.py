"""ALSA C library bindings using ctypes."""

from contextlib import contextmanager
from ctypes import (
    CDLL,
    c_char_p,
    c_int,
    c_long,
    c_void_p,
    byref,
    create_string_buffer,
)
from ctypes.util import find_library
from dataclasses import dataclass
from functools import cached_property
from typing import Iterator

_lib = CDLL(find_library("asound"))

# Type aliases
ctl_t = c_void_p
ctl_card_info_t = c_void_p
mixer_t = c_void_p
mixer_elem_t = c_void_p
mixer_selem_id_t = c_void_p

# Configure return types for functions that return pointers
_lib.snd_strerror.restype = c_char_p
_lib.snd_ctl_card_info_get_name.restype = c_char_p
_lib.snd_mixer_first_elem.restype = c_void_p
_lib.snd_mixer_elem_next.restype = c_void_p
_lib.snd_mixer_find_selem.restype = c_void_p
_lib.snd_mixer_selem_id_get_name.restype = c_char_p


class ALSAError(Exception):
    """Exception raised for ALSA errors."""

    pass


def _check_error(err: int, summary: str) -> None:
    """Check error code and raise ALSAError if negative."""
    if err < 0:
        message = _lib.snd_strerror(err).decode()
        raise ALSAError(f"{summary}: {message}")


@dataclass
class Mixer:
    """Represents an ALSA mixer element."""

    card: "Card"
    name: str
    index: int = 0

    @property
    def has_volume_control(self) -> bool:
        """
        Check if mixer element has playback volume control.

        Returns:
            True if playback volume control exists, False otherwise
        """
        with self._make_alsa_elem() as elem:
            return bool(_lib.snd_mixer_selem_has_playback_volume(elem))

    @property
    def has_mute_control(self) -> bool:
        """
        Check if mixer element has playback switch (mute) control.

        Returns:
            True if playback switch control exists, False otherwise
        """
        with self._make_alsa_elem() as elem:
            return bool(_lib.snd_mixer_selem_has_playback_switch(elem))

    @property
    def volume_range(self) -> tuple[int | None, int | None]:
        """
        Get volume range (min, max).

        Returns:
            Tuple of (min, max) volume levels, or (None, None) if element doesn't support playback volume
        """
        if not self.has_volume_control:
            return None, None
        with self._make_alsa_elem() as elem:
            pmin = c_long()
            pmax = c_long()
            _lib.snd_mixer_selem_get_playback_volume_range(
                elem, byref(pmin), byref(pmax)
            )
            return pmin.value, pmax.value

    @contextmanager
    def _make_alsa_elem(self) -> Iterator[mixer_elem_t]:
        """
        Context manager for accessing the mixer element.

        Yields:
            Mixer element handle

        Raises:
            ALSAError: If unable to access mixer element
        """
        with self.card.make_alsa_mixer_handle() as handle:
            sid = create_string_buffer(_lib.snd_mixer_selem_id_sizeof())
            _lib.snd_mixer_selem_id_set_name(sid, self.name.encode("utf-8"))
            _lib.snd_mixer_selem_id_set_index(sid, self.index)
            elem = _lib.snd_mixer_find_selem(handle, sid)
            if not elem:
                raise ALSAError(
                    f"Mixer element '{self.name}' index {self.index} not found"
                )
            yield elem

    @property
    def volume(self) -> int | None:
        """
        Get current raw volume level.

        Returns:
            Raw volume level, or None if element doesn't support playback volume

        Raises:
            ALSAError: If unable to get volume
        """
        if not self.has_volume_control:
            return None

        with self._make_alsa_elem() as elem:
            value = c_long()
            _check_error(
                _lib.snd_mixer_selem_get_playback_volume(elem, 0, byref(value)),
                "Failed to get playback volume",
            )
            return value.value

    @volume.setter
    def volume(self, value: int) -> None:
        """
        Set raw volume level.

        Args:
            value: Raw volume level

        Raises:
            ALSAError: If unable to set volume or element doesn't support playback volume
        """
        if not self.has_volume_control:
            raise ALSAError(
                f"Mixer element '{self.name}' doesn't support playback volume"
            )
        with self._make_alsa_elem() as elem:
            _check_error(
                _lib.snd_mixer_selem_set_playback_volume_all(elem, value),
                "Failed to set playback volume",
            )

    @property
    def volume_percent(self) -> int | None:
        """
        Get current volume as percentage (0-100).

        Returns:
            Volume percentage, or None if element doesn't support playback volume

        Raises:
            ALSAError: If unable to get volume
        """
        raw_vol = self.volume
        if raw_vol is None:
            return None

        vmin, vmax = self.volume_range
        if vmax == vmin:
            return 0
        return round((raw_vol - vmin) * 100 / (vmax - vmin))

    @volume_percent.setter
    def volume_percent(self, value: int) -> None:
        """
        Set volume as percentage (0-100).

        Args:
            value: Volume percentage (0-100)

        Raises:
            ALSAError: If unable to set volume or element doesn't support playback volume
            ValueError: If value not in range 0-100
        """
        if not 0 <= value <= 100:
            raise ValueError(f"Volume must be between 0 and 100, got {value}")

        vmin, vmax = self.volume_range
        if vmin is None or vmax is None:
            raise ALSAError(
                f"Mixer element '{self.name}' doesn't support playback volume"
            )

        raw_vol = round(vmin + (value * (vmax - vmin) / 100))
        self.volume = raw_vol

    @property
    def muted(self) -> bool | None:
        """
        Get current mute state.

        Returns:
            True if muted, False if unmuted, None if element doesn't support mute

        Raises:
            ALSAError: If unable to get mute state
        """
        if not self.has_mute_control:
            return None
        with self._make_alsa_elem() as elem:
            value = c_int()
            _check_error(
                _lib.snd_mixer_selem_get_playback_switch(elem, 0, byref(value)),
                "Failed to get playback switch",
            )
            unmuted = bool(value.value)
            return not unmuted

    @muted.setter
    def muted(self, value: bool) -> None:
        """
        Set mute state.

        Args:
            value: True to mute, False to unmute

        Raises:
            ALSAError: If unable to set mute state or element doesn't support mute
        """
        if not self.has_mute_control:
            raise ALSAError(
                f"Mixer element '{self.name}' doesn't support playback switch"
            )
        with self._make_alsa_elem() as elem:
            _check_error(
                _lib.snd_mixer_selem_set_playback_switch_all(elem, int(not value)),
                "Failed to set playback switch",
            )


class Card:
    """Represents an ALSA sound card."""

    def __init__(self, index: int | None = None):
        """
        Create a Card instance.

        Args:
            index: Card index, or None to use the default card

        Raises:
            ALSAError: If default card is requested but doesn't exist
        """
        if index is None:
            card_index = c_int()
            err = _lib.snd_card_get_index(b"default", byref(card_index))
            if err < 0:
                raise ALSAError("No default card found")
            self.index = card_index.value
        else:
            self.index = index

    @property
    def device(self) -> str:
        return f"hw:{self.index}"

    @cached_property
    def name(self) -> str:
        """
        Get the card name.

        Returns:
            Card name string

        Raises:
            ALSAError: If unable to get card info
        """
        handle = ctl_t()
        _check_error(
            _lib.snd_ctl_open(byref(handle), self.device.encode("utf-8"), 0),
            f"Failed to open control interface [{self.device}]",
        )
        try:
            info = create_string_buffer(_lib.snd_ctl_card_info_sizeof())
            _check_error(
                _lib.snd_ctl_card_info(handle, info), "Failed to get card info"
            )
            return _lib.snd_ctl_card_info_get_name(info).decode()
        finally:
            _lib.snd_ctl_close(handle)

    @contextmanager
    def make_alsa_mixer_handle(self) -> Iterator[mixer_t]:
        """
        Context manager for accessing the card's mixer handle.

        Yields:
            Mixer handle

        Raises:
            ALSAError: If unable to open mixer
        """
        handle = mixer_t()
        _check_error(_lib.snd_mixer_open(byref(handle), 0), "Failed to open mixer")
        try:
            _check_error(
                _lib.snd_mixer_attach(handle, self.device.encode("utf-8")),
                f"Failed to attach mixer to {self.device}",
            )
            _check_error(
                _lib.snd_mixer_selem_register(handle, None, None),
                "Failed to register mixer elements",
            )
            _check_error(_lib.snd_mixer_load(handle), "Failed to load mixer elements")
            yield handle
        finally:
            _lib.snd_mixer_close(handle)

    def list_mixers(self) -> Iterator[Mixer]:
        """
        List all mixer elements for this card.

        Yields:
            Mixer objects for this card.

        Raises:
            ALSAError: If there's an error accessing the card's mixers.
        """
        with self.make_alsa_mixer_handle() as handle:
            elem = _lib.snd_mixer_first_elem(handle)
            while elem:
                sid = create_string_buffer(_lib.snd_mixer_selem_id_sizeof())
                _lib.snd_mixer_selem_get_id(elem, sid)
                name = _lib.snd_mixer_selem_id_get_name(sid).decode()
                index = _lib.snd_mixer_selem_id_get_index(sid)
                yield Mixer(card=self, name=name, index=index)
                elem = _lib.snd_mixer_elem_next(elem)

    def get_mixer(self, name: str, index: int = 0) -> Mixer:
        """
        Get a mixer element by name.

        Args:
            name: Mixer element name (e.g., "Master", "PCM")
            index: Mixer element index (default: 0)

        Returns:
            Mixer object

        Raises:
            ALSAError: If mixer element doesn't exist
        """
        mixer = Mixer(card=self, name=name, index=index)
        # Verify the mixer exists by accessing it
        with mixer._make_alsa_elem():
            pass
        return mixer


def list_cards() -> Iterator[Card]:
    """
    List all available ALSA sound cards.

    Yields:
        Card objects representing available sound cards.

    Raises:
        ALSAError: If there's an error accessing the sound cards.
    """
    card = c_int(-1)
    while True:
        _check_error(_lib.snd_card_next(byref(card)), "Error enumerating cards")
        if card.value == -1:
            break
        yield Card(card.value)
