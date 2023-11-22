import json
import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


DIR = os.path.dirname(__file__)


class Item():

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Role (optional) """
    role: Optional[str]


    def __init__(self, name: str, description: str, image: str, role: Optional[str] = None) -> None:
        self.name = name
        self.description = description
        self.image = image
        self.role = role

    def to_dict(self):
        res = {
            "name": self.name,
            "description": self.description,
            "image": self.image
        }

        if self.role is not None:
            res["role"] = self.role

        return res

    @staticmethod
    def from_dict(d: dict):
        return Item(**d)

    def get_image(self):
        return Image.open(os.path.join(DIR, "img", self.image))


class Shop():
    """ Currency name """
    currency: str

    """ Currency emoji """
    currency_emoji: str

    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, currency: str, currency_emoji: str, name: str = None, to_buy: dict = {}, to_sell: dict = {}):
        if name is None:
            name = f"{currency.title()} shop"

        self.currency = currency
        self.currency_emoji = currency_emoji
        self.name = name
        self.to_buy = to_buy
        self.to_sell = to_sell

    def to_dict(self):
        return {
            "currency": self.currency,
            "currency_emoji": self.currency_emoji,
            "name": self.name,
            "to_buy": self.to_buy,
            "to_sell": self.to_sell
        }

    @staticmethod
    def from_dict(d: dict):
        return Shop(**d)


def get_emoji_img(emoji: str, size: tuple) -> Image.Image:
    if ".png" in emoji:
        return Image.open(os.path.join(DIR, "img", emoji)).convert("RGBA").resize(size)

    name = "-".join(map(lambda e: hex(ord(e))[2:], emoji)) + ".png"
    path = os.path.join(DIR, "img", "72x72", name)
    print(path)

    if os.path.exists(path):
        return Image.open(path).convert("RGBA").resize(size)
    else:
        font = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 24)
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), emoji, font=font, fill="white")
        return img


def get_shop_image_to_buy(shop, items: dict[str, Item]):
    font = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 32)
    img = Image.open(os.path.join(DIR, "img", "background.png"))
    draw = ImageDraw.Draw(img)

    for i, itemprice in enumerate(shop.to_buy.items()):
        itm, price = itemprice
        item = items[itm]

        x = (i % 4) * 300 + 110
        y = (i // 4) * 300 + 110
        itemimg = item.get_image().resize((160, 160))
        img.paste(itemimg, (x, y), itemimg)

        _, _, w, _ = draw.textbbox((0, 0), item.name, font=font)
        tx = x + 80 - w // 2
        ty = y + 170
        draw.text((tx, ty), item.name, font=font, fill='white')

        currency_img = get_emoji_img(shop.currency_emoji, (48, 48))

        pricetxt = f"{int(price)} "
        _, _, w, _ = draw.textbbox((0, 0), pricetxt, font=font)
        tx = x + 80 - w // 2 - currency_img.size[0] // 2
        ty = y + 210
        draw.text((tx, ty), pricetxt, font=font, fill='white')
        img.paste(currency_img, (tx + w, ty - 8), currency_img)

    return img


def get_shop_image_to_sell(shop, items: dict[str, Item]):
    font = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 32)
    img = Image.open(os.path.join(DIR, "img", "background2.png"))
    draw = ImageDraw.Draw(img)

    for i, itemprice in enumerate(shop.to_sell.items()):
        itm, price = itemprice
        item = items[itm]

        x = (i % 4) * 300 + 110
        y = (i // 4) * 300 + 110
        itemimg = item.get_image().resize((160, 160))
        img.paste(itemimg, (x, y), itemimg)

        _, _, w, _ = draw.textbbox((0, 0), item.name, font=font)
        tx = x + 80 - w // 2
        ty = y + 170
        draw.text((tx, ty), item.name, font=font, fill='white')

        currency_img = get_emoji_img(shop.currency_emoji, (48, 48))

        pricetxt = f"{int(price)} "
        _, _, w, _ = draw.textbbox((0, 0), pricetxt, font=font)
        tx = x + 80 - w // 2 - currency_img.size[0] // 2
        ty = y + 210
        draw.text((tx, ty), pricetxt, font=font, fill='white')
        img.paste(currency_img, (tx + w, ty - 8), currency_img)

    return img



if __name__ == "__main__":
    with open(os.path.join(DIR, "data.json"), encoding='utf8') as f:
        data = json.load(f)

    items = {}
    for k, v in data["items"].items():
        items[k] = Item.from_dict(v)

    for s in data["shops"]:
        shop = Shop.from_dict(s)
        filename = f"to_buy_{hash(json.dumps(shop.to_dict()))}.png"
        path = os.path.join(DIR, "img", "shops", filename)

        if not os.path.exists(path):
            img = get_shop_image_to_buy(shop, items)
            img.save(path)

        filename = f"to_sell_{hash(json.dumps(shop.to_dict()))}.png"
        path = os.path.join(DIR, "img", "shops", filename)

        if not os.path.exists(path):
            img = get_shop_image_to_sell(shop, items)
            img.save(path)
