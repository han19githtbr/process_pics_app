import cv2
import numpy as np

from src.core.models.letter_box import LetterBox
from src.core.models.processing_options import ProcessingOptions
from src.core.processors.opencv_processor import OpenCVProcessor
from src.core.segmenters.improved_segmenter import ImprovedSegmenter


def _build_text_image(text: str, height: int = 500, width: int = 1200, bg_color: int = 255,
                     font_scale: float = 2.5, thickness: int = 6, color: tuple = (0, 0, 0)) -> np.ndarray:
    image = np.full((height, width, 3), bg_color, dtype=np.uint8)
    cv2.putText(
        image,
        text,
        (80, int(height * 0.5)),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA,
    )
    return image


def test_segmenter_detects_letters_from_text():
    image = _build_text_image("Sample text here")
    result = ImprovedSegmenter(ProcessingOptions(min_letter_size=5, max_image_size=1800)).segment(image)

    assert len(result.letters) >= 10
    assert all(letter.width > 0 and letter.height > 0 for letter in result.letters)


def test_segmenter_groups_letters_by_word_order():
    segmenter = ImprovedSegmenter(ProcessingOptions())
    letters = [
        LetterBox(x=20, y=10, width=10, height=10, area=100, confidence=0.9, line=1),
        LetterBox(x=40, y=10, width=10, height=10, area=100, confidence=0.9, line=1),
        LetterBox(x=160, y=10, width=10, height=10, area=100, confidence=0.9, line=1),
        LetterBox(x=220, y=10, width=10, height=10, area=100, confidence=0.9, line=1),
    ]

    words = segmenter._group_letters_by_words(letters)

    assert len(words) == 2
    assert [box.x for box in words[0]] == [20, 40]
    assert [box.x for box in words[1]] == [160, 220]


def test_filter_components_rejects_irregular_noise():
    segmenter = ImprovedSegmenter(ProcessingOptions())
    image = np.full((200, 200), 255, dtype=np.uint8)
    components = [
        {'area': 8, 'x': 2, 'y': 2, 'width': 4, 'height': 4, 'centroid': (4, 4)},
        {'area': 250, 'x': 25, 'y': 20, 'width': 25, 'height': 30, 'centroid': (37, 35)},
    ]

    filtered = segmenter._filter_components(components, image)

    assert len(filtered) == 1
    assert filtered[0]['area'] == 250


def test_segmenter_handles_low_contrast_text():
    image = _build_text_image("Hello", bg_color=220, color=(120, 120, 120), font_scale=2.2, thickness=5)
    result = ImprovedSegmenter(ProcessingOptions(min_letter_size=4, max_image_size=1800)).segment(image)

    assert len(result.letters) >= 3


def test_segmenter_handles_light_text_on_dark_background():
    image = _build_text_image(
        "Texto claro no fundo preto",
        bg_color=0,
        color=(255, 255, 255),
        font_scale=2.2,
        thickness=5,
    )

    result = ImprovedSegmenter(ProcessingOptions(min_letter_size=4, max_image_size=1800)).segment(image)

    assert len(result.letters) >= 10
    assert all(letter.width > 0 and letter.height > 0 for letter in result.letters)


def test_segmenter_handles_large_text_block():
    image = np.full((900, 1200, 3), 255, dtype=np.uint8)
    text = "SAMPLE HERE SAMPLE HERE SAMPLE HERE SAMPLE HERE"
    cv2.putText(image, text, (60, 440), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 0), 5, cv2.LINE_AA)

    result = ImprovedSegmenter(ProcessingOptions(min_letter_size=3, max_image_size=2000)).segment(image)

    assert len(result.letters) >= 20
    assert result.transcript


def test_processor_respects_configuration_options():
    image = np.full((200, 200, 3), 255, dtype=np.uint8)
    options = ProcessingOptions(sensitivity=0.7, padding=6, min_letter_size=3, remove_noise=True, enhance_contrast=True)

    binary = OpenCVProcessor().preprocess(image, options)

    assert binary.dtype == np.uint8
    assert binary.shape == image.shape[:2]


def test_segmenter_builds_transcript_in_reading_order():
    segmenter = ImprovedSegmenter(ProcessingOptions())
    letters = [
        LetterBox(x=30, y=10, width=10, height=10, area=100, confidence=0.9, line=1, id=2),
        LetterBox(x=10, y=10, width=10, height=10, area=100, confidence=0.9, line=1, id=1),
        LetterBox(x=80, y=10, width=10, height=10, area=100, confidence=0.9, line=1, id=3),
    ]

    transcript = segmenter._build_transcript(letters)

    assert transcript == "1 2 3"


def test_segmenter_detects_plagiarism_between_similar_text_images():
    segmenter = ImprovedSegmenter(ProcessingOptions(min_letter_size=4, max_image_size=1800))
    image_a = _build_text_image("Texto idêntico para comparar")
    image_b = _build_text_image("Texto idêntico para comparar")

    comparison = segmenter.compare_images(image_a, image_b)

    assert comparison['similarity'] >= 0.9
    assert comparison['status'] == 'plagio_detectado'


def test_segmenter_generates_pdf_pipeline_steps():
    segmenter = ImprovedSegmenter(ProcessingOptions(min_letter_size=4))
    image = _build_text_image("PDF Pipeline Steps")

    result = segmenter.segment(image)

    assert len(result.steps) == 7
    step_titles = [s['title'] for s in result.steps]
    assert any("Passo 1" in t for t in step_titles)
    assert any("Passo 2" in t for t in step_titles)
    assert any("Passo 3" in t for t in step_titles)
    assert any("Passo 4" in t for t in step_titles)
    assert any("Passo 5" in t for t in step_titles)
    assert any("Passo 6" in t for t in step_titles)
    assert any("Passo 7" in t for t in step_titles)

    for step in result.steps:
        assert step['image'].startswith('data:image/png;base64,')
        assert step['technique']
        assert step['description']


def test_segmenter_splits_wide_grouped_component():
    segmenter = ImprovedSegmenter(ProcessingOptions(split_grouped_letters=True, min_letter_size=4))
    # Cria uma máscara binária com duas barras verticais conectadas por uma ponte fina
    binary = np.zeros((40, 60), dtype=np.uint8)
    binary[5:35, 10:22] = 255  # primeira letra
    binary[5:35, 38:50] = 255  # segunda letra
    binary[20:22, 22:38] = 255  # ponte fina conectando as duas

    comp = {'x': 10, 'y': 5, 'width': 40, 'height': 30, 'area': int(np.count_nonzero(binary)), 'label': 1}
    splits = segmenter._split_wide_component(comp, binary)

    assert len(splits) >= 2


def test_segmenter_rejects_horizontal_line_as_non_letter():
    segmenter = ImprovedSegmenter(ProcessingOptions(filter_non_letters=True, min_letter_size=4))
    image = np.zeros((100, 100), dtype=np.uint8)
    components = [
        # Linha horizontal muito fina e longa (sublinhado)
        {'x': 5, 'y': 50, 'width': 80, 'height': 3, 'area': 240},
        # Letra proporcional normal
        {'x': 20, 'y': 20, 'width': 18, 'height': 24, 'area': 220},
    ]

    filtered = segmenter._filter_components(components, image)
    assert len(filtered) == 1
    assert filtered[0]['width'] == 18

