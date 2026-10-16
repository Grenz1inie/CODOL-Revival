import unittest

from benchmark_match import compare_frames, compare_states, percentiles, scenario


class MatchBenchmarkTests(unittest.TestCase):
    def test_percentiles_are_nearest_rank_and_include_worst_pause(self):
        result = percentiles(list(range(1, 101)))
        self.assertEqual((result['p95_ms'], result['p99_ms'], result['max_ms']), (95, 99, 100))
        self.assertEqual(result['count'], 100)

    def test_replay_is_deterministic_and_has_delayed_frame_and_menu_idle(self):
        first = scenario(352)
        self.assertEqual(first, scenario(352))
        self.assertGreaterEqual(len(first['frames']), 240)
        self.assertTrue(any(f['milliseconds'] > 50 for f in first['frames']))
        self.assertTrue(any(not f['commands'] for f in first['frames']))
        times = [c['time'] for f in first['frames'] for c in f['commands']]
        self.assertEqual(times, sorted(set(times)))

    def test_comparison_requires_exact_integer_state_but_tolerates_float_rounding(self):
        compare_states({'origin': [1.0], 'health': 100}, {'origin': [1.0000001], 'health': 100})
        with self.assertRaisesRegex(AssertionError, 'health'):
            compare_states({'health': 100}, {'health': 99})
        with self.assertRaisesRegex(AssertionError, 'origin'):
            compare_states({'origin': [1.0]}, {'origin': [1.1]})
        with self.assertRaises(AssertionError):
            compare_states({'health': 100}, {})

    def test_wire_float_words_are_numeric_but_event_ids_remain_exact(self):
        before = dict(time=1050, players=[], fields={'13': 2822545336, '1': 3}, wire='00')
        after = dict(time=1050, players=[], fields={'13': 2822544928, '1': 3}, wire='01')
        self.assertEqual(compare_frames([before], [after]), 0)
        after['fields']['1'] = 4
        with self.assertRaisesRegex(AssertionError, 'fields.1'):
            compare_frames([before], [after])


if __name__ == '__main__':
    unittest.main()
