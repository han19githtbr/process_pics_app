from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class EnhanceResult:
    """Resultado da melhoria de qualidade de imagem."""
    enhanced_image: str = ''  # data URL PNG da imagem melhorada
    original_image: str = ''  # data URL PNG da imagem original (para comparação Antes/Depois)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
