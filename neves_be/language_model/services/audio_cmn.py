import pathlib
import re

from django.conf import settings

ACCENTED_PINYIN_REPLACEMENTS = {
    "ā": "a",
    "á": "a",
    "ǎ": "a",
    "à": "a",
    "ē": "e",
    "é": "e",
    "ě": "e",
    "è": "e",
    "ī": "i",
    "í": "i",
    "ǐ": "i",
    "ì": "i",
    "ō": "o",
    "ó": "o",
    "ǒ": "o",
    "ò": "o",
    "ū": "u",
    "ú": "u",
    "ǔ": "u",
    "ù": "u",
    "ǖ": "v",
    "ǘ": "v",
    "ǚ": "v",
    "ǜ": "v",
    "ü": "v",
}
PINYIN_TOKEN_RE = re.compile(r"[a-zA-ZüÜǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùv:]+")


BASE_AUDIO_DIR = pathlib.Path(settings.BASE_DIR) / "audio-cmn" / "18k-abr"


def normalize_pinyin_for_filename(pinyin: str) -> str:
    token_match = PINYIN_TOKEN_RE.search((pinyin or "").strip())
    if token_match is None:
        return ""

    token = token_match.group(0).lower().replace("u:", "v")
    normalized = "".join(ACCENTED_PINYIN_REPLACEMENTS.get(char, char) for char in token)
    return re.sub(r"[^a-zv]", "", normalized)


def get_audio_path_from_pinyin(pinyin: str) -> str:
    audio_dir = BASE_AUDIO_DIR / "syllabs"
    if not audio_dir.exists():
        msg = f"Audio directory not found: {audio_dir}"
        raise ValueError(msg)

    normalized = normalize_pinyin_for_filename(pinyin)

    pronounce = ""

    if normalized and audio_dir.exists():
        matches = sorted(audio_dir.glob(f"cmn-{normalized}[0-9].mp3"))

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
