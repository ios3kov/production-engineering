#!/usr/bin/env python3
"""Build and run the pinned repaired REA in a fresh owned prefix (not a sandbox)."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import urllib.request
import zipfile

COMMIT = "20643d4a47b0562aa794f0a15903630c62912c80"
REPO = "https://github.com/dakjdakd/rea.git"
GHIDRA_SHA = "ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db"
GHIDRA_URL = "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.4_build/ghidra_12.1.4_PUBLIC_20260921.zip"
HERE = Path(__file__).resolve().parent
OPS = {"inventory": "inspect-artifact", "javascript": "analyze-javascript-application",
       "feature-trace": "trace-application-feature", "compare-applications": "compare-application-versions",
       "view": "inspect-analysis-view", "native-overview": "analyze", "native-function": "function",
       "dependencies": "trace-dylib-resolution"}
MCP_TOOLS = ["binary_session", "open_binary", "close_binary", "inspect_artifact",
             "trace_dylib_resolution", "binary_overview", "analyze_function",
             "analyze_javascript_application", "trace_application_feature",
             "compare_application_versions", "inspect_analysis_view"]


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def local_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute() or any(c in str(path) for c in "\x00\n\r"):
        raise ValueError("An absolute local path is required")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlinked paths are not admitted; use the actual canonical path")
    return path


def tree_digest(root: Path) -> str:
    """Commit exact file bytes and link targets; never follow a link outside root."""
    digest = hashlib.sha256()
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(names + [d for d in dirs if (Path(directory) / d).is_symlink()]):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError("Runtime contains an external symlink: " + relative)
                item = [relative, "link", os.readlink(path)]
            elif path.is_file():
                item = [relative, "file", sha(path)]
            else:
                raise ValueError("Runtime contains a nonregular file: " + relative)
            digest.update(json.dumps(item, ensure_ascii=True, separators=(",", ":")).encode() + b"\n")
    return digest.hexdigest()


def environment(prefix: Path, java_home: str | None = None) -> dict[str, str]:
    # Do not inherit tokens, proxy credentials, NODE_OPTIONS, or the user's home/config.
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(prefix / "home"),
           "TMPDIR": str(prefix / "tmp"), "LANG": "en_US.UTF-8", "NO_COLOR": "1",
           "REA_RUNTIME": str(prefix / "source"), "REA_OUTPUT": str(prefix / "evidence"),
           "GHIDRA_INSTALL_DIR": str(prefix / "ghidra_12.1.4_PUBLIC")}
    if java_home:
        env["JAVA_HOME"] = java_home
    return env


def execute(argv: list[str], cwd: Path, env: dict[str, str], out: Path, timeout: int = 900) -> int:
    """Preserve full output; terminate the owned process group on timeout."""
    with out.with_suffix(".stdout").open("xb") as stdout, out.with_suffix(".stderr").open("xb") as stderr:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            return process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise


def require_run(argv: list[str], prefix: Path, env: dict[str, str], label: str, cwd: Path | None = None) -> None:
    print(label, file=sys.stderr, flush=True)
    code = execute(argv, cwd or prefix, env, prefix / "evidence" / label)
    if code:
        raise RuntimeError(f"{label} failed ({code}); inspect {prefix / 'evidence' / label}.stderr")


def config_text(prefix: Path) -> str:
    return ("# Merge this fragment only after reviewing it; existing configuration is not edited.\n"
            "[mcp_servers.rea_static]\ncommand = " + json.dumps(sys.executable) + "\nargs = " +
            json.dumps([str(HERE / "runtime.py"), "mcp", str(prefix)]) +
            "\nstartup_timeout_sec = 180\ntool_timeout_sec = 360\nenabled_tools = " + json.dumps(MCP_TOOLS) + "\n")


def install(prefix: Path, apply: bool) -> None:
    if prefix.exists():
        raise ValueError("Installation prefix must be new; an existing installation is never overwritten")
    if not apply:
        print(json.dumps({"status": "PLANNED", "prefix": str(prefix), "source": REPO, "commit": COMMIT,
                          "ghidra_sha256": GHIDRA_SHA, "client_configuration": "NOT_CHANGED"}, indent=2))
        return
    if sys.platform not in ("linux", "darwin"):
        raise ValueError("This qualified installer supports Linux and macOS, not native Windows")
    node = shutil.which("node")
    if not node or subprocess.check_output([node, "--version"], text=True).strip() != "v24.18.0":
        raise ValueError("Use already installed Node 24.18.0; this installer does not upgrade Node")
    for tool in ("git", "npm", "java", "cc", "python3", "unzip"):
        if not shutil.which(tool):
            raise ValueError("Missing prerequisite: " + tool)
    prefix.mkdir(mode=0o700, parents=False)
    for name in ("home", "tmp", "evidence", "source"):
        (prefix / name).mkdir(mode=0o700)
    java_home = os.environ.get("JAVA_HOME")
    env = environment(prefix, java_home)
    env["PATH"] = str(Path(node).parent) + os.pathsep + env["PATH"]
    source = prefix / "source"
    for label, args in [
        ("git-init", ["git", "init", str(source)]),
        ("git-remote", ["git", "-C", str(source), "remote", "add", "origin", REPO]),
        ("git-fetch", ["git", "-C", str(source), "fetch", "--depth=1", "origin", COMMIT]),
        ("git-checkout", ["git", "-C", str(source), "checkout", "--detach", "FETCH_HEAD"]),
    ]:
        require_run(args, prefix, env, label)
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], env=env, text=True).strip()
    if head != COMMIT:
        raise ValueError("Source commit mismatch")
    require_run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org"], prefix, env, "npm-ci", source)
    require_run(["npm", "run", "compile"], prefix, {**env, "NODE_OPTIONS": "--max-old-space-size=4096"}, "compile", source)
    archive = prefix / "ghidra.zip"
    with urllib.request.urlopen(GHIDRA_URL, timeout=90) as response, archive.open("xb") as destination:
        shutil.copyfileobj(response, destination)
    if sha(archive) != GHIDRA_SHA:
        raise ValueError("Ghidra archive integrity mismatch")
    with zipfile.ZipFile(archive) as zipped:
        for info in zipped.infolist():
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsafe Ghidra archive member")
    # unzip preserves executable bits that Python's extractall does not.
    require_run(["unzip", "-q", str(archive), "-d", str(prefix)], prefix, env, "ghidra-extract")
    engine = prefix / "ghidra_12.1.4_PUBLIC"
    if sys.platform == "darwin" or platform.machine().lower() not in ("x86_64", "amd64"):
        require_run(["./gradlew", "--no-daemon", "buildNatives"], prefix, env, "ghidra-native-build", engine / "support" / "gradle")
    for filename in ("repair-check.mjs", "capability-check.mjs"):
        require_run([node, str(HERE / filename)], prefix, env, "qualify-" + filename.removesuffix(".mjs"))
    for name in ("repair-report.json", "capability-report.json"):
        report = json.loads((prefix / "evidence" / name).read_text())
        if report.get("status") != "PASS" or report.get("source_commit") != COMMIT:
            raise ValueError("Qualification did not pass: " + name)
    manifest = {"schema_version": 1, "source_commit": COMMIT, "node": str(Path(node).resolve()),
                "node_sha256": sha(Path(node)), "source_tree_sha256": tree_digest(source),
                "engine_tree_sha256": tree_digest(engine), "ghidra_archive_sha256": GHIDRA_SHA,
                "java_home": java_home, "host": [sys.platform, platform.machine()],
                "reports": {name: sha(prefix / "evidence" / name) for name in ("repair-report.json", "capability-report.json")},
                "limits": "Local integrity receipt, not independent attestation or a security sandbox"}
    (prefix / "runtime.json").write_text(json.dumps(manifest, indent=2))
    (prefix / "codex-fragment.toml").write_text(config_text(prefix))
    print(json.dumps({"status": "INSTALLED_AND_FIXTURE_QUALIFIED", "prefix": str(prefix), "client_activation": "NOT_PERFORMED"}))


def verify(prefix: Path) -> dict:
    manifest = json.loads((prefix / "runtime.json").read_text())
    if manifest.get("source_commit") != COMMIT or manifest.get("host") != [sys.platform, platform.machine()]:
        raise ValueError("Unqualified source or host")
    for target, expected in [(Path(manifest["node"]), manifest["node_sha256"])]:
        if sha(target) != expected:
            raise ValueError("Node changed since qualification")
    for name, key in (("source", "source_tree_sha256"), ("ghidra_12.1.4_PUBLIC", "engine_tree_sha256")):
        if tree_digest(prefix / name) != manifest[key]:
            raise ValueError("Runtime changed since qualification: " + name)
    for name, digest in manifest["reports"].items():
        if sha(prefix / "evidence" / name) != digest:
            raise ValueError("Qualification report changed")
    return manifest


def run(prefix: Path, operation: str, target: str, output: Path, selector: str | None) -> int:
    manifest = verify(prefix)
    source = local_path(target)
    if not source.exists():
        raise ValueError("Target is missing")
    if operation not in OPS:
        raise ValueError("Operation is outside the static profile")
    if operation == "native-function":
        if not selector or selector.startswith("-") or any(c in selector for c in "\x00\n\r"):
            raise ValueError("A literal function selector is required")
    elif selector is not None:
        raise ValueError("Unexpected selector")
    if operation == "dependencies" and sys.platform != "darwin":
        raise ValueError("Dylib qualification is macOS-only")
    output.mkdir(mode=0o700, parents=False)
    argv = [manifest["node"], str(prefix / "source/scripts/rea.mjs"), OPS[operation], str(source)]
    if selector:
        argv.append(selector)
    if operation.startswith("native-"):
        argv += ["--provider", "ghidra"]
    argv.append("--json")
    code = execute(argv, output, environment(prefix, manifest.get("java_home")), output / "result")
    receipt = {"source_commit": COMMIT, "argv": argv, "exit_code": code,
               "stdout_sha256": sha(output / "result.stdout"), "stderr_sha256": sha(output / "result.stderr"),
               "status": "NEEDS_REVIEW" if code == 0 else "FAILED_OR_INCOMPLETE", "product_readiness": "NOT_ASSESSED"}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))
    return 0 if code == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("install", "verify", "config", "mcp", "run"):
        p = sub.add_parser(action)
        p.add_argument("prefix")
        if action == "install":
            p.add_argument("--apply", action="store_true")
        if action == "run":
            p.add_argument("operation", choices=sorted(OPS))
            p.add_argument("target")
            p.add_argument("--output", required=True)
            p.add_argument("--selector")
    args = parser.parse_args(argv)
    try:
        prefix = local_path(args.prefix)
        if args.action == "install":
            install(prefix, args.apply)
        elif args.action == "run":
            return run(prefix, args.operation, args.target, local_path(args.output), args.selector)
        else:
            manifest = verify(prefix)
            if args.action == "config":
                print(config_text(prefix))
            elif args.action == "mcp":
                # Client enabled_tools filters the exposed tools; this is not a server-side sandbox.
                os.execve(manifest["node"], [manifest["node"], str(prefix / "source/scripts/rea.mjs"), "mcp"], environment(prefix, manifest.get("java_home")))
            else:
                print(json.dumps({"status": "INTEGRITY_MATCH", "source_commit": COMMIT}))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
