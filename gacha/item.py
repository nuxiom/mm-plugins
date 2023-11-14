from typing import Optional

from pydantic import BaseModel


class Item(BaseModel):

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Role (optional) """
    role: Optional[str]


    def __init__(self, name: str, description: str, image: str, role: Optional[str] = None) -> None:
        sup = super()
        print("Initializing Item, sup is: ", str(sup))
        sup.__init__(name=name, description=description, image=image, role=role)