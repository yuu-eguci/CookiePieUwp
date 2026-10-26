import os
import tempfile
import unittest

import check_trx


def make_trx(passed=1, failed_tests=(), error=0, executed=None, extra_results=""):
    failed = len(failed_tests)
    if executed is None:
        executed = passed + failed
    results = "".join(
        '<UnitTestResult testName="{}" outcome="Failed" />'.format(name)
        for name in failed_tests
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">'
        "<Results>{results}{extra}</Results>"
        '<ResultSummary outcome="{outcome}">'
        '<Counters total="{executed}" executed="{executed}" passed="{passed}" '
        'failed="{failed}" error="{error}" timeout="0" aborted="0" '
        'inconclusive="0" notExecuted="0" />'
        "</ResultSummary></TestRun>"
    ).format(
        results=results,
        extra=extra_results,
        outcome="Failed" if failed else "Completed",
        executed=executed,
        passed=passed,
        failed=failed,
        error=error,
    )


class CheckTests(unittest.TestCase):
    def test_all_passed_with_zero_exit_code_is_ok(self):
        self.assertEqual([], check_trx.check(make_trx(passed=3), 0, []))

    def test_zero_executed_tests_is_an_error(self):
        errors = check_trx.check(make_trx(passed=0), 0, [])
        self.assertTrue(any("executed 0" in e for e in errors), errors)

    def test_unexpected_failure_is_an_error(self):
        errors = check_trx.check(make_trx(passed=1, failed_tests=["Foo"]), 1, [])
        self.assertTrue(any("Foo" in e for e in errors), errors)

    def test_nonzero_exit_code_without_failures_is_an_error(self):
        errors = check_trx.check(make_trx(passed=1), 1, [])
        self.assertTrue(any("exit code" in e for e in errors), errors)

    def test_expected_failure_with_nonzero_exit_code_is_ok(self):
        trx = make_trx(passed=1, failed_tests=["AddOne_IntentionalFailure"])
        self.assertEqual(
            [], check_trx.check(trx, 1, ["AddOne_IntentionalFailure"])
        )

    def test_expected_failure_with_zero_exit_code_is_an_error(self):
        trx = make_trx(passed=1, failed_tests=["AddOne_IntentionalFailure"])
        errors = check_trx.check(trx, 0, ["AddOne_IntentionalFailure"])
        self.assertTrue(any("exit code" in e for e in errors), errors)

    def test_expected_failure_that_passed_is_an_error(self):
        errors = check_trx.check(make_trx(passed=2), 1, ["AddOne_IntentionalFailure"])
        self.assertTrue(any("AddOne_IntentionalFailure" in e for e in errors), errors)

    def test_other_failure_instead_of_expected_one_is_an_error(self):
        trx = make_trx(passed=1, failed_tests=["Other"])
        errors = check_trx.check(trx, 1, ["AddOne_IntentionalFailure"])
        self.assertTrue(any("Other" in e for e in errors), errors)

    def test_only_expected_failure_and_no_pass_is_an_error(self):
        trx = make_trx(passed=0, failed_tests=["AddOne_IntentionalFailure"])
        errors = check_trx.check(trx, 1, ["AddOne_IntentionalFailure"])
        self.assertTrue(any("passed 0" in e for e in errors), errors)

    def test_failed_counter_without_named_result_is_an_error(self):
        trx = make_trx(passed=1).replace('failed="0"', 'failed="1"')
        errors = check_trx.check(trx, 0, [])
        self.assertTrue(any("failed=1" in e for e in errors), errors)

    def test_errored_tests_are_an_error(self):
        errors = check_trx.check(make_trx(passed=1, error=1, executed=2), 1, [])
        self.assertTrue(any("error=1" in e for e in errors), errors)

    def test_missing_counters_is_an_error(self):
        trx = (
            '<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">'
            "</TestRun>"
        )
        errors = check_trx.check(trx, 0, [])
        self.assertTrue(any("Counters" in e for e in errors), errors)

    def test_malformed_xml_is_an_error(self):
        errors = check_trx.check("<TestRun", 0, [])
        self.assertTrue(any("parse" in e for e in errors), errors)


class MainTests(unittest.TestCase):
    def test_missing_trx_file_fails(self):
        self.assertEqual(1, check_trx.main(["--trx", "no-such.trx", "--exit-code", "0"]))

    def test_passing_trx_file_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "result.trx")
            with open(path, "w", encoding="utf-8") as f:
                f.write(make_trx(passed=1))
            self.assertEqual(0, check_trx.main(["--trx", path, "--exit-code", "0"]))

    def test_expected_failure_argument_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "result.trx")
            with open(path, "w", encoding="utf-8") as f:
                f.write(make_trx(passed=1, failed_tests=["AddOne_IntentionalFailure"]))
            self.assertEqual(
                0,
                check_trx.main(
                    [
                        "--trx",
                        path,
                        "--exit-code",
                        "1",
                        "--expect-failed",
                        "AddOne_IntentionalFailure",
                    ]
                ),
            )


if __name__ == "__main__":
    unittest.main()
