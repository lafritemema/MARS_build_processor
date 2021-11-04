
import abc
from typing import Dict


class Definition(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def parse(serialize_definition: Dict):
        return

    @abc.abstractmethod
    def get_sequence(self):
        return

    @abc.abstractmethod
    def to_dict(self):
        return
