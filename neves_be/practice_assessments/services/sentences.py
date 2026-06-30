from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import assert_never
from typing import cast

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import Radical
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.practice_assessments.exceptions import (
    CreateSentenceSessionAssessmentError,
)
from neves_be.practice_assessments.models import (
    PracticeAssessmentAlternativeTypeChoices,
)
from neves_be.practice_assessments.models import PracticeSessionAssessmentQuestionAlt
from neves_be.practice_assessments.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.practice_assessments.models import SentenceSessionAssessment
from neves_be.practice_assessments.models import SentenceSessionAssessmentQuestion
from neves_be.practice_assessments.services.assessments import BaseAssessmentAccessor
from neves_be.practice_assessments.services.assessments import BaseAssessmentFactory
from neves_be.sentence_sessions.models import SentenceSession

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db import models

    from neves_be.language_model.types import LogogramId
    from neves_be.language_model.types import SentenceId
    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_assessments.types import SentenceAssessmentQuestionType
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.users.models import User

QUESTION_TYPES: tuple[SentenceAssessmentQuestionType, ...] = (
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_AUDIO,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_AUDIO,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_TEXT,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_TEXT,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_RADICALS,
    ),
)


class SentenceAssessmentAccessor(BaseAssessmentAccessor):
    NOT_FOUND_ERROR_MSG = "Sentence test not found."
    ASSESSMENT_TYPE = SentenceSessionAssessment


class AlternativesSetup(TypedDict):
    correct_answer: PracticeSessionAssessmentQuestionAnswer
    alternatives: Sequence[PracticeSessionAssessmentQuestionAlt]


class Sentence2WordQuestionSetup(TypedDict):
    audio: str
    selected_word: Word
    question_txt: str


