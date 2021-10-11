
import abc
from typing import Dict


class Definition:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse(serialize_definition: Dict):
        return

    @abc.abstractmethod
    def get_sequence(self):
        return
