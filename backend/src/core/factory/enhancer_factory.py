from ..interfaces.image_enhancer import IImageEnhancer
from ..models.enhance_options import EnhanceOptions
from ..enhancers.quality_enhancer import QualityEnhancer


class EnhancerFactory:
    """Factory para criar melhoradores de qualidade de imagem."""

    @staticmethod
    def create_enhancer(options: EnhanceOptions = None) -> IImageEnhancer:
        """Cria um melhorador de qualidade de imagem."""
        return QualityEnhancer(options)

    @staticmethod
    def create_default_enhancer() -> IImageEnhancer:
        """Cria um melhorador de qualidade de imagem com opções padrão (modo automático)."""
        return QualityEnhancer(EnhanceOptions())