class SentenceAssessmentFactory(BaseAssessmentFactory):
    NUM_OF_QUESTIONS = 10
    MINIMUM_WORDS_LEARNED_RATE = 0.8
    MAXIMUM_ITERATIONS = 1e3

    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _session = cast("SentenceSession", session)
        assessment_sentences = self.__get_valid_sentences(_session)

        assessment = SentenceSessionAssessment.objects.create(
            session=_session,
        )
        self.__make_questions(assessment, assessment_sentences)

        return assessment

    def __get_valid_sentences(self, session: SentenceSession) -> Sequence[Sentence]:
        words_learned = set(
            Word.objects.filter(
                word_sentences__sentence__sentence_sessions__session__isnull=False,
            ),
        )

        _user = session.user

        assert _user

        snt_word_mapping = self.__make_snt_wrd_mapping_from_snt_cluster(
            _user,
        )
        snts_lrn_by_user = list(self.__get_learned_sentences_qs(_user))
        assessment_sentences: set[Sentence] = set()
        curr_iters = 0

        while len(assessment_sentences) < self.NUM_OF_QUESTIONS:
            curr_iters += 1

            curr_sentence = random.choice(snts_lrn_by_user)
            words_in_sentence = len(snt_word_mapping[curr_sentence.id])
            words_learning_in_sentence = len(
                words_learned.intersection(snt_word_mapping[curr_sentence.id]),
            )

            if (
                words_learning_in_sentence
                >= words_in_sentence * self.MINIMUM_WORDS_LEARNED_RATE
            ):
                assessment_sentences.add(curr_sentence)
            else:
                snts_lrn_by_user.remove(curr_sentence)

            if curr_iters >= self.MAXIMUM_ITERATIONS:
                raise CreateSentenceSessionAssessmentError(
                    code="NOT_ENOUGH_SENTENCES",
                    title="Assessment locked",
                    details="Learn more sentences to unlock this assessment",
                )

        return cast("Sequence[Sentence]", assessment_sentences)

    def __make_snt_wrd_mapping_from_snt_cluster(
        self,
        user: User,
    ) -> dict[SentenceId, list[Word]]:
        snt_wrd_pairs = set(
            WordSentenceMap.objects.filter(
                sentence_id=self.__get_learned_sentences_qs(user).values_list(
                    "pk",
                    flat=True,
                ),
            ),
        )
        result: dict[SentenceId, list[Word]] = defaultdict(list)

        for snt_wrd_pair in snt_wrd_pairs:
            result[cast("SentenceId", snt_wrd_pair.sentence_id)].append(
                snt_wrd_pair.word,
            )

        return result

    def __get_learned_sentences_qs(self, user: User) -> models.QuerySet[Sentence]:
        user_sessions = SentenceSession.objects.filter(user=user)
        return Sentence.objects.filter(
            sentence_sessions__session_id__in=user_sessions.values_list(
                "pk",
                flat=True,
            ),
        )

    def __make_questions(
        self,
        assessment: SentenceSessionAssessment,
        sentences: Sequence[Sentence],
    ) -> Sequence[SentenceSessionAssessmentQuestion]:
        questions = set()
        alternatives_to_create = []
        number = 1

        for sentence in sentences:
            question_num = number
            audio = ""
            question_type = random.choice(QUESTION_TYPES)

            if SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_RADICALS:
                selected_logograms = self.__select_logograms(assessment.session)
                question_logogram = selected_logograms[random.randint(0, 4)]
                question_txt = self.__make_chr_2_rdcs_txt(question_logogram)
                alts_stp = self.__setup_logogram_alternatives(
                    question_logogram,
                    selected_logograms,
                )
                expected_answer = alts_stp["correct_answer"]
                alternatives = alts_stp["alternatives"]

            else:
                question_setup = self.__setup_snt_2_wrd_question(
                    sentence,
                    question_type,
                )
                question_txt = question_setup["question_txt"]
                audio = question_setup["audio"]
                question_word = question_setup["selected_word"]
                selected_words = self.__select_words(question_word)
                alts_stp = self.__setup_word_alternatives(
                    question_word,
                    selected_words,
                    question_type,
                )
                expected_answer = alts_stp["correct_answer"]
                alternatives = alts_stp["alternatives"]

            question = SentenceSessionAssessmentQuestion.objects.create(
                number=question_num,
                question=question_txt,
                audio=audio,
                expected_answer=expected_answer,
                assessment=assessment,
            )
            questions.add(question)

            for alt in alternatives:
                alt.question = question
                alternatives_to_create.append(alt)

            number += 1

        PracticeSessionAssessmentQuestionAlt.objects.bulk_create(alternatives_to_create)

        return cast("Sequence[SentenceSessionAssessmentQuestion]", questions)

    def __make_chr_2_rdcs_txt(self, logogram: Logogram) -> str:
        return f"What radicals compose the character {logogram.id}?"

    def __select_logograms(self, session: SentenceSession) -> Sequence[Logogram]:
        avlbl_logograms = list(
            Logogram.objects.filter(
                **{  # noqa: PIE804
                    "logogram_words__word__word_sentences__sentence__"
                    "sentence_sessions__session__user": session.user,
                },
            ),
        )

        return cast("Sequence[Logogram]", random.sample(avlbl_logograms, k=5))

    def __setup_logogram_alternatives(
        self,
        question_logogram: Logogram,
        selected_logograms: Sequence[Logogram],
    ) -> AlternativesSetup:
        correct_answer = PracticeSessionAssessmentQuestionAnswer.A
        alt_letters = list(PracticeSessionAssessmentQuestionAnswer)
        alternatives: list[PracticeSessionAssessmentQuestionAlt] = []
        lgg_rdcs_mapping = self.__make_lgg_rdcs_mapping(selected_logograms)

        for ltt_idx, curr_char in enumerate(selected_logograms):
            if curr_char == question_logogram:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                PracticeSessionAssessmentQuestionAlt(
                    letter=alt_letters[ltt_idx],
                    type=PracticeAssessmentAlternativeTypeChoices.TEXT,
                    payload=" ".join(
                        radical.id for radical in lgg_rdcs_mapping[curr_char.id]
                    ),
                ),
            )

        return AlternativesSetup(
            correct_answer=correct_answer,
            alternatives=alternatives,
        )

    def __make_lgg_rdcs_mapping(
        self,
        logograms: Sequence[Logogram],
    ) -> dict[LogogramId, list[Radical]]:
        lgg_rdcs_pairs = RadicalLogogramMap.objects.filter(logogram__in=logograms)
        result: dict[LogogramId, list[Radical]] = defaultdict(list)

        for lgg_rdcs_pair in lgg_rdcs_pairs:
            result[lgg_rdcs_pair.logogram_id].append(lgg_rdcs_pair.radical)

        return result

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

    def __get_or_create_audio_for(self, question_txt: str) -> str:
        del question_txt
        raise NotImplementedError

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
        alternatives: list[PracticeSessionAssessmentQuestionAlt] = []
        alternative_type = self.__get_alt_type_by_question_type(question_type)

        for ltt_idx, curr_word in enumerate(selected_words):
            if curr_word == question_word:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                PracticeSessionAssessmentQuestionAlt(
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
