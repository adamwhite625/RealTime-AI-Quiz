import difflib
import logging
import re
import unicodedata
from typing import List, Optional, Tuple, Dict, Any

from app.schemas.answer_dto import OptionInfo, MatchAnswerResponse

logger = logging.getLogger(__name__)


def remove_accents(input_str: str) -> str:
    """Removes Vietnamese tone marks and accents for loose phonetic comparison."""
    if not input_str:
        return ""
    nfkd = unicodedata.normalize("NFKD", input_str)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return no_accent.replace("đ", "d").replace("Đ", "D")


def clean_text(text: str) -> str:
    """Normalizes text by lowercasing and trimming punctuation."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


class AnswerMatcherService:
    """
    Intelligent Vietnamese Quiz Answer Matcher.
    Parses speech transcripts to identify the player's intended answer option:
    1. By Label: A, B, C, D (or phonetic: bê, xê, đê, cờ...)
    2. By Index: một (1), hai (2), ba (3), bốn/tư (4)
    3. By Content: Substring match or fuzzy similarity with option text
    """

    # Label synonyms in Vietnamese speech
    LABEL_PATTERNS = {
        "A": [r"\ba\b", r"\bá\b", r"\bây\b"],
        "B": [r"\bb\b", r"\bbê\b", r"\bb bò\b", r"\bbi\b"],
        "C": [r"\bc\b", r"\bxê\b", r"\bcờ\b", r"\bsi\b"],
        "D": [r"\bd\b", r"\bđ\b", r"\bđê\b", r"\bđi\b", r"\bdê\b"],
    }

    INDEX_PATTERNS = {
        0: [r"\bmột\b", r"\b1\b", r"\bnhất\b", r"\bđầu tiên\b"],
        1: [r"\bhai\b", r"\b2\b", r"\bnhì\b"],
        2: [r"\bba\b", r"\b3\b"],
        3: [r"\bbốn\b", r"\btư\b", r"\b4\b"],
    }

    def match(self, transcribed_text: str, options: List[OptionInfo]) -> MatchAnswerResponse:
        """
        Matches transcribed Vietnamese speech against a question's options list.
        """
        raw_text = transcribed_text.strip()
        normalized = clean_text(raw_text)
        no_accent_norm = clean_text(remove_accents(raw_text))

        if not normalized or not options:
            return MatchAnswerResponse(
                transcribed_text=raw_text,
                matched_option_id=None,
                matched_label=None,
                matched_text=None,
                confidence=0.0,
                match_type="none",
                is_matched=False,
            )

        # 1. Match by Option Label (A, B, C, D)
        # Look for explicit triggers like "chọn a", "đáp án b", "câu c", "ý d" or standalone letter
        for idx, opt in enumerate(options):
            label = (opt.label or chr(65 + idx)).upper()
            patterns = self.LABEL_PATTERNS.get(label, [rf"\b{label.lower()}\b"])
            
            for pat in patterns:
                # Strong match: "đáp án B", "chọn B", "câu B", "ý B"
                strong_pat = rf"(?:đáp án|chọn|câu|ý|phương án)\s+{pat}"
                if re.search(strong_pat, normalized, re.IGNORECASE):
                    logger.info("Matched by strong label '%s' in '%s'", label, raw_text)
                    return MatchAnswerResponse(
                        transcribed_text=raw_text,
                        matched_option_id=opt.id,
                        matched_label=label,
                        matched_text=opt.text,
                        confidence=0.98,
                        match_type="label",
                        is_matched=True,
                    )
                # Standalone or relaxed letter match
                if re.search(pat, normalized, re.IGNORECASE):
                    logger.info("Matched by label '%s' in '%s'", label, raw_text)
                    return MatchAnswerResponse(
                        transcribed_text=raw_text,
                        matched_option_id=opt.id,
                        matched_label=label,
                        matched_text=opt.text,
                        confidence=0.92,
                        match_type="label",
                        is_matched=True,
                    )

        # 2. Match by Numeric Ordinal (1 -> A, 2 -> B, 3 -> C, 4 -> D)
        for idx, patterns in self.INDEX_PATTERNS.items():
            if idx < len(options):
                opt = options[idx]
                label = (opt.label or chr(65 + idx)).upper()
                for pat in patterns:
                    strong_pat = rf"(?:đáp án|chọn|số|câu|thứ)\s+{pat}"
                    if re.search(strong_pat, normalized, re.IGNORECASE):
                        logger.info("Matched by strong index %d (%s) in '%s'", idx, label, raw_text)
                        return MatchAnswerResponse(
                            transcribed_text=raw_text,
                            matched_option_id=opt.id,
                            matched_label=label,
                            matched_text=opt.text,
                            confidence=0.95,
                            match_type="index",
                            is_matched=True,
                        )

        # 3. Match by Content (Option text substring & fuzzy matching)
        best_match: Optional[OptionInfo] = None
        best_score = 0.0
        best_label = None

        for idx, opt in enumerate(options):
            label = (opt.label or chr(65 + idx)).upper()
            opt_clean = clean_text(opt.text)
            opt_no_accent = clean_text(remove_accents(opt.text))

            # Exact phrase containment (e.g. "Hà Nội" inside "Tôi chọn thủ đô Hà Nội")
            if opt_clean and opt_clean in normalized:
                score = 0.95
                if score > best_score:
                    best_score = score
                    best_match = opt
                    best_label = label
                continue

            # Accent-free containment
            if opt_no_accent and opt_no_accent in no_accent_norm:
                score = 0.90
                if score > best_score:
                    best_score = score
                    best_match = opt
                    best_label = label
                continue

            # Fuzzy sequence similarity
            similarity = difflib.SequenceMatcher(None, opt_clean, normalized).ratio()
            similarity_no_acc = difflib.SequenceMatcher(None, opt_no_accent, no_accent_norm).ratio()
            max_sim = max(similarity, similarity_no_acc)

            # Check individual tokens overlap
            opt_words = set(opt_clean.split())
            spoken_words = set(normalized.split())
            if opt_words and opt_words.issubset(spoken_words):
                max_sim = max(max_sim, 0.88)

            if max_sim > best_score and max_sim >= 0.65:
                best_score = max_sim
                best_match = opt
                best_label = label

        if best_match and best_score >= 0.65:
            logger.info("Matched by content '%s' (score=%.2f) in '%s'", best_match.text, best_score, raw_text)
            return MatchAnswerResponse(
                transcribed_text=raw_text,
                matched_option_id=best_match.id,
                matched_label=best_label,
                matched_text=best_match.text,
                confidence=round(best_score, 2),
                match_type="content",
                is_matched=True,
            )

        # Fallback: No decisive match
        return MatchAnswerResponse(
            transcribed_text=raw_text,
            matched_option_id=None,
            matched_label=None,
            matched_text=None,
            confidence=0.0,
            match_type="none",
            is_matched=False,
        )


answer_matcher = AnswerMatcherService()
