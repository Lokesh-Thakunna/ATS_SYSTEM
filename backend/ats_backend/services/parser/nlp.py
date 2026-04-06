from functools import lru_cache

import spacy
from spacy.matcher import PhraseMatcher


@lru_cache(maxsize=1)
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None


@lru_cache(maxsize=1)
def get_skill_phrase_matcher():
    nlp = get_nlp()
    if nlp is None:
        return None

    from .skills_extractor import SKILLS

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    matcher.add("SKILLS", [nlp.make_doc(skill) for skill in SKILLS])
    return matcher
