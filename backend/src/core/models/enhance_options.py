from dataclasses import dataclass


@dataclass
class EnhanceOptions:
    """Opções de melhoria de qualidade de imagem (Banco de Imagens de Alta Qualidade).

    modo 'auto' (padrão): cada técnica (denoise, contraste, nitidez) é calibrada
    automaticamente a partir de métricas físicas medidas na própria imagem de entrada
    (ver QualityEnhancer._measure_*). modo 'manual': os parâmetros abaixo (0..1) são
    usados diretamente, mapeados para a faixa efetiva de cada operador do OpenCV.
    """
    mode: str = 'auto'  # 'auto' ou 'manual'
    denoise_strength: float = 0.5  # 0..1 (usado apenas no modo manual)
    sharpen_amount: float = 0.5  # 0..1 (usado apenas no modo manual)
    clahe_clip_limit: float = 2.5  # usado diretamente no modo manual
    target_glyph_height: float = 46.0  # altura alvo (px) para a escala adaptativa de texto pequeno
    max_upscale_factor: float = 4.0
    max_dimension: int = 3600
    max_input_size: int = 2000  # teto de segurança de entrada antes do processamento pesado

    @classmethod
    def from_dict(cls, data: dict) -> 'EnhanceOptions':
        """Cria opções a partir de um dicionário (payload JSON do frontend)."""
        return cls(
            mode=str(data.get('mode', 'auto')),
            denoise_strength=float(data.get('denoiseStrength', data.get('denoise_strength', 0.5))),
            sharpen_amount=float(data.get('sharpenAmount', data.get('sharpen_amount', 0.5))),
            clahe_clip_limit=float(data.get('claheClipLimit', data.get('clahe_clip_limit', 2.5))),
            target_glyph_height=float(data.get('targetGlyphHeight', data.get('target_glyph_height', 46.0))),
            max_upscale_factor=float(data.get('maxUpscaleFactor', data.get('max_upscale_factor', 4.0))),
            max_dimension=int(data.get('maxDimension', data.get('max_dimension', 3600))),
            max_input_size=int(data.get('maxInputSize', data.get('max_input_size', 2000))),
        )
