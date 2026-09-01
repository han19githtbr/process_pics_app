from abc import ABC, abstractmethod
import numpy as np
from typing import Tuple

class IImageProcessor(ABC):
    """Interface para processamento de imagens."""
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Pré-processa a imagem para segmentação."""
        pass
    
    @abstractmethod
    def resize_if_needed(self, image: np.ndarray, max_size: int = 1800) -> Tuple[np.ndarray, float]:
        """Redimensiona imagem se necessário."""
        pass
    
    @abstractmethod
    def binarize(self, image: np.ndarray, method: str = 'auto') -> np.ndarray:
        """Binariza a imagem."""
        pass