from pydantic import BaseModel


class Item(BaseModel):

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Role (optional) """
    role: str


    def __init__(self, name: str, description: str, image: str, role: str = None):
        self.name = name
        self.description = description
        self.image = image
        self.role = role
