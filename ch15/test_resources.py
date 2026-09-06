import unittest
from resources import (accounting, resource_trials, Meter, ReadCache, schedule,
                       cache_example, cancellation_example)
from chapter2 import ToolCall, Final, Event


class AccountingTests(unittest.TestCase):
    def test_failures_remain_in_numerator(self):
        result = accounting([{'passed': True, 'estimated_units': 10},
                             {'passed': False, 'estimated_units': 90}])
        self.assertEqual(result['estimated_units_per_accepted'], 100)

    def test_no_acceptance_is_undefined(self):
        self.assertIsNone(accounting([{'passed': False, 'estimated_units': 3}])
                          ['estimated_units_per_accepted'])

    def test_unknown_cost_is_not_zero(self):
        result = accounting([{'passed': True, 'estimated_units': None}])
        self.assertIsNone(result['estimated_total_units'])

    def test_unknown_verdict_remains_visible(self):
        result = accounting([{'passed': None, 'estimated_units': 4}])
        self.assertEqual(result['unknown'], 1)
        self.assertEqual(result['tasks'], 1)

    def test_empty_population(self):
        self.assertIsNone(accounting([])['estimated_units_per_accepted'])

    def test_controls_keep_expected_acceptance(self):
        rows = resource_trials()
        self.assertEqual(len(rows), 20)
        for config, expected in [('full', 5), ('fixed', 2), ('no_reads', 1),
                                 ('declared_route', 5)]:
            self.assertEqual(sum(r['passed'] for r in rows
                                 if r['config'] == config), expected)
        self.assertTrue(all(r['provider_tokens'] is None for r in rows))

    def test_meter_counts_failed_decision(self):
        class Broken:
            def next(self, task, events):
                raise RuntimeError('failed')
        meter = Meter(Broken())
        with self.assertRaises(RuntimeError):
            meter.next('task', ())
        self.assertEqual(meter.calls, 1)
        self.assertGreater(meter.input_bytes, 0)

    def test_meter_has_explicit_utf8_encoding(self):
        class Done:
            def next(self, task, events):
                return Final('done')
        meter = Meter(Done())
        meter.next('é', ())
        self.assertEqual(meter.input_bytes, len('{"events": [], "task": "é"}'
                                                .encode('utf-8')))


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.cache = {}
        self.tool = ReadCache({'a': 'one', 'hidden': 'secret'}, self.cache,
                              'scope-a', {'a'})
        self.call = ToolCall('r', 'read_file', {'path': 'a'})

    def test_warm_read(self):
        self.assertEqual(self.tool.execute(self.call), self.tool.execute(self.call))
        self.assertEqual((self.tool.hits, self.tool.misses), (1, 1))

    def test_source_change_misses(self):
        self.tool.execute(self.call)
        self.tool.files['a'] = 'two'
        self.assertEqual(self.tool.execute(self.call)['data']['text'], 'two')
        self.assertEqual(self.tool.misses, 2)

    def test_revocation_precedes_hit(self):
        self.tool.execute(self.call)
        self.tool.allowed.clear()
        self.assertEqual(self.tool.execute(self.call)['error'], 'denied')
        self.assertEqual(self.tool.hits, 0)

    def test_scope_separation(self):
        self.tool.execute(self.call)
        other = ReadCache({'a': 'one'}, self.cache, 'scope-b', {'a'})
        other.execute(self.call)
        self.assertEqual(other.misses, 1)

    def test_version_separation(self):
        self.tool.execute(self.call)
        other = ReadCache({'a': 'one'}, self.cache, 'scope-a', {'a'}, 'read-v2')
        other.execute(self.call)
        self.assertEqual(other.misses, 1)

    def test_cached_result_cannot_be_mutated_by_caller(self):
        result = self.tool.execute(self.call)
        result['data']['text'] = 'poison'
        self.assertEqual(self.tool.execute(self.call)['data']['text'], 'one')

    def test_search_respects_same_access(self):
        result = self.tool.execute(ToolCall('s', 'search', {'query': 'secret'}))
        self.assertEqual(result['data']['matches'], [])

    def test_dispatch_rejects_invalid_request(self):
        result = self.tool.execute(ToolCall('r', 'read_file', {'path': 'a', 'x': 1}))
        self.assertEqual(result['error'], 'invalid_arguments')
        self.assertFalse(self.cache)

    def test_removed_source_is_not_served(self):
        self.tool.execute(self.call)
        del self.tool.files['a']
        self.assertEqual(self.tool.execute(self.call)['error'], 'unknown_file')


class SchedulingTests(unittest.TestCase):
    def test_queue_wait_is_in_completion_time(self):
        report = schedule([100, 100, 100, 1000], 1)
        self.assertEqual(report['makespan_ms'], 1300)
        self.assertEqual(report['jobs'][-1]['queue_ms'], 300)

    def test_parallelism_does_not_reduce_work(self):
        reports = [schedule([100, 100, 100, 1000], n) for n in (1, 2, 4)]
        self.assertEqual([r['makespan_ms'] for r in reports], [1300, 1100, 1000])
        self.assertTrue(all(r['service_ms_total'] == 1300 for r in reports))

    def test_invalid_schedule_inputs(self):
        for durations, workers in [([0], 1), ([True], 1), ([1], 0), ([1], True)]:
            with self.assertRaises(ValueError):
                schedule(durations, workers)

    def test_empty_schedule(self):
        self.assertEqual(schedule([], 2)['makespan_ms'], 0)

    def test_cancelled_decision_does_not_dispatch_late_tool(self):
        self.assertEqual(cancellation_example(),
                         {'status': 'cancelled', 'decision_calls': 1,
                          'tool_requests': 0})


if __name__ == '__main__':
    unittest.main()
