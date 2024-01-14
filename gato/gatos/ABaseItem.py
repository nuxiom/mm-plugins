from abc import ABC
from enum import Enum
from random import random


class ItemType(Enum):
    CONSUMABLE = 1
    EQUIPEMENT = 2
    GATO = 3


class ABaseItem(ABC):
    """**Abstract class** to implement for every item (yes, gatos are items).

    Attributes starting with a `_` should not be modified manually.
    Attributes in CAPS are constants."""

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    """Sprite of the item. **OVERRIDE IT!**"""

    ANIMATIONS: str = "3star"
    """A reference to a key in `animations.json`. **OVERRIDE IT!**"""

    DISPLAY_NAME: str = "Base Item"
    """Display name of this item. **OVERRIDE IT!**"""

    RARITY: int = 3
    """Rarity of the item in stars (3-5). **OVERRIDE IT!**"""

    ITEM_TYPE: ItemType = ItemType.CONSUMABLE
    """Type of the item. **OVERRIDE IT!**"""

