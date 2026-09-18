from __future__ import annotations

import re

from app.models.schemas import SandboxResult, TestResult

__test__ = False

_COUNT_RE = re.compile(r"(?P<count>\d+)\s+(?P<label>failed|passed|skipped)")


def parse_test_result(result: SandboxResult) -> TestResult:
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    passed = failed = skipped = 0
    for line in output.splitlines():
        if "passed" in line or "failed" in line or "skipped" in line:
            counts = {match.group("label"): int(match.group("count")) for match in _COUNT_RE.finditer(line)}
            if counts:
                passed = counts.get("passed", 0)
                failed = counts.get("failed", 0)
                skipped = counts.get("skipped", 0)
    total = passed + failed + skipped
    status = "error" if result.status == "error" or result.error_message else ("passed" if result.exit_code == 0 else "failed")
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
