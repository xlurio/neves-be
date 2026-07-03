import functools
import logging
import re

from django.conf import settings
from django.db import transaction
from optimum.intel import OVModelForSeq2SeqLM
from transformers import AutoTokenizer
from transformers import PreTrainedTokenizerBase

from neves_be.genai.exceptions import TranslationError
from neves_be.genai.models import GeneratedTranslation
from neves_be.genai.services.local_utils import generation_cache_id

CHINESE_CHAR_PATTERN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
EXTRA_TOKEN_PATTERN = re.compile(r"[<]extra_id_[0-9]+[>]")

_logger = logging.getLogger(__name__)


@functools.cache
def make_translation_tokenizer() -> PreTrainedTokenizerBase:
    return AutoTokenizer.from_pretrained(settings.GENAI_TRANSLATION_MODEL_PATH)


@functools.cache
def make_translation_model() -> OVModelForSeq2SeqLM:
    return OVModelForSeq2SeqLM.from_pretrained(settings.GENAI_TRANSLATION_MODEL_PATH)


def _normalize_output(output: str) -> str:
    return EXTRA_TOKEN_PATTERN.sub("", output).strip()


def _is_valid_translation(output: str) -> bool:
    return bool(output) and not CHINESE_CHAR_PATTERN.search(output)


def _target_language_token_id(
    tokenizer: PreTrainedTokenizerBase,
) -> int:
    target_lang = settings.GENAI_TRANSLATION_TARGET_LANG
    token_id = tokenizer.convert_tokens_to_ids(target_lang)
    unknown_token_id = getattr(tokenizer, "unk_token_id", None)
    if token_id is None or token_id == unknown_token_id:
        raise TranslationError.invalid_target_language_token(target_lang)
    return token_id


def _generate_candidate(
    txt: str,
    *,
    source_lang: str,
    target_token_id: int,
) -> str:
    tokenizer = make_translation_tokenizer()
    model = make_translation_model()

    if not hasattr(tokenizer, "src_lang"):
        raise TranslationError.unsupported_source_language_selection()

    tokenizer.src_lang = source_lang
    input_ids = tokenizer(txt, return_tensors="pt").to(model.device)

    output_embed = model.generate(
        **input_ids,
        forced_bos_token_id=target_token_id,
    )
    detoken_output = tokenizer.decode(output_embed[0], skip_special_tokens=True)
    return _normalize_output(detoken_output)


@transaction.atomic
def generate_translation(txt: str) -> str:
    if translation_model := GeneratedTranslation.objects.filter(
        id=generation_cache_id(txt),
    ).first():
        if _is_valid_translation(translation_model.output):
            return translation_model.output
        _logger.warning(
            "Dropping cached translation with invalid output",
            extra={"translation_id": translation_model.id},
        )
        translation_model.delete()

    _logger.info("No translation was found for '%s', generating a new one", txt)

    source_langs = tuple(settings.GENAI_TRANSLATION_SOURCE_LANGS)
    if not source_langs:
        raise TranslationError.missing_source_languages()

    target_token_id = _target_language_token_id(make_translation_tokenizer())

    invalid_outputs: list[str] = []
    for source_lang in source_langs:
        try:
            output = _generate_candidate(
                txt,
                source_lang=source_lang,
                target_token_id=target_token_id,
            )
        except Exception as exc:
            if isinstance(exc, TranslationError):
                raise
            raise TranslationError.failed_attempt_for_source_lang(source_lang) from exc

        if _is_valid_translation(output):
            translation_model, _ = GeneratedTranslation.objects.get_or_create(
                id=generation_cache_id(txt),
                output=output,
            )
            return translation_model.output

        invalid_outputs.append(f"{source_lang}: {output!r}")
        _logger.warning(
            "Translation output failed quality checks",
            extra={"source_lang": source_lang, "output": output},
        )

    raise TranslationError.invalid_english_output(invalid_outputs)
