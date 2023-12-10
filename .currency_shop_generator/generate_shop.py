import hashlib
import json
import os
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


DIR = os.path.dirname(__file__)
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"


def hash2(s: str):
    return hashlib.md5(s.encode()).hexdigest()


class Item():

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Effects """
    effects: dict[str, list]


    def __init__(self, name: str, description: str, image: str, effects: dict[str, list] = {}) -> None:
        self.name = name
        self.description = description
        self.image = image
        self.effects = effects

    def to_dict(self):
        res = {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "effects": self.effects
        }

        return res

    @staticmethod
    def from_dict(d: dict):
        return Item(**d)

    def get_image(self):
        return Image.open(os.path.join(DIR, "..", "currency", "img", "items", self.image))


class Shop():
    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, name: str, to_buy: dict = {}, to_sell: dict = {}):
        self.name = name
        self.to_buy = to_buy
        self.to_sell = to_sell

    def to_dict(self):
        return {
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
    bigfont = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 64)

    imgs = []
    n = 0
    # Split the items in chunks of 8
    to_buys = [list(shop.to_buy.items())[i * 8:(i + 1) * 8] for i in range((len(shop.to_buy) + 8 - 1) // 8 )]
    for to_buy in to_buys:
        img = Image.open(os.path.join(DIR, "img", "background2.png"))
        draw = ImageDraw.Draw(img)

        for i, itemprice in enumerate(to_buy):
            n += 1
            itm, price = itemprice
            item = items[itm]

            x = (i % 4) * 300 + 110
            y = (i // 4) * 300 + 110
            itemimg = item.get_image().resize((160, 160))
            img.paste(itemimg, (x, y), itemimg)
            draw.text((x - 40, y - 40), f"#{n}", font=bigfont, fill='white', stroke_fill='black', stroke_width=2)

            _, _, w, _ = draw.textbbox((0, 0), item.name, font=font)
            tx = x + 80 - w // 2
            ty = y + 170
            draw.text((tx, ty), item.name, font=font, fill='white')

            currency_img = get_emoji_img(CURRENCY_EMOJI, (42, 42))

            pricetxt = f"{int(price)} "
            _, _, w, _ = draw.textbbox((0, 0), pricetxt, font=font)
            tx = x + 80 - w // 2 - currency_img.size[0] // 2
            ty = y + 210
            draw.text((tx, ty), pricetxt, font=font, fill='white')
            img.paste(currency_img, (tx + w, ty), currency_img)

        imgs.append(img)

    return imgs


def get_shop_image_to_sell(shop, items: dict[str, Item]):
    font = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 32)
    bigfont = ImageFont.truetype(os.path.join(DIR, "ggsymbola.ttf"), 64)

    imgs = []
    n = 0
    # Split the items in chunks of 8
    to_sells = [list(shop.to_sell.items())[i * 8:(i + 1) * 8] for i in range((len(shop.to_sell) + 8 - 1) // 8 )]
    for to_sell in to_sells:
        img = Image.open(os.path.join(DIR, "img", "background.png"))
        draw = ImageDraw.Draw(img)

        for i, itemprice in enumerate(to_sell):
            n += 1
            itm, price = itemprice
            item = items[itm]

            x = (i % 4) * 300 + 110
            y = (i // 4) * 300 + 110
            itemimg = item.get_image().resize((160, 160))
            img.paste(itemimg, (x, y), itemimg)
            draw.text((x - 40, y - 40), f"#{n}", font=bigfont, fill='white', stroke_fill='black', stroke_width=2)

            _, _, w, _ = draw.textbbox((0, 0), item.name, font=font)
            tx = x + 80 - w // 2
            ty = y + 170
            draw.text((tx, ty), item.name, font=font, fill='white')

            currency_img = get_emoji_img(shop.currency_emoji, (42, 42))

            pricetxt = f"{int(price)} "
            _, _, w, _ = draw.textbbox((0, 0), pricetxt, font=font)
            tx = x + 80 - w // 2 - currency_img.size[0] // 2
            ty = y + 210
            draw.text((tx, ty), pricetxt, font=font, fill='white')
            img.paste(currency_img, (tx + w, ty), currency_img)

        imgs.append(img)

    return imgs



if __name__ == "__main__":
    with open(os.path.join(DIR, "..", "currency", "data.json"), encoding='utf8') as f:
        data = json.load(f)

    items = {}
    for k, v in data["items"].items():
        items[k] = Item.from_dict(v)

    for s in data["shops"]:
        shop = Shop.from_dict(s)
        filename = f"to_buy_{hash2(json.dumps(shop.to_dict()))}_0.png"
        path = os.path.join(DIR, "img", "shops", filename)

        if not os.path.exists(path):
            imgs = get_shop_image_to_buy(shop, items)
            for n, img in enumerate(imgs):
                filename = f"to_buy_{hash2(json.dumps(shop.to_dict()))}_{n}.png"
                path = os.path.join(DIR, "img", "shops", filename)
                img.save(path)

        filename = f"to_sell_{hash2(json.dumps(shop.to_dict()))}_0.png"
        path = os.path.join(DIR, "img", "shops", filename)

        if not os.path.exists(path):
            imgs = get_shop_image_to_sell(shop, items)
            for n, img in enumerate(imgs):
                filename = f"to_sell_{hash2(json.dumps(shop.to_dict()))}_{n}.png"
                path = os.path.join(DIR, "img", "shops", filename)
                img.save(path)
