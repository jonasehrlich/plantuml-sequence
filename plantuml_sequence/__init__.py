import importlib.metadata

from .diagram import Diagram

__version__ = importlib.metadata.version(__name__)
__all__ = ["Diagram"]
