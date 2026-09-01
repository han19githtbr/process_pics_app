from abc import ABC, abstractmethod
import numpy as np
from typing import List
from ..models.letter_box import LetterBox

class ILetterValidator(ABC):
    """Interface para validação de letras."""
    
    @abstractmethod
    def validate(self, letter_boxes: List[LetterBox], image: np.ndarray) -> List[LetterBox]:
        """Valida e filtra caixas de letras."""
        pass
    
    @abstractmethod
    def calculate_confidence(self, letter_box: LetterBox, image: np.ndarray) -> float:
        """Calcula confiança de que um componente é uma letra."""
        pass
    
    @abstractmethod
    def is_letter(self, letter_box: LetterBox, image: np.ndarray) -> bool:
        """Verifica se um componente é uma letra."""
        pass