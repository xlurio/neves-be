from __future__ import annotations

from typing import TYPE_CHECKING
from typing import NewType

if TYPE_CHECKING:
    from collections.abc import Sequence

Tone = NewType("Tone", int)


class ToneAccessor:
    def get_tone_for_pinyin(
        self,
        pinyin: str,
        char_tone_pairs: Sequence[tuple[str, Tone]],
        *,
        start_pinyin_idx: int,
        end_pinyin_idx: int,
        start_map_idx: int,
        end_map_idx: int,
    ) -> Tone:
        automata_state = 0

        assert start_pinyin_idx >= 0
        assert end_pinyin_idx >= 0
        assert start_map_idx >= 0
        assert end_map_idx >= 0
        assert end_pinyin_idx >= start_pinyin_idx
        assert end_map_idx >= start_map_idx

        if start_map_idx == end_map_idx:
            automata_state |= 0b01

        if start_pinyin_idx == end_pinyin_idx:
            automata_state |= 0b10

        return self.__GET_TONE_FOR_PINYIN_AUTOMATA[automata_state](
            self,
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=start_pinyin_idx,
            end_pinyin_idx=end_pinyin_idx,
            start_map_idx=start_map_idx,
            end_map_idx=end_map_idx,
        )

    def _get_tone_for_pinyin_part_all(
        self,
        pinyin: str,
        char_tone_pairs: Sequence[tuple[str, Tone]],
        *,
        start_pinyin_idx: int,
        end_pinyin_idx: int,
        start_map_idx: int,
        end_map_idx: int,
    ) -> Tone:
        mid_pinyin_idx = ((end_pinyin_idx - start_pinyin_idx) // 2) + start_pinyin_idx
        mid_map_idx = ((end_map_idx - start_map_idx) // 2) + start_map_idx

        if tone := self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=start_pinyin_idx,
            end_pinyin_idx=mid_pinyin_idx,
            start_map_idx=start_map_idx,
            end_map_idx=mid_map_idx,
        ):
            return tone

        if tone := self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=mid_pinyin_idx + 1,
            end_pinyin_idx=end_pinyin_idx,
            start_map_idx=start_map_idx,
            end_map_idx=mid_map_idx,
        ):
            return tone

        if tone := self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=start_pinyin_idx,
            end_pinyin_idx=mid_pinyin_idx,
            start_map_idx=mid_map_idx + 1,
            end_map_idx=end_map_idx,
        ):
            return tone

        return self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=mid_pinyin_idx + 1,
            end_pinyin_idx=end_pinyin_idx,
            start_map_idx=mid_map_idx + 1,
            end_map_idx=end_map_idx,
        )

    def _get_tone_for_pinyin_part_map(
        self,
        pinyin: str,
        char_tone_pairs: Sequence[tuple[str, Tone]],
        *,
        start_pinyin_idx: int,
        end_pinyin_idx: int,
        start_map_idx: int,
        end_map_idx: int,
    ) -> Tone:
        pinyin_idx = start_pinyin_idx
        del start_pinyin_idx, end_pinyin_idx

        mid_map_idx = ((end_map_idx - start_map_idx) // 2) + start_map_idx

        if tone := self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=pinyin_idx,
            end_pinyin_idx=pinyin_idx,
            start_map_idx=start_map_idx,
            end_map_idx=mid_map_idx,
        ):
            return tone

        return self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=pinyin_idx,
            end_pinyin_idx=pinyin_idx,
            start_map_idx=mid_map_idx + 1,
            end_map_idx=end_map_idx,
        )

    def _get_tone_for_pinyin_part_pinyin(
        self,
        pinyin: str,
        char_tone_pairs: Sequence[tuple[str, Tone]],
        *,
        start_pinyin_idx: int,
        end_pinyin_idx: int,
        start_map_idx: int,
        end_map_idx: int,
    ) -> Tone:
        map_idx = start_map_idx
        del start_map_idx, end_map_idx

        mid_pinyin_idx = ((end_pinyin_idx - start_pinyin_idx) // 2) + start_pinyin_idx

        if tone := self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=start_pinyin_idx,
            end_pinyin_idx=mid_pinyin_idx,
            start_map_idx=map_idx,
            end_map_idx=map_idx,
        ):
            return tone

        return self.get_tone_for_pinyin(
            pinyin,
            char_tone_pairs,
            start_pinyin_idx=mid_pinyin_idx + 1,
            end_pinyin_idx=end_pinyin_idx,
            start_map_idx=map_idx,
            end_map_idx=map_idx,
        )

    def _get_tone_for_pinyin_proc(
        self,
        pinyin: str,
        char_tone_pairs: Sequence[tuple[str, Tone]],
        *,
        start_pinyin_idx: int,
        end_pinyin_idx: int,
        start_map_idx: int,
        end_map_idx: int,
    ) -> Tone:
        pinyin_idx = start_pinyin_idx
        map_idx = start_map_idx

        del start_pinyin_idx, end_pinyin_idx, start_map_idx, end_map_idx

        if (
            pinyin[pinyin_idx] == char_tone_pairs[map_idx][0]
            and char_tone_pairs[map_idx][1]
        ):
            return char_tone_pairs[map_idx][1]

        return None

    __GET_TONE_FOR_PINYIN_AUTOMATA = (
        _get_tone_for_pinyin_part_all,  # 00
        _get_tone_for_pinyin_part_pinyin,  # 01
        _get_tone_for_pinyin_part_map,  # 10
        _get_tone_for_pinyin_proc,  # 11
    )
