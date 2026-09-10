from abc import ABC, abstractmethod
import numpy as np
from typing import Optional
from ..models.enhance_options import EnhanceOptions
from ..models.enhance_result import EnhanceResult


class IImageEnhancer(ABC):
    """Interface para melhoria de qualidade de imagens (nitidez, ruído, contraste e escala)."""

    @abstractmethod
    def enhance(self, image: np.ndarray, options: Optional[EnhanceOptions] = None) -> EnhanceResult:
        """Melhora a qualidade da imagem, preservando cor/tom (ao contrário da binarização de segmentação)."""
        pass

    @abstractmethod
    def set_options(self, options: EnhanceOptions) -> None:
        """Define opções de melhoria de qualidade."""
        pass
