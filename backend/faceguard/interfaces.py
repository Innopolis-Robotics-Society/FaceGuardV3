from abc import ABC, abstractmethod
import numpy as np


class FaceProviderInterface(ABC):
    @abstractmethod
    def extract_embedding(self, frame: np.ndarray):
        pass
