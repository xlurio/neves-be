import functools

from transformers import AutoModelForSeq2SeqLM
from transformers import AutoTokenizer
from transformers import PreTrainedTokenizerBase
from transformers.integrations.executorch import Seq2SeqLMExportableModule

from neves_be.language_model.models import Translation


@functools.cache
def make_translation_tokenizer() -> PreTrainedTokenizerBase:
    return AutoTokenizer.from_pretrained("google-t5/t5-small")


@functools.cache
def make_translation_model() -> Seq2SeqLMExportableModule:
    return AutoModelForSeq2SeqLM.from_pretrained(
        "google-t5/t5-small",
        device_map="auto",
    )


def generate_translation(txt: str) -> str:
    if translation_model := Translation.objects.get(id=hash(txt)):
        return translation_model.output

    tokenizer = make_translation_tokenizer()
    model = make_translation_model()

    input_ids = tokenizer(
        f"translate Chinese to English: {txt}",
        return_tensors="pt",
    ).to(model.device)

    output = model.generate(**input_ids, cache_implementation="static")

    translation_model = Translation.objects.create(
        id=hash(txt),
        output=tokenizer.decode(output[0], skip_special_tokens=True),
    )

    return translation_model.output
