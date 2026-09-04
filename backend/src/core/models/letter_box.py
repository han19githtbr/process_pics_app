from dataclasses import dataclass
from typing import Optional

@dataclass
class LetterBox:
    """Representa uma caixa delimitadora de letra."""
    x: int
    y: int
    width: int
    height: int
    area: int
    confidence: float
    id: Optional[int] = None
    line: Optional[int] = None
    image: Optional[str] = None
    confidence_details: Optional[dict] = None

    def __post_init__(self):
        """Garante tipos nativos do Python (evita numpy.intc/float32 no JSON)."""
        self.x = int(self.x)
        self.y = int(self.y)
        self.width = int(self.width)
        self.height = int(self.height)
        self.area = int(self.area)
        self.confidence = float(self.confidence)
        if self.id is not None:
            self.id = int(self.id)
        if self.line is not None:
            self.line = int(self.line)
    
    @property
    def aspect_ratio(self) -> float:
        """Retorna a proporção largura/altura."""
        return self.width / max(self.height, 1)
    
    @property
    def center_x(self) -> float:
        """Retorna a coordenada X do centro."""
        return self.x + self.width / 2
    
    @property
    def center_y(self) -> float:
        """Retorna a coordenada Y do centro."""
        return self.y + self.height / 2
