"""Generate a focused skill summary for Binance software engineering roles in the UK."""
from __future__ import annotations

import csv
import datetime as dt
import pathlib
import re
from collections import Counter, OrderedDict
from typing import Dict, Iterable, List, Sequence, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent
DATA_PATH = REPO_ROOT / "majors.csv"
OUTPUT_PATH = REPO_ROOT / "reports" / "binance_uk_software_engineering_skills.md"

UK_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"\bunited kingdom\b", re.IGNORECASE),
    re.compile(r"\bu\. ?k\.?(?!\w)", re.IGNORECASE),
    re.compile(r"\buk\b", re.IGNORECASE),
)

SkillPattern = Tuple[str, Sequence[re.Pattern[str]], str]

SKILL_PATTERNS: Sequence[SkillPattern] = (
    (
        "Information technology foundation",
        (re.compile(r"\binformation technology\b", re.IGNORECASE),),
        "Jobs emphasise formal IT training or comparable computing backgrounds.",
    ),
    (
        "Payments & financial-market expertise",
        (
            re.compile(r"\bfinancial market\b", re.IGNORECASE),
            re.compile(r"\bpayment", re.IGNORECASE),
        ),
        "Experience building for regulated payment rails and financial products is expected.",
    ),
    (
        "Business administration credentials",
        (
            re.compile(r"\bbusiness administration\b", re.IGNORECASE),
            re.compile(r"\bbusiness or a\b", re.IGNORECASE),
        ),
        "Binance values candidates who can pair technical delivery with business leadership training.",
    ),
    (
        "Cross-functional programme leadership",
        (
            re.compile(r"\bmatrixed organization\b", re.IGNORECASE),
            re.compile(r"\blead critical and transformative initiatives\b", re.IGNORECASE),
        ),
        "Ability to drive complex initiatives across distributed teams surfaces repeatedly.",
    ),
)


