from enum import unique, Enum


class ComponentProperties:
    def __init__(self, density=1):
        self.density = density


@unique
class Component(Enum):
    GIN = ComponentProperties()
    TONIC = ComponentProperties()
    RUM = ComponentProperties()
    COLA = ComponentProperties()


GIN_TONIC = [  # 1:2, total 345ml + ice & lime
    (Component.GIN, 115),
    (Component.TONIC, 230)
]


CUBA_LIBRE = [  # total 170 + lime
    (Component.RUM, 50),
    (Component.COLA, 120)
]

