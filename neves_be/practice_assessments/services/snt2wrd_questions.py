import random
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import assert_never

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.practice_assessments.services.questions import AlternativesSetup
from neves_be.practice_assessments.services.questions import BasePracticeQuestionFactory
from neves_be.practice_assessments.services.questions import PracticeQuestionSetup
from neves_be.practice_questions.models import PracticeAssessmentAlternativeTypeChoices
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestion
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestionAlt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from neves_be.practice_assessments.models import PracticeSessionAssessment
    from neves_be.practice_assessments.types import SentenceAssessmentQuestionType


class Sentence2WordQuestionSetup(TypedDict):
    audio: str
    selected_word: Word
    question_txt: str


class Sentence2WordQuestionFactory(BasePracticeQuestionFactory):
    def __init__(
        self,
        sentence: Sentence,
        question_type: SentenceAssessmentQuestionType,
    ) -> None:
        self.__sentence = sentence
        self.__question_type = question_type

    def _setup_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        question_setup = self.__setup_snt_2_wrd_question(
            self.__sentence,
            self.__question_type,
        )
        question_word = question_setup["selected_word"]
        selected_words = self.__select_words(question_word)
        alts_stp = self.__setup_word_alternatives(
            question_word,
            selected_words,
            self.__question_type,
        )

        question = SentenceSessionAssessmentQuestion.objects.create(
            assessment=assessment,
            expected_answer=alts_stp["correct_answer"],
            number=question_num,
            question=question_setup["question_txt"],
            audio=question_setup["audio"],
        )

        return PracticeQuestionSetup(
            question=question,
            alternatives=alts_stp["alternatives"],
        )

    def __setup_snt_2_wrd_question(
        self,
        sentence: Sentence,
        question_type: SentenceAssessmentQuestionType,
    ) -> Sentence2WordQuestionSetup:
        selected_word = random.choice(
            Word.objects.filter(word_sentences__sentence=sentence),
        )
        processed_sentence = sentence.value.replace(selected_word.value, "[HIDDEN]")
        audio = ""

        if question_type in {
            "SENTENCE-AUDIO-TO-WORD-AUDIO",
            "SENTENCE-AUDIO-TO-WORD-TEXT",
        }:
            question_txt = "What word is missing in the following audio?"
            audio = self.__get_or_create_audio_for(question_txt)
        elif question_type in {
            "SENTENCE-TEXT-TO-WORD-AUDIO",
            "SENTENCE-TEXT-TO-WORD-TEXT",
        }:
            question_txt = (
                f"What word is missing in the following sentence?\n{processed_sentence}"
            )
        else:
            assert_never(question_type)  # type: ignore[arg-type]

        return Sentence2WordQuestionSetup(
            audio=audio,
            selected_word=selected_word,
            question_txt=question_txt,
        )

    def __select_words(self, word: Word) -> Sequence[Word]:
        words = set(Word.objects.exclude(pk=word.pk))

        return random.sample(
            words.union(
                {
                    word,
                },
            ),
        )

    def __setup_word_alternatives(
        self,
        question_word: Word,
        selected_words: Sequence[Word],
        question_type: SentenceAssessmentQuestionType,
    ) -> AlternativesSetup:
        correct_answer = PracticeSessionAssessmentQuestionAnswer.A
        alt_letters = list(PracticeSessionAssessmentQuestionAnswer)
        alternatives: list[SentenceSessionAssessmentQuestionAlt] = []
        alternative_type = self.__get_alt_type_by_question_type(question_type)

        for ltt_idx, curr_word in enumerate(selected_words):
            if curr_word == question_word:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                SentenceSessionAssessmentQuestionAlt(
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
        question_type: SentenceAssessmentQuestionType,
    ) -> PracticeAssessmentAlternativeTypeChoices:
        if question_type in {
            "SENTENCE-AUDIO-TO-WORD-AUDIO",
            "SENTENCE-TEXT-TO-WORD-AUDIO",
        }:
            return PracticeAssessmentAlternativeTypeChoices.AUDIO

        if question_type in {
            "SENTENCE-AUDIO-TO-WORD-TEXT",
            "SENTENCE-TEXT-TO-WORD-TEXT",
        }:
            return PracticeAssessmentAlternativeTypeChoices.TEXT

        assert_never(question_type)  # type: ignore[arg-type]
        return None

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

    def __get_or_create_audio_for(self, question_txt: str) -> str:
        del question_txt
        raise NotImplementedError
