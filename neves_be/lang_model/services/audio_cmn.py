import pathlib
import re
from typing import Literal
from typing import TypedDict

from django.conf import settings

from neves_be.lang_model.services.pinyin_to_tone import Tone
from neves_be.lang_model.services.pinyin_to_tone import ToneAccessor


class NormCharAndTone(TypedDict):
    normalized_char: str
    tone: Tone | Literal[""]


ACCENTED_PINYIN_REPLACEMENTS: dict[str, NormCharAndTone] = {
    "ā": {"normalized_char": "a", "tone": 1},
    "á": {"normalized_char": "a", "tone": 2},
    "ǎ": {"normalized_char": "a", "tone": 3},
    "à": {"normalized_char": "a", "tone": 4},
    "ē": {"normalized_char": "e", "tone": 1},
    "é": {"normalized_char": "e", "tone": 2},
    "ě": {"normalized_char": "e", "tone": 3},
    "è": {"normalized_char": "e", "tone": 4},
    "ī": {"normalized_char": "i", "tone": 1},
    "í": {"normalized_char": "i", "tone": 2},
    "ǐ": {"normalized_char": "i", "tone": 3},
    "ì": {"normalized_char": "i", "tone": 4},
    "ō": {"normalized_char": "o", "tone": 1},
    "ó": {"normalized_char": "o", "tone": 2},
    "ǒ": {"normalized_char": "o", "tone": 3},
    "ò": {"normalized_char": "o", "tone": 4},
    "ū": {"normalized_char": "u", "tone": 1},
    "ú": {"normalized_char": "u", "tone": 2},
    "ǔ": {"normalized_char": "u", "tone": 3},
    "ù": {"normalized_char": "u", "tone": 4},
    "ǖ": {"normalized_char": "v", "tone": 1},
    "ǘ": {"normalized_char": "v", "tone": 2},
    "ǚ": {"normalized_char": "v", "tone": 3},
    "ǜ": {"normalized_char": "v", "tone": 4},
    "ü": {"normalized_char": "v", "tone": ""},
}

PINYIN_TOKEN_RE = re.compile(r"[a-zA-ZüÜǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùv:]+")


BASE_AUDIO_DIR = pathlib.Path(settings.BASE_DIR) / "audio-cmn" / "18k-abr"


def normalize_pinyin_for_filename(pinyin: str) -> str:
    token_match = PINYIN_TOKEN_RE.search((pinyin or "").strip())
    if token_match is None:
        return ""

    token = token_match.group(0).lower().replace("u:", "v")
    normalized = "".join(
        ACCENTED_PINYIN_REPLACEMENTS.get(char, {"normalized_char": char, "tone": ""})[
            "normalized_char"
        ]
        for char in token
    )
    return re.sub(r"[^a-zv]", "", normalized) + str(
        ToneAccessor().get_tone_for_pinyin(
            pinyin,
            [
                (char, char_tone["tone"])
                for char, char_tone in ACCENTED_PINYIN_REPLACEMENTS.items()
            ],
            start_pinyin_idx=0,
            end_pinyin_idx=len(pinyin) - 1,
            start_map_idx=0,
            end_map_idx=len(ACCENTED_PINYIN_REPLACEMENTS) - 1,
        ),
    )


def get_audio_path_from_pinyin(pinyin: str) -> str:
    audio_dir = BASE_AUDIO_DIR / "syllabs"
    if not audio_dir.exists():
        msg = f"Audio directory not found: {audio_dir}"
        raise ValueError(msg)

    normalized = normalize_pinyin_for_filename(pinyin)

    pronounce = ""

    if normalized and audio_dir.exists():
        matches = sorted(audio_dir.glob(f"cmn-{normalized}.mp3"))

        if matches:
            pronounce = f"/audio-cmn/18k-abr/syllabs/{matches[0].name}"

    if not pronounce:
        msg = f"Pronounce not found for {pinyin}"
        raise ValueError(msg)

    return pronounce


def get_audio_path_from_chinese(chinese_txt: str) -> str:
    audio_dir = BASE_AUDIO_DIR / "hsk"

    if not audio_dir.exists():
        msg = f"Audio directory not found: {audio_dir}"
        raise ValueError(msg)

    pronounce = ""

    if chinese_txt and audio_dir.exists():
        matches = sorted(audio_dir.glob(f"cmn-{chinese_txt}[0-9].mp3"))
        if matches:
            pronounce = f"/audio-cmn/18k-abr/hsk/{matches[0].name}"

    if not pronounce:
        msg = f"Pronounce not found for {chinese_txt}"
        raise ValueError(msg)

    return pronounce
