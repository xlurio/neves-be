from __future__ import annotations

from typing import TYPE_CHECKING
from typing import assert_never
from typing import cast

from neves_be.practice_assessments.constants import ANSWER_CHOICES
from neves_be.practice_assessments.constants import RADICAL_QUESTION_TYPES
from neves_be.practice_assessments.services.assessments import safe_pronounce_url
from neves_be.practice_assessments.services.questions import BasePracticeQuestionFactory
from neves_be.practice_assessments.services.questions import PracticeQuestionSetup
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestion
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestionAlt

if TYPE_CHECKING:
    import random
    from collections.abc import Sequence

    from rest_framework.request import Request

    from neves_be.language_model.models import Radical
    from neves_be.practice_assessments.models import RadicalSessionAssessment
    from neves_be.practice_assessments.types import RadicalAssessmentQuestionType


class RadicalQuestionFactory(BasePracticeQuestionFactory):
    def __init__(
        self,
        request: Request,
        radical: Radical,
        radical_pool: Sequence[Radical],
        rng: random.Random,
    ) -> None:
        self.__request = request
        self.__radical = radical
        self.__rng = rng
        self.__radical_pool = radical_pool

    def _setup_question(
        self,
        assessment: RadicalSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        question_type = RADICAL_QUESTION_TYPES[
            (question_num - 1) % len(RADICAL_QUESTION_TYPES)
        ]
        options = self.__pick_option_radicals(
            self.__radical,
            self.__radical_pool,
            self.__rng,
        )
        question = RadicalSessionAssessmentQuestion.objects.create(  # type: ignore[misc]
            assessment=assessment,
            number=question_num,
            type=question_type,
            question=self.__question_text(self.__radical, question_type),
            audio=self.__radical.pronounce
            if question_type == RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM
            else "",
            expected_answer=ANSWER_CHOICES[options.index(self.__radical)],
        )

        return PracticeQuestionSetup(
            question=question,
            alternatives=self.__build_alternatives(
                self.__request,
                question_type,
                options,
            ),
        )

    def __pick_option_radicals(
        self,
        correct: Radical,
        pool: list[Radical],
        rng: random.Random,
    ) -> list[Radical]:
        distractors = [radical for radical in pool if radical.id != correct.id]
        selected = rng.sample(distractors, k=4)
        options = [*selected, correct]
        rng.shuffle(options)
        return options

    def __question_text(
        self,
        radical: Radical,
        question_type: RadicalAssessmentQuestionType,
    ) -> str:
        if question_type == RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM:
            return "What logogram corresponds to the following audio?"
        if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
            return f"What pronounce corresponds the logogram {radical.id}?"
        if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING:
            return f"What meaning corresponds to the logogram {radical.id}?"
        if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN:
            return f"What pinyin corresponds to the logogram {radical.id}?"
        if question_type == RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM:
            return f'What logogram corresponds to the meaning "{radical.meaning}"?'
        return f'What logogram corresponds to the pinyin "{radical.pinyin}"?'

    def __build_alternatives(
        self,
        request: Request,
        question_type: RadicalAssessmentQuestionType,
        options: list[Radical],
    ) -> Sequence[RadicalSessionAssessmentQuestionAlt]:
        alt_letters = tuple(PracticeSessionAssessmentQuestionAnswer)
        alternatives: list[RadicalSessionAssessmentQuestionAlt] = []

        for ltt_idx, option in enumerate(options):
            if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
                alternatives.append(
                    RadicalSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="AUDIO",
                        payload=safe_pronounce_url(request, option.pronounce),
                    ),
                )
            elif (
                question_type
                == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING
            ):
                alternatives.append(
                    RadicalSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.meaning,
                    ),
                )
            elif (
                question_type
                == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN
            ):
                alternatives.append(
                    RadicalSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.pinyin,
                    ),
                )
            elif question_type in {
                RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM,
                RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM,
                RadicalSessionAssessmentQuestion.Type.PINYIN_TO_LOGOGRAM,
            }:
                alternatives.append(
                    RadicalSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.id,
                    ),
                )
            else:
                assert_never(question_type)

        return cast("Sequence[RadicalSessionAssessmentQuestionAlt]", alternatives)
