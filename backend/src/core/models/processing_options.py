from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ProcessingOptions:
    """Opções de processamento da segmentação baseadas no trabalho acadêmico (PDF) e melhorias."""
    threshold_mode: str = 'auto'
    sensitivity: float = 0.44
    padding: int = 4
    min_letter_size: int = 3
    max_letter_size: int = 1500
    remove_noise: bool = True
    enhance_contrast: bool = True
    max_image_size: int = 1800
    # Parâmetros específicos do documento acadêmico (PDF UFRRJ)
    mode: str = 'enhanced'  # 'academic' (PDF puro) ou 'enhanced' (PDF + melhorias de precisão)
    split_grouped_letters: bool = True  # Análise de projeção vertical para separar letras coladas
    filter_non_letters: bool = True  # Filtragem morfológica de linhas, molduras e ruídos
    bilateral_d: int = 10  # Diâmetro de vizinhança do Filtro Bilateral (especificado no PDF)
    bilateral_sigma_color: int = 75  # Filtro de espaço de cor do Bilateral (especificado no PDF)
    bilateral_sigma_space: int = 75  # Filtro de espaço de coordenadas do Bilateral (especificado no PDF)
    canny_low: int = 70  # Limiar mínimo de Canny (especificado no PDF)
    canny_high: int = 150  # Limiar máximo de Canny (especificado no PDF)

    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessingOptions':
        """Cria opções a partir de um dicionário."""
        return cls(
            threshold_mode=data.get('thresholdMode', data.get('threshold_mode', 'auto')),
            sensitivity=float(data.get('sensitivity', 0.44)),
            padding=int(data.get('padding', 4)),
            min_letter_size=int(data.get('minLetterSize', data.get('min_letter_size', 3))),
            max_letter_size=int(data.get('maxLetterSize', data.get('max_letter_size', 1500))),
            remove_noise=bool(data.get('removeNoise', data.get('remove_noise', True))),
            enhance_contrast=bool(data.get('enhanceContrast', data.get('enhance_contrast', True))),
            max_image_size=int(data.get('maxImageSize', data.get('max_image_size', 1800))),
            mode=str(data.get('mode', 'enhanced')),
            split_grouped_letters=bool(data.get('splitGroupedLetters', data.get('split_grouped_letters', True))),
            filter_non_letters=bool(data.get('filterNonLetters', data.get('filter_non_letters', True))),
            bilateral_d=int(data.get('bilateralD', data.get('bilateral_d', 10))),
            bilateral_sigma_color=int(data.get('bilateralSigmaColor', data.get('bilateral_sigma_color', 75))),
            bilateral_sigma_space=int(data.get('bilateralSigmaSpace', data.get('bilateral_sigma_space', 75))),
            canny_low=int(data.get('cannyLow', data.get('canny_low', 70))),
            canny_high=int(data.get('cannyHigh', data.get('canny_high', 150))),
        )
