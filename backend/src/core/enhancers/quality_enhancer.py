import cv2
import numpy as np
import time
from typing import Optional, Dict, Any, List
from ..interfaces.image_enhancer import IImageEnhancer
from ..models.enhance_options import EnhanceOptions
from ..models.enhance_result import EnhanceResult
from ..processors.opencv_processor import OpenCVProcessor
from ..utils.image_utils import ImageUtils


class QualityEnhancer(IImageEnhancer):
    """
    Melhorador de qualidade de imagens de texto para o "Banco de Imagens de Alta
    Qualidade": recupera a legibilidade de fotos/scans de baixa qualidade (borrados,
    ruidosos, com baixo contraste ou com texto muito pequeno) preservando tom e cor.

    Reaproveitamento do algoritmo de segmentação (`ImprovedSegmenter` /
    `OpenCVProcessor`): a etapa de "Escala Adaptativa para Texto Pequeno"
    (`auto_upscale_small_text`) e a estimativa de altura mediana de glifo
    (`estimate_median_glyph_height`) resolvem exatamente o mesmo problema físico
    aqui e no recorte de letras (texto pequeno demais para o processamento seguinte
    produzir um resultado confiável) e por isso são reaproveitadas integralmente,
    sem reescrever a lógica.

    O que NÃO é reaproveitado, e por quê: o núcleo do algoritmo de segmentação
    (binarização de Otsu + Canny + `findContours`) converte deliberadamente a
    imagem em preto-e-branco absoluto para poder isolar e recortar cada letra —
    esse é o oposto do objetivo desta funcionalidade, que é restaurar e preservar
    a imagem original em cor/tons de cinza contínuos. Aplicar a binarização de
    segmentação aqui destruiria a informação de imagem que o usuário quer manter.
    Por isso, as etapas de restauração de qualidade (denoising, balanço de branco,
    CLAHE e nitidez) são técnicas de visão computacional novas, implementadas
    especificamente para este módulo e documentadas abaixo e no GUIA.md.
    """

    def __init__(self, options: Optional[EnhanceOptions] = None):
        self.options = options or EnhanceOptions()
        self.processor = OpenCVProcessor()

    def set_options(self, options: EnhanceOptions) -> None:
        """Define opções de melhoria de qualidade."""
        self.options = options

    # ---------------------------------------------------------------------
    # Passo 1: Métricas de diagnóstico (medidas físicas objetivas dos pixels)
    # ---------------------------------------------------------------------

    def _measure_sharpness(self, image: np.ndarray) -> float:
        """Variância do Laplaciano: energia de alta frequência da imagem. Quanto
        menor o valor, mais borrada/desfocada está a imagem (bordas suaves geram
        pouca variação de segunda derivada)."""
        gray = self.processor.to_grayscale(image)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def _measure_noise(self, image: np.ndarray) -> float:
        """Desvio padrão do resíduo entre a imagem e um filtro de mediana 3x3.
        O filtro de mediana preserva bordas e remove ruído impulsivo, então o
        resíduo isola predominantemente ruído de alta frequência não-estrutural
        (grão de scanner, ruído de sensor de câmera, artefatos de compressão)."""
        gray = self.processor.to_grayscale(image).astype(np.float32)
        median = cv2.medianBlur(gray.astype(np.uint8), 3).astype(np.float32)
        return float(np.std(gray - median))

    def _measure_contrast(self, image: np.ndarray) -> float:
        """Desvio padrão global de luminância (contraste RMS): quanto menor,
        mais uniforme/"lavada" está a distribuição tonal da imagem."""
        gray = self.processor.to_grayscale(image)
        return float(np.std(gray))

    # ---------------------------------------------------------------------
    # Calibração adaptativa de intensidade de cada técnica
    # ---------------------------------------------------------------------

    def _adaptive_denoise_h(self, noise_score: float) -> float:
        """Calibra a força (h) do Non-Local Means a partir do ruído medido no
        Passo 1. Faixas escolhidas empiricamente: abaixo de h=3 o filtro não
        produz efeito perceptível; acima de h=15 começa a borrar traços finos
        de texto junto com o ruído."""
        if self.options.mode == 'manual':
            return float(np.clip(3.0 + self.options.denoise_strength * 17.0, 3.0, 20.0))
        if noise_score < 4:
            return 3.0
        if noise_score < 10:
            return 6.0
        if noise_score < 20:
            return 10.0
        return 15.0

    def _adaptive_clahe_clip(self, contrast_score: float) -> float:
        """Calibra o clipLimit do CLAHE a partir do contraste medido no Passo 1:
        quanto mais "lavada"/uniforme a imagem, maior o limite de realce aplicado
        (o corte evita amplificar ruído de forma descontrolada em blocos quase
        uniformes, que é o principal risco de um clipLimit alto sem calibração)."""
        if self.options.mode == 'manual':
            return float(np.clip(self.options.clahe_clip_limit, 1.0, 6.0))
        if contrast_score < 25:
            return 4.0
        if contrast_score < 45:
            return 3.0
        if contrast_score < 65:
            return 2.0
        return 1.2

    def _adaptive_sharpen_amount(self, sharpness_score: float) -> float:
        """Calibra a intensidade da máscara de nitidez a partir da nitidez medida
        no Passo 1: imagens mais borradas recebem reforço maior; imagens já
        nítidas recebem reforço mínimo para evitar halos e ruído artificial nas
        bordas (sobre-nitidez)."""
        if self.options.mode == 'manual':
            return float(np.clip(0.1 + self.options.sharpen_amount * 1.4, 0.1, 1.5))
        if sharpness_score < 60:
            return 1.4
        if sharpness_score < 150:
            return 1.0
        if sharpness_score < 400:
            return 0.6
        return 0.25

    # ---------------------------------------------------------------------
    # Operadores de restauração
    # ---------------------------------------------------------------------

    def _denoise(self, image: np.ndarray, h: float) -> np.ndarray:
        """Non-Local Means Denoising colorido: para cada pixel, busca blocos de
        pixels semelhantes em TODA a imagem (não apenas na vizinhança imediata,
        como um filtro Gaussiano/mediana convencional) e calcula uma média
        ponderada por similaridade. Remove ruído granular preservando bordas de
        traços, o que é essencial para não perder legibilidade do texto.
        `cv2.fastNlMeansDenoisingColored(img, h, hColor, templateWindowSize, searchWindowSize)`.
        """
        return cv2.fastNlMeansDenoisingColored(
            image, None, h=h, hColor=h, templateWindowSize=7, searchWindowSize=21
        )

    def _white_balance_gray_world(self, image: np.ndarray) -> np.ndarray:
        """Balanço de branco por hipótese de 'mundo cinza': assume que a média
        espacial de cada canal de cor (B, G, R) deveria convergir, em média, para
        um cinza neutro. Corrige matizes amarelados/azulados causados por
        iluminação artificial ou pelo balanço automático de câmeras de celular,
        que reduzem o contraste percebido entre a tinta do texto e o papel.
        ganho_c = clamp(médiaGlobal / média_c, 0.7, 1.4)."""
        result = image.astype(np.float32)
        gray_target = float(np.mean(result))
        for channel in range(3):
            channel_mean = float(np.mean(result[:, :, channel]))
            if channel_mean > 1e-3:
                gain = float(np.clip(gray_target / channel_mean, 0.7, 1.4))
                result[:, :, channel] *= gain
        return np.clip(result, 0, 255).astype(np.uint8)

    def _clahe_contrast(self, image: np.ndarray, clip_limit: float) -> np.ndarray:
        """CLAHE (Contrast Limited Adaptive Histogram Equalization) aplicado
        apenas ao canal L (luminância) do espaço de cor LAB: equaliza o
        histograma em blocos locais (tiles) de 8x8 em vez de globalmente,
        recuperando contraste do traço da tinta contra o papel mesmo sob
        iluminação desigual (sombra de celular, foto tirada em ângulo), sem
        alterar a informação de cor (canais A/B) e sem amplificar ruído de
        crominância."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=max(0.1, clip_limit), tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)
        merged = cv2.merge((l_enhanced, a_channel, b_channel))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    def _unsharp_mask(self, image: np.ndarray, amount: float, sigma: float = 1.4) -> np.ndarray:
        """Máscara de nitidez (Unsharp Masking): subtrai uma versão borrada
        (filtro Gaussiano) da imagem original para isolar os componentes de alta
        frequência (bordas/traços) e soma esse resíduo de volta amplificado,
        recuperando a definição de caracteres afetados por desfoque leve de foco
        ou movimento. I_nítida = I + amount x (I - Gauss_sigma(I))."""
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)

    # ---------------------------------------------------------------------
    # Pipeline principal
    # ---------------------------------------------------------------------

    def enhance(self, image: np.ndarray, options: Optional[EnhanceOptions] = None) -> EnhanceResult:
        """Executa o pipeline completo de restauração de qualidade:
        1. Diagnóstico automático (nitidez, ruído, contraste, altura de glifo)
        2. Escala adaptativa para texto pequeno/borrado (reaproveitada do segmentador)
        3. Redução de ruído adaptativa (Non-Local Means)
        4. Balanço de branco automático (mundo cinza)
        5. Realce de contraste local adaptativo (CLAHE)
        6. Nitidez adaptativa (máscara de nitidez / unsharp masking)
        """
        start_time = time.time()
        if options:
            self.set_options(options)

        original_image = image.copy()

        # Diagnóstico bruto (imagem de entrada, na escala original) — usado só
        # para CALIBRAR a intensidade de cada técnica seguinte (nenhuma etapa usa
        # um valor fixo "chutado") e para a narrativa do Passo 1. Não é usado como
        # baseline da comparação Antes/Depois (ver nota abaixo).
        raw_sharpness = self._measure_sharpness(original_image)
        raw_noise = self._measure_noise(original_image)
        raw_contrast = self._measure_contrast(original_image)
        quick_gray = self.processor.to_grayscale(original_image)
        _, quick_binary = cv2.threshold(quick_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        glyph_height_estimate = self.processor.estimate_median_glyph_height(quick_binary)

        # Teto de segurança: reduz imagens muito grandes antes das operações mais
        # pesadas (Non-Local Means é O(n) por bloco de busca, custoso em imagens
        # de muitos megapixels), preservando desempenho previsível na API.
        processed, _ = self.processor.resize_if_needed(original_image, self.options.max_input_size)

        # Passo 2: Escala Adaptativa para Texto Pequeno/Borrado — reaproveita
        # integralmente `OpenCVProcessor.auto_upscale_small_text`, a mesma rotina
        # usada pelo `ImprovedSegmenter` (ver docstring da classe).
        upscaled, upscale_factor = self.processor.auto_upscale_small_text(
            processed,
            target_height=self.options.target_glyph_height,
            max_factor=self.options.max_upscale_factor,
            max_dimension=self.options.max_dimension,
        )

        # Baseline "justa" da comparação Antes/Depois: medida DEPOIS da escala
        # adaptativa (Passo 2), mas ANTES de qualquer restauração (Passos 3-6).
        # Isso evita uma distorção metodológica: a variância do Laplaciano (e
        # métricas de ruído/contraste correlatas) é sensível à escala da imagem
        # — ampliar por interpolação bicúbica sozinho já reduz a nitidez por
        # pixel sem que nenhuma restauração real tenha ocorrido ainda. Comparar
        # a imagem original (pré-escala) contra o resultado final (pós-escala)
        # penalizaria injustamente o ganho de nitidez trazido pelas etapas
        # seguintes. Medir "antes" e "depois" na mesma resolução de trabalho
        # garante uma comparação de nitidez/ruído/contraste "maçã com maçã".
        sharpness_before = self._measure_sharpness(upscaled)
        noise_before = self._measure_noise(upscaled)
        contrast_before = self._measure_contrast(upscaled)

        # Passo 3: Redução de Ruído Adaptativa
        denoise_h = self._adaptive_denoise_h(raw_noise)
        denoised = self._denoise(upscaled, denoise_h)

        # Passo 4: Balanço de Branco Automático
        balanced = self._white_balance_gray_world(denoised)

        # Passo 5: Realce de Contraste Local Adaptativo (CLAHE)
        clahe_clip = self._adaptive_clahe_clip(raw_contrast)
        contrasted = self._clahe_contrast(balanced, clahe_clip)

        # Passo 6: Nitidez Adaptativa (aplicada por último, sobre a imagem já sem
        # ruído — nitidez antes do denoising amplificaria o próprio ruído)
        sharpen_amount = self._adaptive_sharpen_amount(raw_sharpness)
        sharpened = self._unsharp_mask(contrasted, sharpen_amount)

        final_image = sharpened

        # Métricas finais, medidas da mesma forma que a baseline acima, para
        # permitir uma comparação Antes/Depois honesta, auditável e na mesma
        # escala (não apenas visual).
        sharpness_after = self._measure_sharpness(final_image)
        noise_after = self._measure_noise(final_image)
        contrast_after = self._measure_contrast(final_image)

        techniques_applied: List[str] = [
            (
                f'Escala adaptativa {upscale_factor:.2f}x (interpolação bicúbica, reaproveitada do segmentador de letras)'
                if upscale_factor > 1.01
                else 'Escala adaptativa: não necessária (texto já em tamanho adequado)'
            ),
            f'Redução de ruído Non-Local Means Colorido (h={denoise_h:.1f})',
            'Balanço de branco automático (hipótese de mundo cinza)',
            f'Realce de contraste local CLAHE (clipLimit={clahe_clip:.1f}, blocos 8x8 no canal L/LAB)',
            f'Nitidez adaptativa por máscara de nitidez (amount={sharpen_amount:.2f}, sigma=1.4)',
        ]

        processing_time = time.time() - start_time

        steps = self._build_pipeline_steps(
            original_image=original_image,
            upscaled=upscaled,
            upscale_factor=upscale_factor,
            denoised=denoised,
            denoise_h=denoise_h,
            balanced=balanced,
            contrasted=contrasted,
            clahe_clip=clahe_clip,
            sharpened=sharpened,
            sharpen_amount=sharpen_amount,
            sharpness_before=raw_sharpness,
            noise_before=raw_noise,
            contrast_before=raw_contrast,
        )

        metrics: Dict[str, Any] = {
            'sharpnessBefore': round(sharpness_before, 2),
            'sharpnessAfter': round(sharpness_after, 2),
            'noiseBefore': round(noise_before, 2),
            'noiseAfter': round(noise_after, 2),
            'contrastBefore': round(contrast_before, 2),
            'contrastAfter': round(contrast_after, 2),
            'glyphHeightEstimate': round(glyph_height_estimate, 1),
            'upscaleFactor': round(float(upscale_factor), 4),
            'denoiseH': round(denoise_h, 2),
            'claheClipLimit': round(clahe_clip, 2),
            'sharpenAmount': round(sharpen_amount, 2),
            'processingTime': round(processing_time, 4),
            'techniquesApplied': techniques_applied,
            'comparisonNote': (
                'sharpnessBefore/noiseBefore/contrastBefore são medidos após a escala '
                'adaptativa (Passo 2), na mesma resolução do resultado final — não na '
                'imagem original bruta — para que a comparação Antes/Depois não seja '
                'distorcida pela mudança de escala (ampliar sozinho já altera a variância '
                'do Laplaciano sem nenhuma restauração real).'
            ),
        }

        return EnhanceResult(
            enhanced_image=ImageUtils.encode_to_data_url(final_image),
            original_image=ImageUtils.encode_to_data_url(original_image),
            steps=steps,
            metrics=metrics,
            metadata={
                'width': int(final_image.shape[1]),
                'height': int(final_image.shape[0]),
                'originalWidth': int(original_image.shape[1]),
                'originalHeight': int(original_image.shape[0]),
                'mode': self.options.mode,
            },
        )

    def _build_pipeline_steps(self, **kw) -> List[Dict[str, Any]]:
        """Monta as 6 etapas visuais/explicativas exibidas no frontend, no mesmo
        formato usado pelo Pipeline Viewer da segmentação de letras (step, title,
        technique, formula, description, image em data URL)."""
        original_image = kw['original_image']
        upscaled = kw['upscaled']
        upscale_factor = kw['upscale_factor']
        denoised = kw['denoised']
        denoise_h = kw['denoise_h']
        balanced = kw['balanced']
        contrasted = kw['contrasted']
        clahe_clip = kw['clahe_clip']
        sharpened = kw['sharpened']
        sharpen_amount = kw['sharpen_amount']
        sharpness_before = kw['sharpness_before']
        noise_before = kw['noise_before']
        contrast_before = kw['contrast_before']

        return [
            {
                'step': 1,
                'title': 'Passo 1: Diagnóstico Automático de Qualidade',
                'technique': 'cv2.Laplacian (nitidez) + resíduo de mediana (ruído) + desvio padrão (contraste)',
                'formula': 'Nitidez = Var(Laplaciano(I)); Ruído = sigma(I - mediana3x3(I)); Contraste = sigma(I)',
                'description': (
                    f'Antes de qualquer transformação, a imagem é medida objetivamente: nitidez '
                    f'{sharpness_before:.1f} (variância do Laplaciano — quanto menor, mais borrada), ruído '
                    f'{noise_before:.1f} (desvio padrão do resíduo de alta frequência) e contraste '
                    f'{contrast_before:.1f} (desvio padrão global de luminância). Esses três números '
                    'calibram a intensidade de cada etapa seguinte — a imagem não recebe um filtro fixo '
                    'igual para todas as imagens, e sim uma prescrição adaptada ao problema físico '
                    'diagnosticado nela.'
                ),
                'image': ImageUtils.encode_to_data_url(original_image),
            },
            {
                'step': 2,
                'title': 'Passo 2: Escala Adaptativa para Texto Pequeno/Borrado',
                'technique': 'OpenCVProcessor.auto_upscale_small_text (reaproveitado do módulo de segmentação de letras)',
                'formula': f'fator = min(fator_max, altura_alvo / altura_mediana_glifo) -> {upscale_factor:.2f}x',
                'description': (
                    'Reaproveita integralmente a mesma rotina de escala adaptativa usada no recorte de '
                    'letras: estima a altura mediana dos caracteres por uma binarização auxiliar rápida e '
                    'amplia a imagem por interpolação bicúbica quando o texto é pequeno demais, dando mais '
                    'pixels de trabalho para as etapas seguintes de restauração.'
                    + (
                        f' Fator aplicado nesta imagem: {upscale_factor:.2f}x.'
                        if upscale_factor > 1.01
                        else ' Nenhuma ampliação foi necessária nesta imagem.'
                    )
                ),
                'image': ImageUtils.encode_to_data_url(upscaled),
            },
            {
                'step': 3,
                'title': 'Passo 3: Redução de Ruído Adaptativa (Non-Local Means)',
                'technique': (
                    f'cv2.fastNlMeansDenoisingColored(h={denoise_h:.1f}, hColor={denoise_h:.1f}, '
                    'templateWindowSize=7, searchWindowSize=21)'
                ),
                'formula': 'Ip = soma[ w(p,q) . Iq ], onde w pondera pixels q de toda a imagem por similaridade de blocos com p',
                'description': (
                    'Diferente de um desfoque simples (que apenas suaviza a vizinhança imediata), o filtro '
                    'Non-Local Means busca, em toda a imagem, blocos de pixels semelhantes ao redor de cada '
                    'ponto e faz uma média ponderada por similaridade. Isso remove granulação de scanner ou '
                    'câmera e artefatos de compressão JPEG preservando as bordas dos traços — essencial para '
                    'não perder legibilidade do texto. A intensidade (h) é calibrada pelo ruído medido no '
                    'Passo 1, não é um valor fixo arbitrário.'
                ),
                'image': ImageUtils.encode_to_data_url(denoised),
            },
            {
                'step': 4,
                'title': 'Passo 4: Balanço de Branco Automático (Mundo Cinza)',
                'technique': 'Gray-World White Balance por canal B/G/R',
                'formula': 'ganho_c = clamp(mediaGlobal / media_c, 0.7, 1.4), c em {B, G, R}',
                'description': (
                    'Corrige matizes de cor causados por iluminação artificial ou pelo balanço automático de '
                    'câmeras de celular (fotos de texto frequentemente saem amareladas ou azuladas), '
                    'assumindo que a média espacial de cada canal de cor deveria convergir para um cinza '
                    'neutro. Isso reduz o véu de cor que compete visualmente com a tinta do texto contra o '
                    'papel.'
                ),
                'image': ImageUtils.encode_to_data_url(balanced),
            },
            {
                'step': 5,
                'title': 'Passo 5: Realce de Contraste Local Adaptativo (CLAHE)',
                'technique': f'cv2.createCLAHE(clipLimit={clahe_clip:.1f}, tileGridSize=(8,8)) no canal L do espaço LAB',
                'formula': 'Equalização de histograma por blocos locais, com corte de amplificação de ruído (clip limit)',
                'description': (
                    'Ao contrário da equalização de histograma global (que pode saturar áreas já claras ou '
                    'escuras), o CLAHE divide a imagem em blocos de 8x8 e equaliza o histograma de luminância '
                    'localmente em cada bloco, recuperando o contraste do traço da tinta contra o papel mesmo '
                    'sob iluminação desigual (sombra de celular, foto tirada em ângulo). O limite de corte é '
                    'calibrado pelo contraste global medido no Passo 1: quanto mais "lavada" a imagem, maior '
                    'o clipLimit aplicado.'
                ),
                'image': ImageUtils.encode_to_data_url(contrasted),
            },
            {
                'step': 6,
                'title': 'Passo 6: Nitidez Adaptativa (Unsharp Masking)',
                'technique': f'sharpened = original + {sharpen_amount:.2f} x (original - GaussianBlur(sigma=1.4))',
                'formula': 'I_nitida = I + amount . (I - Gauss_sigma(I))',
                'description': (
                    'Subtrai uma versão borrada (filtro Gaussiano) da imagem para isolar os componentes de '
                    'alta frequência — as bordas dos traços — e os soma de volta amplificados, recuperando a '
                    'definição de caracteres afetados por desfoque leve de foco ou movimento. A intensidade é '
                    'calibrada pela nitidez medida no Passo 1: quanto mais borrada a imagem original, maior o '
                    'reforço aplicado, evitando tanto o sub- quanto o sobre-processamento (halos artificiais '
                    'nas bordas).'
                ),
                'image': ImageUtils.encode_to_data_url(sharpened),
            },
        ]
