from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import assert_never
from typing import cast

from neves_be.genai.services.text2speech import generate_speech
from neves_be.practice_assessments.constants import MASK_TOKEN
from neves_be.practice_assessments.services.questions import AlternativesSetup
from neves_be.practice_assessments.services.questions import BasePracticeQuestionFactory
from neves_be.practice_assessments.services.questions import PracticeQuestionSetup
from neves_be.practice_questions.models import NgramSessionAssessmentQuestion
from neves_be.practice_questions.models import NgramSessionAssessmentQuestionAlt
from neves_be.practice_questions.models import NgramSessionQuestionType
from neves_be.practice_questions.models import PracticeAssessmentAlternativeTypeChoices
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.word_lm.models import Ngram
from neves_be.word_lm.models import Word

if TYPE_CHECKING:
    from collections.abc import Sequence

    from neves_be.practice_assessments.models import NgramSessionAssessment
    from neves_be.practice_assessments.models import PracticeSessionAssessment


class Ngram2WordQuestionSetup(TypedDict):
    audio: str
    selected_word: Word
    question_txt: str


class Ngram2WordQuestionFactory(BasePracticeQuestionFactory):
    def __init__(
        self,
        ngram: Ngram,
        question_type: NgramSessionQuestionType,
    ) -> None:
        self.__ngram = ngram
        self.__question_type = question_type

    def _setup_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        question_setup = self.__setup_ngr_2_wrd_question(
            self.__ngram,
            self.__question_type,
        )
        question_word = question_setup["selected_word"]
        selected_words = self.__select_words(question_word)
        alts_stp = self.__setup_word_alternatives(
            question_word,
            selected_words,
            self.__question_type,
        )

        question = NgramSessionAssessmentQuestion.objects.create(
            assessment=cast("NgramSessionAssessment", assessment),
            expected_answer=alts_stp["correct_answer"],
            number=question_num,
            question=question_setup["question_txt"],
            audio=question_setup["audio"],
        )

        return PracticeQuestionSetup(
            question=question,
            alternatives=alts_stp["alternatives"],
        )

    def __setup_ngr_2_wrd_question(
        self,
        ngram: Ngram,
        question_type: NgramSessionQuestionType,
    ) -> Ngram2WordQuestionSetup:
        selected_word = random.choice(
            Word.objects.filter(word_ngrams__ngram=ngram),
        )
        processed_ngram = ngram.value.replace(selected_word.value, MASK_TOKEN)
        audio = ""

        if question_type in {
            "NGRAM-AUDIO-TO-WORD-AUDIO",
            "NGRAM-AUDIO-TO-WORD-TEXT",
        }:
            question_txt = "What word is missing in the following audio?"
            audio = generate_speech(question_txt)
        elif question_type in {
            "NGRAM-TEXT-TO-WORD-AUDIO",
            "NGRAM-TEXT-TO-WORD-TEXT",
        }:
            question_txt = (
                f"What word is missing in the following ngram?\n{processed_ngram}"
            )
        else:
            msg = f"Unknown question type: {question_type}"
            raise ValueError(msg)

        return Ngram2WordQuestionSetup(
            audio=audio,
            selected_word=selected_word,
            question_txt=question_txt,
        )

    def __select_words(self, word: Word) -> Sequence[Word]:
        words = set(Word.objects.exclude(pk=word.pk))
        options = [*random.sample(cast("Sequence[Word]", words), k=4), word]
        options.sort(key=lambda _: random.random())

        return cast("Sequence[Word]", options)

    def __setup_word_alternatives(
        self,
        question_word: Word,
        selected_words: Sequence[Word],
        question_type: NgramSessionQuestionType,
    ) -> AlternativesSetup:
        correct_answer = PracticeSessionAssessmentQuestionAnswer.A
        alt_letters = list(PracticeSessionAssessmentQuestionAnswer)
        alternatives: list[NgramSessionAssessmentQuestionAlt] = []
        alternative_type = self.__get_alt_type_by_question_type(question_type)

        for ltt_idx, curr_word in enumerate(selected_words):
            if curr_word == question_word:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                NgramSessionAssessmentQuestionAlt(
                    letter=alt_letters[ltt_idx],
                    type=alternative_type,
                    payload=self.__get_word_alt_payload_for_type(
                        curr_word,
                        alternative_type,
                    ),
                ),
            )

        return AlternativesSetup(
            correct_answer=correct_answer,
            alternatives=alternatives,
        )

    def __get_alt_type_by_question_type(
        self,
        question_type: NgramSessionQuestionType,
    ) -> PracticeAssessmentAlternativeTypeChoices:
        if question_type in {
            "NGRAM-AUDIO-TO-WORD-AUDIO",
            "NGRAM-TEXT-TO-WORD-AUDIO",
        }:
            return PracticeAssessmentAlternativeTypeChoices.AUDIO

        if question_type in {
            "NGRAM-AUDIO-TO-WORD-TEXT",
            "NGRAM-TEXT-TO-WORD-TEXT",
        }:
            return PracticeAssessmentAlternativeTypeChoices.TEXT

        msg = f"Unknown question type {question_type}"
        raise ValueError(msg)

    def __get_word_alt_payload_for_type(
        self,
        word: Word,
        alternative_type: PracticeAssessmentAlternativeTypeChoices,
    ) -> str:
        if alternative_type == PracticeAssessmentAlternativeTypeChoices.AUDIO:
            return word.pronounce

        if alternative_type == PracticeAssessmentAlternativeTypeChoices.TEXT:
            return word.value

        assert_never(alternative_type)
        return None
