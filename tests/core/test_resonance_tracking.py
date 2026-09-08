from __future__ import annotations

import math
import unittest

from sim_spr_lmr.core.domain import ResonanceDetection
from sim_spr_lmr.core.optics import track_resonances_by_continuity


def detection(position: float) -> ResonanceDetection:
    return ResonanceDetection(position=position, fwhm=10.0, minimum_response=0.1)


class ResonanceTrackingTests(unittest.TestCase):
    def test_crossing_modes_keep_their_directional_identity(self) -> None:
        tracks = track_resonances_by_continuity(
            [
                [detection(400), detection(600)],
                [detection(440), detection(560)],
                [detection(480), detection(520)],
                [detection(480), detection(520)],
            ],
            [0, 1, 2, 3],
            response_axis_span=400,
            response_axis_resolution=1,
        )

        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].positions, [400, 440, 480, 520])
        self.assertEqual(tracks[1].positions, [600, 560, 520, 480])

    def test_missing_detection_is_nan_and_track_is_reacquired(self) -> None:
        tracks = track_resonances_by_continuity(
            [
                [detection(400), detection(600)],
                [detection(420), detection(580)],
                [detection(560)],
                [detection(460), detection(540)],
            ],
            [0, 1, 2, 3],
            response_axis_span=300,
            response_axis_resolution=1,
        )

        self.assertTrue(math.isnan(tracks[0].positions[2]))
        self.assertEqual(tracks[0].positions[3], 460)
        self.assertEqual(tracks[1].positions, [600, 580, 560, 540])

    def test_new_resonance_starts_with_nan_history(self) -> None:
        tracks = track_resonances_by_continuity(
            [[detection(500)], [detection(510), detection(700)]],
            [0, 1],
            response_axis_span=400,
            response_axis_resolution=1,
        )

        self.assertEqual(len(tracks), 2)
        self.assertTrue(math.isnan(tracks[1].positions[0]))
        self.assertEqual(tracks[1].positions[1], 700)

    def test_single_resonance_is_reassociated_after_absence_or_large_jump(self) -> None:
        tracks = track_resonances_by_continuity(
            [
                [detection(400)],
                [],
                [detection(940)],
                [detection(770)],
            ],
            [60, 61, 62, 63],
            response_axis_span=600,
            response_axis_resolution=1,
            single_resonance=True,
        )

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].positions[0], 400)
        self.assertTrue(math.isnan(tracks[0].positions[1]))
        self.assertEqual(tracks[0].positions[2:], [940, 770])


if __name__ == "__main__":
    unittest.main()
