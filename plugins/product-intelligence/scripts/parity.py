#!/usr/bin/env python3
"""Feature parity score for replica-diff. Standard library only.

Reads the feature matrix that replica-recon wrote and you have been filling in
while you build, and tells you how much of the original your clone does, what
is missing, and in what order to build it.

    python3 parity.py replica/features.csv
    python3 parity.py replica/features.csv --visual diffs/*.json
    python3 parity.py replica/features.csv --markdown > replica/parity.md
    python3 parity.py replica/features.csv --fail-under 80

The CSV has these columns (extra columns are ignored):

    feature    what it does, in plain words ("reschedule a booking")
    area       the screen or flow it belongs to ("booking page")
    priority   must | should | could   (P0 | P1 | P2 also work)
    original   yes | no     does the original app have it
    clone      yes | partial | no | skip
    notes      anything. For skip, say why ("licensed content, out of scope")

Weights: must 3, should 2, could 1. yes counts 1, partial 0.5, no 0.
skip and rows where original is "no" (features you added) are left out of the
score and listed separately, so the number only ever measures parity.

With --visual, the layout scores from imgdiff.py --json are averaged and
reported next to the feature score, and the overall score is
80% features + 20% layout. Features are what users pay for.
"""

# Adapted from Jake Schincariol, Replica Skill (MIT), pinned in references/UPSTREAM.md.
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

WEIGHT = {"must": 3, "should": 2, "could": 1, "p0": 3, "p1": 2, "p2": 1}
CREDIT = {"yes": 1.0, "done": 1.0, "partial": 0.5, "no": 0.0, "": 0.0, "todo": 0.0}
PRIORITY_NAME = {3: "must", 2: "should", 1: "could"}


class MatrixError(Exception):
    pass


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise MatrixError("%s is empty" % path)
        fields = [f.strip().lower() for f in reader.fieldnames]
        for need in ("feature", "priority", "clone"):
            if need not in fields:
                raise MatrixError("%s has no '%s' column. Columns needed: "
                                  "feature, area, priority, original, clone, notes"
                                  % (path, need))
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not row.get("feature"):
                continue
            row["line"] = i
            rows.append(row)
    return rows


def score(rows):
    counted = []
    skipped = []
    extras = []
    problems = []
    for row in rows:
        original = row.get("original", "yes").lower() or "yes"
        clone = row.get("clone", "").lower()
        prio = row.get("priority", "").lower()
        if original in ("no", "n", "false"):
            extras.append(row)
            continue
        if clone == "skip":
            if prio in ("must", "p0"):
                problems.append("line %d: must-have skipped; requires an explicit scope decision" % row["line"])
            skipped.append(row)
            continue
        if prio not in WEIGHT:
            problems.append("line %d: priority '%s' is not must/should/could, counted as could"
                            % (row["line"], row.get("priority", "")))
        if clone not in CREDIT:
            problems.append("line %d: clone '%s' is not yes/partial/no/skip, counted as no"
                            % (row["line"], row.get("clone", "")))
        w = WEIGHT.get(prio, 1)
        c = CREDIT.get(clone, 0.0)
        counted.append(dict(row, weight=w, credit=c))

    total = sum(r["weight"] for r in counted)
    got = sum(r["weight"] * r["credit"] for r in counted)
    feature_score = 100.0 * got / total if total else 0.0

    areas = {}
    for r in counted:
        a = r.get("area") or "(no area)"
        t = areas.setdefault(a, [0.0, 0.0, 0])
        t[0] += r["weight"] * r["credit"]
        t[1] += r["weight"]
        t[2] += 1
    by_area = sorted(
        ({"area": a, "score": round(100.0 * g / t, 1) if t else 0.0, "features": n}
         for a, (g, t, n) in areas.items()),
        key=lambda d: d["score"])

    missing = [r for r in counted if r["credit"] < 1.0]
    missing.sort(key=lambda r: (-r["weight"], r["credit"], r.get("area", ""), r["feature"]))

    def brief(r):
        return {"feature": r["feature"], "area": r.get("area", ""),
                "priority": PRIORITY_NAME.get(r.get("weight", WEIGHT.get(
                    r.get("priority", "").lower(), 1)), "could"),
                "clone": r.get("clone", "") or "no", "notes": r.get("notes", "")}

    musts = [r for r in counted if r["weight"] == 3]
    return {
        "feature_score": round(feature_score, 1),
        "counted": len(counted),
        "must_have_done": sum(1 for r in musts if r["credit"] == 1.0),
        "must_have_total": len(musts),
        "by_area": by_area,
        "missing": [brief(r) for r in missing],
        "skipped": [brief(r) for r in skipped],
        "extras": [brief(r) for r in extras],
        "problems": problems,
    }


def visual_scores(paths):
    scores = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        if "score" not in data:
            raise MatrixError("%s is not imgdiff.py --json output" % p)
        name = data.get("files", {}).get("clone", p)
        scores.append({"file": name, "score": float(data["score"]),
                       "mode": data.get("mode", "layout")})
    return scores


def combine(result, visuals):
    if visuals:
        layout = sum(v["score"] for v in visuals) / len(visuals)
        result["visual"] = visuals
        result["layout_score"] = round(layout, 1)
        result["overall"] = round(0.8 * result["feature_score"] + 0.2 * layout, 1)
    else:
        result["overall"] = result["feature_score"]
    return result


