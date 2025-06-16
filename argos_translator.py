"""Argos Translate 기반 Markdown 문서 번역기"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re

try:
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


@dataclass
class TranslationUnit:
    content: str
    unit_type: str  # paragraph, sentence, header, code, empty
    is_translatable: bool
    metadata: Dict


class MarkdownTranslator:
    def __init__(self, source_lang: str = "auto", target_lang: str = "ko"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.detected_language: Optional[str] = None

    def detect_language(self, text: str) -> str:
        if not LANGDETECT_AVAILABLE:
            return "en"
        sample = text[:1000]
        try:
            return detect(sample)
        except Exception:
            return "en"

    def split_into_units(self, markdown_text: str, split_by_sentence: bool = False) -> List[TranslationUnit]:
        units: List[TranslationUnit] = []
        lines = markdown_text.split("\n")
        paragraph: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith("```"):
                if paragraph:
                    units.extend(self._process_paragraph(paragraph, split_by_sentence))
                    paragraph = []
                code_block = [line]
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_block.append(lines[i])
                    i += 1
                if i < len(lines):
                    code_block.append(lines[i])
                units.append(TranslationUnit("\n".join(code_block), "code", False, {"line_count": len(code_block)}))
            elif stripped.startswith("#"):
                if paragraph:
                    units.extend(self._process_paragraph(paragraph, split_by_sentence))
                    paragraph = []
                level = len(stripped) - len(stripped.lstrip('#'))
                header_text = stripped[level:].strip()
                units.append(TranslationUnit(line, "header", bool(header_text), {"level": level, "text": header_text}))
            elif not stripped:
                if paragraph:
                    units.extend(self._process_paragraph(paragraph, split_by_sentence))
                    paragraph = []
                units.append(TranslationUnit("", "empty", False, {}))
            else:
                paragraph.append(line)
            i += 1
        if paragraph:
            units.extend(self._process_paragraph(paragraph, split_by_sentence))
        return units

    def _process_paragraph(self, lines: List[str], split_by_sentence: bool) -> List[TranslationUnit]:
        text = "\n".join(lines)
        if not text.strip():
            return []
        if split_by_sentence:
            sentences = self._split_sentences(text)
            return [TranslationUnit(s, "sentence", True, {}) for s in sentences if s.strip()]
        else:
            return [TranslationUnit(text, "paragraph", True, {"line_count": len(lines)})]

    def _split_sentences(self, text: str) -> List[str]:
        pattern = r"(?<=[.!?])\s+(?=[A-Z])"
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def translate_unit(self, unit: TranslationUnit) -> str:
        if not unit.is_translatable:
            return unit.content
        if not ARGOS_AVAILABLE:
            return f"[Argos Translate 번역 실패: 번역 엔진이 설치되어 있지 않습니다]"
        src = self.detected_language if self.source_lang == "auto" and self.detected_language else self.source_lang
        try:
            result = argostranslate.translate.translate(unit.content, src, self.target_lang)
            # 번역이 원본과 같으면 번역 실패로 간주
            if result.strip() == unit.content.strip():
                preview = unit.content[:30].replace('\n', ' ')
                return f"[Argos Translate 번역 실패: '{preview}...']"
            return result
        except Exception as e:
            preview = unit.content[:30].replace('\n', ' ')
            return f"[Argos Translate 번역 실패: '{preview}...']"

    def translate_document(self, markdown_text: str, split_by_sentence: bool = False) -> List[str]:
        if self.source_lang == "auto":
            self.detected_language = self.detect_language(markdown_text)
        units = self.split_into_units(markdown_text, split_by_sentence)
        translated: List[str] = []
        for unit in units:
            translated.append(self.translate_unit(unit))
        return translated


def translate_markdown(markdown_text: str, path: Optional[str] = None, source_lang: str = "auto", target_lang: str = "ko", split_by_sentence: bool = False) -> str:
    translator = MarkdownTranslator(source_lang, target_lang)
    translations = translator.translate_document(markdown_text, split_by_sentence)

    if path:
        from progress_manager import progress_manager
        chunks_info = [
            {"index": i, "header": "paragraph", "size": len(unit), "status": "completed"}
            for i, unit in enumerate(translations)
        ]
        progress_manager.set_total_chunks(path, len(translations), chunks_info)
        for i, text in enumerate(translations):
            progress_manager.add_chunk_result(path, i, text)
        progress_manager.finish(path)

    return "\n".join(translations)
