"""
SAMAAN Matching Engine (MVP)
----------------------------
Attribute-first material matching:
  1. Extract structured signals from a raw description (regex layer):
       - spec/standard codes   (ASTM/IS-style codes, e.g. A336(63-10))
       - part numbers          (P/N 301.00, PN 220, P13D56)
       - dimensions            (18MM, 24 IN, 50NB ...)
       - positional modifiers  (UPPER/LOWER/INLET/OUTLET/DE/NDE ...)
  2. Extract the core part-type nouns using spaCy POS tagging (NLP layer),
     filtered against a brand/company stoplist.
  3. Score two descriptions by combining:
       - noun-set overlap (Jaccard)
       - semantic similarity of the noun phrase only (word vectors,
         NOT the full sentence -- this is what avoids the false
         positives a naive whole-sentence embedding produces)
       - spec-code overlap
       - dimension overlap
     then applies a positional-modifier penalty (UPPER vs LOWER etc.)
  4. Buckets the score into auto-map / human-review / new-candidate.
"""

import re
import spacy

try:
    nlp = spacy.load("en_core_web_md")
except Exception:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")

COMPANY_STOPWORDS = {
    "bpcl", "iocl", "ongc", "bhel", "hpcl", "gail", "ir", "siemens",
    "delta", "corp", "b", "a", "nxg", "pro",
}

POSITIONAL_MODIFIERS = {
    "upper", "lower", "left", "right", "inlet", "outlet", "de", "nde",
    "top", "bottom", "front", "rear", "inner", "outer",
}

SPEC_PATTERN = re.compile(
    r"\b[A-Z]-?\d{2,4}\s?\(?\d{1,3}-\d{1,3}\)?"   # A336(63-10), A-536(65-10)
    r"|\bASTM\s?[A-Z]?\d{2,4}\b"
    r"|\bIS\s?\d{3,5}\b"
    r"|\bPN\s?\d{2,4}[A-Z]?\b"                     # PN 220, PN 465A/465B (variant suffix)
    r"|\bP\/?N[\s\-]?\d{1,4}(?:\.\d{1,2})?",       # P/N 301.00, P/N-2
    re.IGNORECASE,
)

DIMENSION_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:MM|NB|IN|INCH|KG|BAR)\b", re.IGNORECASE
)


def _clean(text: str) -> str:
    text = str(text).upper()
    text = re.sub(r"[^A-Z0-9\s\.\-\/\(\)#:]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_attributes(description: str) -> dict:
    text = _clean(description)

    specs = set(m.group().upper().replace(" ", "") for m in SPEC_PATTERN.finditer(text))
    dims = set(m.group().upper().replace(" ", "") for m in DIMENSION_PATTERN.finditer(text))

    # noun extraction via POS tagging
    doc = nlp(text.lower())
    nouns = set()
    positional = set()
    for tok in doc:
        lemma = tok.lemma_.lower()
        surface = tok.text.lower()
        if surface in POSITIONAL_MODIFIERS or lemma in POSITIONAL_MODIFIERS:
            positional.add(surface)
            continue
        if lemma in COMPANY_STOPWORDS:
            continue
        if tok.pos_ in ("NOUN", "PROPN") and tok.is_alpha and len(lemma) > 2:
            nouns.add(lemma)

    noun_phrase = " ".join(sorted(nouns)) if nouns else text.lower()

    return {
        "raw": description,
        "part_type_nouns": nouns,
        "spec_codes": specs,
        "dimensions": dims,
        "positional_modifiers": positional,
        "noun_phrase": noun_phrase,
    }


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _semantic_sim(phrase_a: str, phrase_b: str) -> float:
    da, db = nlp(phrase_a), nlp(phrase_b)
    if da.vector_norm == 0 or db.vector_norm == 0:
        return 0.0
    return float(da.similarity(db))


def score_pair(desc_a: str, desc_b: str) -> dict:
    attr_a = extract_attributes(desc_a)
    attr_b = extract_attributes(desc_b)

    noun_overlap = _jaccard(attr_a["part_type_nouns"], attr_b["part_type_nouns"])
    semantic_sim = _semantic_sim(attr_a["noun_phrase"], attr_b["noun_phrase"])
    spec_overlap = _jaccard(attr_a["spec_codes"], attr_b["spec_codes"])
    dim_overlap = _jaccard(attr_a["dimensions"], attr_b["dimensions"])

    combined = (
        0.40 * noun_overlap
        + 0.25 * semantic_sim
        + 0.20 * spec_overlap
        + 0.15 * dim_overlap
    )

    # Positional-modifier safeguard: if both sides specify a positional
    # modifier and they differ (UPPER vs LOWER, INLET vs OUTLET, DE vs NDE),
    # they are almost certainly different physical parts -- penalize hard.
    pos_a, pos_b = attr_a["positional_modifiers"], attr_b["positional_modifiers"]
    penalty_applied = False
    if pos_a and pos_b and pos_a.isdisjoint(pos_b):
        combined *= 0.3
        penalty_applied = True

    if combined >= 0.75:
        decision = "auto-map"
    elif combined >= 0.35:
        decision = "human-review"
    else:
        decision = "new-candidate"

    return {
        "score": round(combined, 3),
        "noun_overlap": round(noun_overlap, 3),
        "semantic_sim": round(semantic_sim, 3),
        "spec_overlap": round(spec_overlap, 3),
        "dim_overlap": round(dim_overlap, 3),
        "positional_penalty_applied": penalty_applied,
        "decision": decision,
        "attributes_a": {k: (list(v) if isinstance(v, set) else v) for k, v in attr_a.items()},
        "attributes_b": {k: (list(v) if isinstance(v, set) else v) for k, v in attr_b.items()},
    }
