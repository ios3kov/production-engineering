#!/usr/bin/env python3
"""Offline REA command planner and raw-result receipt. Never executes a command.

The optional qualification workflow runs the real upstream CLI in a separate
network-disabled container. This planner is not a sandbox or an MCP proxy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
MAX_JSON = 8 * 1024 * 1024
# Deliberately no setup/update, extraction, process/browser capture or debugger console.
OPERATIONS = {
    "inventory": ("inspect-artifact", False, False),
    "javascript": ("analyze-javascript-application", False, False),
    "native-overview": ("analyze", True, False),
    "native-function": ("function", True, True),
    "native-decompile": ("decompile", True, True),
    "native-xrefs": ("xrefs", True, True),
    "view": ("inspect-analysis-view", False, False),
    "feature-trace": ("trace-application-feature", False, False),
    "semantic-trace": ("trace-javascript-semantics", False, False),
    "compare-applications": ("compare-application-versions", False, False),
    "compare-evidence": ("compare", False, False),
}
REQUEST_OPERATIONS = {"view", "feature-trace", "semantic-trace", "compare-applications"}
# Do not trust 6.5.0's exact/complete labels for recovered Webpack exports.
# Conservatively block the whole JS lane and mixed-origin derived workflows;
# no heuristic can reliably prove an arbitrary package is unaffected.
QUARANTINED_OPERATIONS = {
    "javascript", "view", "feature-trace", "semantic-trace",
    "compare-applications", "compare-evidence",
}
QUARANTINE_REASON = (
    "REA 6.5.0 JS/export Evidence is quarantined: morluto/rea#3551 can omit "
    "CommonJS exports while reporting complete coverage. A corrected exact "
    "package and real regression qualification are required."
)


class AdapterError(ValueError):
    pass


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    with path.open("rb") as source:
        raw = source.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise AdapterError("JSON exceeds planner limit; preserve complete Evidence externally")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(AdapterError("Non-finite JSON")))


def absolute_path(value: str, *, must_exist: bool = True) -> Path:
    if not value or "\x00" in value or "\n" in value or "\r" in value:
        raise AdapterError("Invalid path")
    path = Path(value)
    if not path.is_absolute():
        raise AdapterError("An explicit absolute local path is required")
    # Do not silently reinterpret a different source via a symlink.
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise AdapterError("Linked input path is not admitted")
    if must_exist and not path.exists():
        raise AdapterError("Input is unavailable: " + str(path))
    return path


def make_plan(operation: str, target: str, *, cli: str = "rea", selector: str | None = None,
              right: str | None = None, advertised_commands: set[str] | None = None) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise AdapterError("Operation is outside the static profile")
    if cli != "rea" and not Path(cli).is_absolute():
        raise AdapterError("CLI must be rea or an absolute, operator-reviewed executable path")
    if any(c in cli for c in "\x00\n\r"):
        raise AdapterError("Invalid executable path")
    command, native, needs_selector = OPERATIONS[operation]
    if needs_selector:
        if not selector or selector.startswith("-") or len(selector) > 512 or any(c in selector for c in "\x00\n\r"):
            raise AdapterError("A literal function name/address is required")
    elif selector is not None:
        raise AdapterError("This operation takes no selector")
    source = absolute_path(target)
    if not source.is_file() and not (source.is_dir() and operation in {"inventory", "javascript", "native-overview", "native-function", "native-decompile", "native-xrefs"}):
        raise AdapterError("Unsupported input kind")
    if operation in REQUEST_OPERATIONS:
        if not isinstance(read_json(source), dict):
            raise AdapterError("A structured request object is required")
        # The exact REA schema remains upstream's responsibility. No code/string eval.
    args = [cli, command, str(source)]
    if needs_selector:
        args.append(selector)
    if operation == "compare-evidence":
        if not right or not absolute_path(right).is_file():
            raise AdapterError("A second saved Evidence file is required")
        args.append(right)
    elif right is not None:
        raise AdapterError("Unexpected second input")
    if native:
        args += ["--provider", "ghidra"]
    args.append("--json")
    supported = advertised_commands is not None and command in advertised_commands
    blockers = [] if supported else ["Command support in the exact installed package has not been confirmed"]
    if operation in QUARANTINED_OPERATIONS:
        blockers.append(QUARANTINE_REASON)
    return {
        "schema_version": 1,
        "operation": operation,
        "argv": args,
        "package": "rea-agents@6.5.0",
        "execution_status": "NOT_RUN",
        "readiness": "BLOCKED" if blockers else "REQUIRES_HOST_REVIEW",
        "blockers": blockers,
        "required_checks": ["exact package/dependency identity and local executable admission", "authorized target scope", "filesystem/network/process isolation appropriate to this host", "raw output and exit status retained"] + (["Ghidra + compatible Java, real provider probe"] if native else []),
        "product_readiness": "NOT_ASSESSED",
        "limits": ["argv is data, not execution authorization", "The command allowlist is not a sandbox", "Source main and the published package can have different capabilities"],
    }


def receipt(path: str, exit_code: int, *, subject_sha256: str, package_version: str) -> dict[str, Any]:
    """Bind original bytes without translating unknowns or promoting a result to PASS."""
    source = absolute_path(path)
    if not source.is_file():
        raise AdapterError("Raw output must be a regular file")
    if package_version != "6.5.0":
        raise AdapterError("Package version differs from the reviewed profile")
    if not re.fullmatch(r"[0-9a-f]{64}", subject_sha256):
        raise AdapterError("Exact subject SHA-256 required (do not substitute a path or Git SHA)")
    if type(exit_code) is not int or not 0 <= exit_code <= 255:
        raise AdapterError("Exit code must be an integer from 0 to 255")
    with source.open("rb") as fh:
        size = os.fstat(fh.fileno()).st_size
        digest = hashlib.file_digest(fh, "sha256").hexdigest()
    if size == 0:
        raise AdapterError("Empty output cannot be accepted as Evidence")
    return {
        "schema_version": 1,
        "raw_output": {"path": str(source), "sha256": digest, "bytes": size},
        "declared_subject_sha256": subject_sha256,
        "declared_package_version": package_version,
        "declared_exit_code": exit_code,
        "analysis_status": "NEEDS_REVIEW" if exit_code == 0 else "FAILED_OR_INCOMPLETE",
        "product_readiness": "NOT_ASSESSED",
        "limitations": ["Producer, package and subject declarations are not independently authenticated", "Raw REA schema, subject identity, coverage, contradictions and unknowns still need review", "Exit zero may contain partial/cancelled/unsupported results", "Use existing AS/AE Evidence admission; this receipt is not a replacement check record"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("operation", choices=sorted(OPERATIONS))
    plan.add_argument("target")
    plan.add_argument("--cli", default="rea")
    plan.add_argument("--selector")
    plan.add_argument("--right")
    plan.add_argument("--catalog", type=Path, help='Reviewed probe file: {"commands": ["inspect-artifact", ...]}')
    rec = sub.add_parser("receipt")
    rec.add_argument("raw_output")
    rec.add_argument("--exit-code", type=int, required=True)
    rec.add_argument("--subject-sha256", required=True)
    rec.add_argument("--package-version", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            commands = None
            if args.catalog:
                catalog = read_json(args.catalog)
                if not isinstance(catalog, dict) or not isinstance(catalog.get("commands"), list) or not all(isinstance(c, str) for c in catalog["commands"]):
                    raise AdapterError("Invalid reviewed command catalog")
                commands = set(catalog["commands"])
            result = make_plan(args.operation, args.target, cli=args.cli, selector=args.selector, right=args.right, advertised_commands=commands)
        else:
            result = receipt(args.raw_output, args.exit_code, subject_sha256=args.subject_sha256, package_version=args.package_version)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("readiness") == "BLOCKED" else (1 if result.get("analysis_status") == "FAILED_OR_INCOMPLETE" else 0)
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"error": str(error), "status": "BLOCKED", "product_readiness": "NOT_ASSESSED"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
