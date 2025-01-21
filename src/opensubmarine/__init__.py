from opensubmarine.contracts.access.Ownable.contract import Ownable, OwnableInterface
from opensubmarine.contracts.participation.Stakable.contract import Stakeable
from opensubmarine.contracts.update.Upgradeable.contract import Upgradeable
from opensubmarine.contracts.factory.Deployable.contract import Deployable
from opensubmarine.contracts.factory.Factory.contract import BaseFactory


__version__ = "0.1.7"

__all__ = [
    "Ownable",
    "OwnableInterface",
    "Stakeable",
    "Upgradeable",
    "Deployable",
    "BaseFactory",
]

OpenSubmarine_version = __version__