def _load_rows(path: pathlib.Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _binance_software_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    matched: List[Dict[str, str]] = []
    for row in rows:
        if row.get("company") != "Binance":
            continue
        if "Computer Science / Software Engineering" not in row.get("categories", ""):
            continue
        matched.append(row)
    return matched


def _targets_united_kingdom(row: Dict[str, str]) -> bool:
    fields = (
        row.get("location_countries", ""),
        row.get("location_cities", ""),
        row.get("location_regions", ""),
        row.get("location_raw", ""),
        row.get("applicant_location_requirements", ""),
    )
    for field in fields:
        if not field:
            continue
        lowered = field.lower()
        for pattern in UK_PATTERNS:
            if pattern.search(lowered):
                return True
    return False


def _collect_phrase_stats(rows: Sequence[Dict[str, str]]) -> Tuple[Counter[str], Dict[str, str]]:
    counts: Counter[str] = Counter()
    canonical: Dict[str, str] = {}
    for row in rows:
        seen_lower: set[str] = set()
        for raw in row["raw_phrases"].split(";"):
            cleaned = raw.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen_lower:
                continue
            seen_lower.add(key)
            counts[key] += 1
            canonical.setdefault(key, cleaned)
    return counts, canonical


def _summarise_skill_themes(rows: Sequence[Dict[str, str]]) -> OrderedDict[str, Tuple[int, float, str]]:
    totals = OrderedDict()
    total_rows = len(rows)
    for label, patterns, blurb in SKILL_PATTERNS:
        totals[label] = [0, blurb]  # type: ignore[list-item]
    for row in rows:
        text = row["raw_phrases"].lower()
        for label, patterns, blurb in SKILL_PATTERNS:
            if any(pattern.search(text) for pattern in patterns):
                totals[label][0] += 1  # type: ignore[index]
    ordered: OrderedDict[str, Tuple[int, float, str]] = OrderedDict()
    for label, value in totals.items():
        count, blurb = value  # type: ignore[misc]
        share = (count / total_rows * 100) if total_rows else 0.0
        ordered[label] = (count, share, blurb)
    return ordered


def _format_percentage(value: float) -> str:
    return f"{value:.0f}%" if value and value >= 1 else f"{value:.1f}%"


def generate_report() -> None:
    rows = _load_rows(DATA_PATH)
    binance_rows = _binance_software_rows(rows)
    filtered = [row for row in binance_rows if _targets_united_kingdom(row)]

    total = len(filtered)
    universe_total = len(binance_rows)
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = []
    lines.append("# Binance UK Software Engineering Skill Snapshot")
    lines.append("")
    if total == 0:
        lines.append("No Binance postings tagged as software engineering with United Kingdom locations were found in the current dataset.")
        lines.append("")
        lines.append("*Data refreshed:* " + generated)
    else:
        lines.append(
            f"*Data coverage: {total} posting{'s' if total != 1 else ''} sourced from `majors.csv` (generated via `web3_major_stats.py`). Updated {generated}.*"
        )
        lines.append("")

        lines.append("## Location coverage check")
        lines.append("")
        lines.append(
            f"- Binance software-engineering postings analysed globally: {universe_total}."
        )
        lines.append(
            "- United Kingdom matches after scanning all location fields (countries, cities, regions, raw text, applicant requirements) and UK synonyms: "
            f"{total}."
        )
        lines.append("")

        country_counts: Counter[str] = Counter()
        for row in binance_rows:
            tokens = [
                token.strip()
                for token in row.get("location_countries", "").split(";")
                if token.strip()
            ]
            if tokens:
                country_counts.update(tokens)
            else:
                country_counts["(unspecified)"] += 1

        if country_counts:
            lines.append("### Global country footprint for Binance software-engineering roles")
            lines.append("")
            lines.append("| Country token | Postings mentioning | Share of Binance sample |")
            lines.append("| --- | ---: | ---: |")
            top_countries = country_counts.most_common(10)
            if "United Kingdom" in country_counts and not any(
                country == "United Kingdom" for country, _ in top_countries
            ):
                top_countries.append(("United Kingdom", country_counts["United Kingdom"]))
            for country, count in top_countries:
                share = count / universe_total * 100 if universe_total else 0.0
                lines.append(
                    f"| {country} | {count} | {_format_percentage(share)} |"
                )
            lines.append("")

        remote_count = sum(1 for row in filtered if row["location_is_remote"].strip().lower() == "true")
        city_tokens = []
        for row in filtered:
            for token in row["location_cities"].split(";"):
                token = token.strip()
                if token:
                    city_tokens.append(token)
        unique_cities = sorted(set(city_tokens))
        titles = [row["title"] for row in filtered]

        phrase_counts, canonical = _collect_phrase_stats(filtered)
        top_phrases = sorted(
            (
                (canonical[key], count, count / total * 100)
                for key, count in phrase_counts.items()
            ),
            key=lambda item: (-item[1], item[0].lower()),
        )[:10]

        skill_themes = _summarise_skill_themes(filtered)

        lines.append("## Posting snapshot")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Postings captured | {total} |")
        lines.append(f"| Remote-friendly roles | {remote_count} ({_format_percentage(remote_count / total * 100)}) |")
        lines.append(
            "| Representative locations | " + (", ".join(unique_cities) if unique_cities else "(not specified)") + " |"
        )
        lines.append("| Sample titles | " + "; ".join(titles) + " |")
        lines.append("")

        lines.append("## Skill themes surfaced")
        lines.append("")
        lines.append("| Theme | Postings mentioning | Share of sample | Interpretation |")
        lines.append("| --- | --- | --- | --- |")
        for label, (count, share, blurb) in skill_themes.items():
            share_text = _format_percentage(share)
            lines.append(f"| {label} | {count} | {share_text} | {blurb} |")
        lines.append("")

        if top_phrases:
            lines.append("## Raw requirement phrases")
            lines.append("")
            lines.append("| Phrase excerpt | Postings mentioning | Share of sample |")
            lines.append("| --- | --- | --- |")
            for phrase, count, share in top_phrases:
                lines.append(f"| {phrase} | {count} | {_format_percentage(share)} |")
            lines.append("")

        lines.append("## What this means for students")
        lines.append("")
        lines.append(
            "- Focus on **information-technology fundamentals**—the lone UK posting still requests a clear computing background despite its programme-management framing."
        )
        lines.append(
            "- Build **payments and financial-services literacy** so you can articulate how engineering decisions support regulated money-movement products."
        )
        lines.append(
            "- Strengthen **business leadership and cross-functional delivery skills** (e.g., managing matrixed stakeholders, leading critical initiatives) to stand out in lean regional teams."
        )
        lines.append("")

        lines.append("## Methodology")
        lines.append("")
        lines.append(
            "- Filtered `majors.csv` for records where `company == \"Binance\"`, `categories` contained \"Computer Science / Software Engineering\", and any of the location fields mentioned the United Kingdom (matching `United Kingdom`, `UK`, or `U.K.` case-insensitively)."
        )
        lines.append("- Deduplicated requirement phrases per posting before counting to prevent multi-line repetitions from inflating totals.")
        lines.append("- Skill themes were matched via targeted keyword patterns tailored to payments-focused engineering leadership roles.")
        lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate_report()
