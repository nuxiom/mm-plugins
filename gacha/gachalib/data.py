from gachalib.banner import Banner
from gachalib.item import Item
from gachalib.shop import Shop

class Data:

    items = {
        "5starRole": Item(
            "5⭐ Role",
            "This is a super rare role!",
            "https://media.discordapp.net/attachments/1106786214608109669/1173895704821907517/ruan_mei_mooncake.png?ex=65659e91&is=65532991&hm=5a9e5f513c124acfbdf05a2c1f02b14df757395aaa0725ca2d1fb25184073f94&=&width={size}&height={size}",
            "Super Lucky Player"
        ),
        "4starCollectible": Item(
            "4⭐ Collectible",
            "This is just a collectible, doesn't give a role but it's nice to have!",
            "https://media.discordapp.net/attachments/1106786214608109669/1173895705329405952/ruan_mei_dumpling.png?ex=65659e92&is=65532992&hm=4a134dee3c3568714b8654fd3109840937589664a2a8bfd1a1a5c3ff892b55ec&=&width={size}&height={size}"
        )
    }


    shops = [
        Shop(
            currency="Plum Blossom",
            to_buy={
                "5starRole": 1e6
            },
            to_sell={
                "4starCollectible": 300
            }
        )
    ]


    banners = [
        Banner(
            "Standard banner",
            {
                1: ["5starRole"],
                2999: ["4starCollectible"]
            }
        )
    ]