def render(result, markdown=False):
    out = []
    h = "## " if markdown else ""
    out.append("%sParity: %.1f / 100" % (h, result["overall"]))
    out.append("")
    out.append("Evidence: %s" % result.get("evidence_mode", "DECLARED ONLY"))
    if result.get("unverified_features"):
        out.append("Unverified claimed features: %d" % len(result["unverified_features"]))
    if result.get("evidence_warnings"):
        out.extend("- %s" % warning for warning in result["evidence_warnings"])
    out.append("features %.1f  (%d counted, must-haves %d of %d done)" % (
        result["feature_score"], result["counted"], result["must_have_done"],
        result["must_have_total"]))
    if "layout_score" in result:
        out.append("layout   %.1f  (%d screens compared)" % (
            result["layout_score"], len(result["visual"])))
    if result["must_have_done"] < result["must_have_total"]:
        out.append("")
        out.append("Not shippable yet: %d must-have features are not done."
                   % (result["must_have_total"] - result["must_have_done"]))
    out.append("")
    out.append("%sBy area, weakest first" % h)
    for a in result["by_area"]:
        out.append("- %-28s %5.1f  (%d features)" % (a["area"], a["score"], a["features"]))
    out.append("")
    out.append("%sMissing, in build order" % h)
    if not result["missing"]:
        out.append("- nothing. Every counted feature is done.")
    for m in result["missing"]:
        note = ("  (%s)" % m["notes"]) if m["notes"] else ""
        out.append("- [%s] %s: %s, %s%s" % (m["priority"], m["area"] or "-",
                                             m["feature"], m["clone"], note))
    if result["skipped"]:
        out.append("")
        out.append("%sLeft out on purpose (not scored)" % h)
        for m in result["skipped"]:
            out.append("- %s: %s" % (m["feature"], m["notes"] or "no reason given, add one"))
    if result["extras"]:
        out.append("")
        out.append("%sYours, not in the original (not scored)" % h)
        for m in result["extras"]:
            out.append("- %s" % m["feature"])
    if result.get("visual"):
        out.append("")
        out.append("%sScreens" % h)
        for v in sorted(result["visual"], key=lambda d: d["score"]):
            out.append("- %-40s %5.1f" % (v["file"], v["score"]))
    if result["problems"]:
        out.append("")
        out.append("%sFix in the matrix" % h)
        for p in result["problems"]:
            out.append("- %s" % p)
    return "\n".join(out)


def verified_checks(path, subject_sha):
    """Check actual artifact digests for self-reported PASS results; no attestation."""
    p = Path(path).resolve()
    with p.open(encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict) or doc.get("subject_sha") != subject_sha:
        raise MatrixError("checks subject_sha does not match requested build/commit")
    entries = doc.get("checks")
    if not isinstance(entries, list):
        raise MatrixError("checks must be an array")
    passed, problems, seen = set(), [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise MatrixError("check entries must be objects")
        check_id = entry.get("id")
        if not isinstance(check_id, str) or not check_id:
            raise MatrixError("check id missing")
        if check_id in seen:
            raise MatrixError("duplicate check id: %s" % check_id)
        seen.add(check_id)
        if entry.get("status") != "PASS":
            continue
        rel = entry.get("artifact_path")
        digest = entry.get("sha256")
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            problems.append("%s: missing relative artifact_path or sha256" % check_id)
            continue
        target = (p.parent / rel).resolve()
        if not target.is_relative_to(p.parent) or not target.is_file() or target.stat().st_size > 20_000_000:
            problems.append("%s: artifact missing, outside evidence root, or oversized" % check_id)
            continue
        with target.open("rb") as fh:
            actual = hashlib.file_digest(fh, "sha256").hexdigest()
        if actual.lower() != digest.lower():
            problems.append("%s: artifact SHA-256 mismatch" % check_id)
            continue
        passed.add(check_id)
    return passed, problems


def apply_verified(rows, passed):
    """Only count claimed functionality with an artifact-linked PASS check."""
    changed, unverified = [], []
    for row in rows:
        row = dict(row)
        if row.get("clone", "").lower() in ("yes", "done", "partial"):
            check_id = row.get("check_id", "")
            if not check_id or check_id not in passed:
                unverified.append(row["feature"])
                row["notes"] = (row.get("notes", "") + " [unverified]").strip()
                row["clone"] = "no"
        changed.append(row)
    return changed, unverified


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("matrix", help="the feature matrix CSV")
    ap.add_argument("--visual", nargs="*", default=[],
                    help="imgdiff.py --json outputs to fold in")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--checks", help="offline JSON check records; must match actual artifact hashes")
    ap.add_argument("--subject-sha", help="exact build or commit identity matching checks JSON")
    ap.add_argument("--fail-under", type=float)
    args = ap.parse_args(argv)
    try:
        rows = load(args.matrix)
        if bool(args.checks) != bool(args.subject_sha):
            raise MatrixError("--checks and --subject-sha must be supplied together")
        if args.checks:
            passed, problems = verified_checks(args.checks, args.subject_sha)
            rows, unverified = apply_verified(rows, passed)
            result = combine(score(rows), visual_scores(args.visual))
            result["evidence_mode"] = "artifact-hash-backed self-reported PASS (not independently attested)"
            result["unverified_features"] = unverified
            result["evidence_warnings"] = problems
        else:
            result = combine(score(rows), visual_scores(args.visual))
            result["evidence_mode"] = "DECLARED ONLY; no test evidence checked"
    except (MatrixError, OSError, ValueError) as exc:
        print("parity: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result, markdown=args.markdown))
    if args.fail_under is not None and result["overall"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
