# pythonalsa

Python bindings for ALSA (Advanced Linux Sound Architecture) using ctypes. Control audio mixers, volume levels, and mute states directly from Python without external dependencies.

## Features

- Pure Python implementation using ctypes (no compiled extensions)
- Control volume levels (raw values and percentages)
- Mute/unmute audio channels
- List all available sound cards and mixer elements
- Clean, Pythonic API with context managers

## Requirements

- Python 3.9 or higher
- Linux system with ALSA (`libasound.so.2`)

## Installation

```bash
pip install pythonalsa
```

## Usage

```python
from pythonalsa import Card, Mixer, list_cards

# Get the default card
card = Card()
print(f"Default card: {card.name}")

# Or get a specific card
card = Card(0)

# List all cards
for card in list_cards():
    print(f"Card {card.index}: {card.name}")

# List mixers for a card
for mixer in card.list_mixers():
    print(f"Mixer: {mixer.name}")

# Get a specific mixer
mixer = card.get_mixer("Master")

# Or create mixer directly
mixer = Mixer(card=card, name="Master")

# Volume control
print(f"Current volume: {mixer.volume_percent}%")
mixer.volume_percent = 75

# Raw volume
min_vol, max_vol = mixer.volume_range
print(f"Volume range: {min_vol} - {max_vol}")
mixer.volume = 23

# Mute control
print(f"Muted: {mixer.muted}")
mixer.muted = True
mixer.muted = False
```

## API Reference

See docstrings for `Card`, `Mixer`, `iter_cards`, and `ALSAError`.

## License

GPL-3.0-or-later

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
