from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ProcessingOptions:
    """Opções de processamento da segmentação."""
    threshold_mode: str = 'auto'
    sensitivity: float = 0.44
    padding: int = 4
    min_letter_size: int = 3
    max_letter_size: int = 1500
    remove_noise: bool = True
    enhance_contrast: bool = True
    max_image_size: int = 1800
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessingOptions':
        """Cria opções a partir de um dicionário."""
        return cls(
            threshold_mode=data.get('thresholdMode', 'auto'),
            sensitivity=float(data.get('sensitivity', 0.44)),
            padding=int(data.get('padding', 4)),
            min_letter_size=int(data.get('minLetterSize', 5)),
            max_letter_size=int(data.get('maxLetterSize', 200)),
            remove_noise=bool(data.get('removeNoise', True)),
            enhance_contrast=bool(data.get('enhanceContrast', True)),
            max_image_size=int(data.get('maxImageSize', 1800))
        )
