from __future__ import annotations

import re

from app.models.schemas import SandboxResult, TestResult

_SUMMARY_RE = re.compile(r"(?:(?P<failed>\d+) failed)?(?:, )?(?:(?P<passed>\d+) passed)?(?:, )?(?:(?P<skipped>\d+) skipped)?")


def parse_test_result(result: SandboxResult) -> TestResult:
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    passed = failed = skipped = 0
    for line in output.splitlines():
        if "passed" in line or "failed" in line or "skipped" in line:
            match = _SUMMARY_RE.search(line)
            if match:
                passed = int(match.group("passed") or 0)
                failed = int(match.group("failed") or 0)
                skipped = int(match.group("skipped") or 0)
    total = passed + failed + skipped
    status = "passed" if result.exit_code == 0 else ("failed" if result.status == "failed" else "error")
    return TestResult(
        status=status,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration=result.duration,
        stdout=result.stdout,
        stderr=result.stderr,
    )
