from dataclasses import dataclass, field
from typing import List, Dict, Any
from .letter_box import LetterBox

@dataclass
class SegmentResult:
    """Resultado da segmentação."""
    letters: List[LetterBox] = field(default_factory=list)
    debug_image: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)
    transcript: str = ''
    steps: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def total_letters(self) -> int:
        """Número total de letras encontradas."""
        return len(self.letters)
    
    @property
    def confidence_score(self) -> float:
        """Pontuação média de confiança."""
        if not self.letters:
            return 0.0
        return sum(l.confidence for l in self.letters) / len(self.letters)

    @property
    def transcript_text(self) -> str:
        """Texto reconstruído em ordem de leitura."""
        return self.transcript or ' '.join(f"L{index + 1}" for index in range(len(self.letters)))
