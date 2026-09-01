from abc import ABC, abstractmethod
import numpy as np
from typing import Optional
from ..models.processing_options import ProcessingOptions
from ..models.segment_result import SegmentResult

class ILetterSegmenter(ABC):
    """Interface para segmentação de letras."""
    
    @abstractmethod
    def segment(self, image: np.ndarray, options: Optional[ProcessingOptions] = None) -> SegmentResult:
        """Segmenta letras na imagem."""
        pass
    
    @abstractmethod
    def set_options(self, options: ProcessingOptions) -> None:
        """Define opções de processamento."""
        pass