"""Verify a vstest TRX result so that CI cannot pass without really running tests.

vstest can exit successfully when it discovers no tests, so the exit code alone
is not trusted. This script checks the TRX counters, the names of failed tests
and the vstest exit code together.
"""
import argparse
import sys
import xml.etree.ElementTree as ET

NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def check(trx_text, exit_code, expected_failed):
    """Return a list of error messages. An empty list means the run is as expected."""
    try:
        root = ET.fromstring(trx_text)
    except ET.ParseError as e:
        return ["could not parse TRX: {}".format(e)]

    counters = root.find("t:ResultSummary/t:Counters", NS)
    if counters is None:
        return ["TRX has no ResultSummary/Counters element"]

    def count(name):
        return int(counters.get(name, "0"))

    errors = []
    executed = count("executed")
    passed = count("passed")
    if executed < 1:
        errors.append("executed {} tests; expected at least 1".format(executed))
    if passed < 1:
        errors.append("passed {} tests; expected at least 1".format(passed))
    for name in ("error", "timeout", "aborted"):
        if count(name):
            errors.append("{}={} in TRX counters".format(name, count(name)))
    if not expected_failed and count("failed"):
        errors.append("failed={} in TRX counters".format(count("failed")))

    failed = {
        r.get("testName")
        for r in root.iterfind("t:Results/t:UnitTestResult[@outcome='Failed']", NS)
    }
    for name in sorted(failed - set(expected_failed)):
        errors.append("unexpected failed test: {}".format(name))
    for name in sorted(set(expected_failed) - failed):
        errors.append("expected failed test did not fail: {}".format(name))

    if expected_failed and exit_code == 0:
        errors.append("vstest exit code is 0 although failures were expected")
    if not expected_failed and exit_code != 0:
        errors.append("vstest exit code is {}; expected 0".format(exit_code))
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trx", required=True, help="path to the TRX file")
    parser.add_argument("--exit-code", type=int, required=True, help="vstest exit code")
    parser.add_argument(
        "--expect-failed",
        action="append",
        default=[],
        metavar="TEST_NAME",
        help="test that must fail (repeatable); no other test may fail",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.trx, encoding="utf-8-sig") as f:
            trx_text = f.read()
    except OSError as e:
        print("error: could not read TRX: {}".format(e))
        return 1

    errors = check(trx_text, args.exit_code, args.expect_failed)
    for error in errors:
        print("error: {}".format(error))
    if errors:
        return 1
    print("TRX check passed: {}".format(args.trx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
