from ..interfaces.letter_segmenter import ILetterSegmenter
from ..models.processing_options import ProcessingOptions
from ..segmenters.improved_segmenter import ImprovedSegmenter

class SegmenterFactory:
    """Factory para criar segmentadores."""
    
    @staticmethod
    def create_segmenter(options: ProcessingOptions = None) -> ILetterSegmenter:
        """Cria um segmentador de letras."""
        return ImprovedSegmenter(options)
    
    @staticmethod
    def create_default_segmenter() -> ILetterSegmenter:
        """Cria um segmentador com opções padrão."""
        return ImprovedSegmenter(ProcessingOptions())