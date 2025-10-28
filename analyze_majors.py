"""Generate structured major frequency statistics from ``majors.csv``.

This helper reads the CSV export produced by ``web3_major_stats.py`` and
produces a Markdown report with two complementary looks at the data:

* **Step 1 – Raw phrase frequency.** Counts how many unique job postings
  mention each exact major phrase (after light cleanup) so it is easy to see
  the original wording employers used.
* **Step 2 – Normalized major groupings.** Collapses similar phrases into a
  curated set of major buckets (for example, *"Computer Science"*,
  *"Information Technology & Systems"*, *"Finance"*) so that related phrasings
  are aggregated together.

Only phrases that contain degree-relevant keywords are considered.  The
normalization heuristics intentionally favor precision over recall so the
resulting statistics focus on genuine academic disciplines rather than generic
skill requirements that slipped through during scraping.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
from collections import Counter
from datetime import datetime, timezone
import logging
import re
from typing import Dict, List, Mapping, Optional, Sequence, Set


@dataclasses.dataclass(frozen=True)
class JobRecord:
    url: str
    title: str
    company: str
    phrases: Sequence[str]


@dataclasses.dataclass
class FrequencyEntry:
    label: str
    jobs: int
    share_all: float
    share_major: float


@dataclasses.dataclass
class AnalysisResult:
    total_jobs: int
    jobs_with_major: int
    raw_phrase_frequencies: Sequence[FrequencyEntry]
    normalized_frequencies: Sequence[FrequencyEntry]


RAW_PHRASE_EXCLUDE_PATTERN = re.compile(r"\d")
RAW_PHRASE_MIN_KEYWORD_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(
        r"\b(accounting|analytics|artificial intelligence|biology|business|chemistry|commerce|communication|communications|computer|data|design|econom|engineering|finance|informatics|law|legal|marketing|mathematics|math|physics|political science|psychology|science|statistics|supply chain|systems|technology|ux)\b",
        re.IGNORECASE,
    ),
)


def _compile_patterns(mapping: Mapping[str, Sequence[str]]) -> Dict[str, Sequence[re.Pattern[str]]]:
    compiled: Dict[str, List[re.Pattern[str]]] = {}
    for label, patterns in mapping.items():
        compiled[label] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    return compiled


NORMALIZED_MAJOR_PATTERNS: Mapping[str, Sequence[str]] = {
    "Computer Science": (r"\bcomputer science\b", r"\binformatics\b", r"\bcs\b"),
    "Software Engineering": (r"\bsoftware engineering\b",),
    "Information Technology & Systems": (
        r"\bcomputer information systems\b",
        r"\bmanagement information systems\b",
        r"\binformation systems\b",
        r"\binformation technology\b",
        r"\bit management\b",
    ),
    "Computer Engineering": (r"\bcomputer engineering\b",),
    "Electrical Engineering": (r"\belectrical engineering\b",),
    "Mechanical Engineering": (r"\bmechanical engineering\b",),
    "Industrial Engineering": (r"\bindustrial engineering\b",),
    "Chemical Engineering": (r"\bchemical engineering\b",),
    "Civil Engineering": (r"\bcivil engineering\b",),
    "Engineering (General)": (r"\bengineering\b",),
    "Data Science & Machine Learning": (
        r"\bdata science\b",
        r"\bdata analytics\b",
        r"\bdata analysis\b",
        r"\bmachine learning\b",
        r"\bartificial intelligence\b",
        r"\bai\b",
    ),
    "Mathematics": (r"\bmathematics\b", r"\bmath\b", r"\bapplied math\b"),
    "Statistics": (r"\bstatistics\b", r"\bstatistical\b"),
    "Physics": (r"\bphysics\b",),
    "Chemistry": (r"\bchemistry\b",),
    "Biology & Life Sciences": (
        r"\bbiology\b",
        r"\bbiological sciences\b",
        r"\bbiochemistry\b",
        r"\blife sciences\b",
        r"\bbiomedical\b",
    ),
    "Finance": (r"\bfinance\b", r"\bfinancial engineering\b", r"\bquantitative finance\b"),
    "Economics": (r"\beconomics\b", r"\beconomics?\b"),
    "Business Administration & Management": (
        r"\bbusiness administration\b",
        r"\bbusiness management\b",
        r"\bbusiness\b",
        r"\bmba\b",
        r"\bmanagement\b",
        r"\bcommerce\b",
    ),
    "Accounting": (r"\baccounting\b", r"\bchartered accountant\b"),
    "Marketing": (r"\bmarketing\b",),
    "Communications & Media": (
        r"\bcommunications\b",
        r"\bcommunication\b",
        r"\bjournalism\b",
        r"\bmedia\b",
        r"\bpublic relations\b",
    ),
    "Design & UX": (
        r"\bdesign\b",
        r"\bgraphic design\b",
        r"\bux\b",
        r"\buser experience\b",
        r"\bui design\b",
        r"\binteraction design\b",
        r"\bhuman computer interaction\b",
    ),
    "Law": (r"\blaw\b", r"\blegal\b", r"\bjuris doctor\b", r"\bjd\b"),
    "Political Science & International Relations": (
        r"\bpolitical science\b",
        r"\binternational relations\b",
        r"\binternational affairs\b",
    ),
    "Psychology": (r"\bpsychology\b",),
    "Human Resources": (r"\bhuman resources\b", r"\bhr management\b"),
    "Supply Chain & Operations": (
        r"\bsupply chain\b",
        r"\blogistics\b",
        r"\boperations research\b",
        r"\boperations management\b",
    ),
}


NORMALIZED_PATTERNS = _compile_patterns(NORMALIZED_MAJOR_PATTERNS)
SPECIFIC_ENGINEERING_LABELS = {
    "Software Engineering",
    "Computer Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Industrial Engineering",
    "Chemical Engineering",
    "Civil Engineering",
}


def load_records(path: str) -> List[JobRecord]:
    records: List[JobRecord] = []
    with open(path, newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            raw = row.get("raw_phrases") or ""
            phrases = [
                clean_raw_phrase(part)
                for part in raw.split(";")
                if part.strip()
            ]
            phrases = [phrase for phrase in phrases if phrase]
            records.append(
                JobRecord(
                    url=row.get("url", ""),
                    title=row.get("title", ""),
                    company=row.get("company", ""),
                    phrases=phrases,
                )
            )
    return records


def clean_raw_phrase(phrase: str) -> str:
    phrase = phrase.strip()
    phrase = re.sub(r"^[•\-–—:\s]+", "", phrase)
    phrase = re.sub(r"\s+", " ", phrase)
    phrase = re.sub(r"\s*[;,:-]\s*$", "", phrase)
    phrase = re.sub(r"\bwith\b\s+\d.*", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\(.*?\)", "", phrase)
    phrase = phrase.strip()
    if not phrase:
        return ""
    phrase = re.sub(r"^the\s+", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\b(or|and|with|for|in|of|to)\b\s*$",
        "",
        phrase,
        flags=re.IGNORECASE,
    ).strip()
    phrase = re.sub(
        r"\b(technical|related|relevant)\s+(discipline|field|fields)\b",
        "",
        phrase,
        flags=re.IGNORECASE,
    ).strip()
    if len(phrase.split()) > 6:
        return ""
    if RAW_PHRASE_EXCLUDE_PATTERN.search(phrase):
        # Drop phrases that still contain standalone digits (likely noise like
        # "with 5 years" or salary references).
        return ""
    lower = phrase.lower()
    if re.search(
        r"\b(experience|experiences|knowledge|skills|understanding|required|solutions|development|willingness|candidate|candidates|keen|intuition|considered|past)\b",
        lower,
    ):
        return ""
    if re.search(r"\b(love|passion|enthusiasm|beyond|unicorns|ecosystem|industry|realm)\b", lower):
        return ""
    if "what we offer" in lower:
        return ""
    parts = [p.strip() for p in re.split(r"\b(?:or|and|/|,)\b", phrase) if p.strip()]
    if len(parts) > 1:
        for part in parts:
            if any(pattern.search(part) for pattern in RAW_PHRASE_MIN_KEYWORD_PATTERNS):
                phrase = part
                lower = phrase.lower()
                break
    phrase = re.sub(r"\b(or|and)\b\s*$", "", phrase, flags=re.IGNORECASE).strip()
    lower = phrase.lower()
    if lower.endswith(" finance") and lower != "finance":
        phrase = "finance"
        lower = "finance"
    if lower.endswith(" business") and lower != "business":
        phrase = "business"
        lower = "business"
    if not any(pattern.search(phrase) for pattern in RAW_PHRASE_MIN_KEYWORD_PATTERNS):
        return ""
    if "crypto" in lower or "web3" in lower or "blockchain" in lower:
        return ""
    return phrase


def match_normalized_labels(phrase: str) -> Set[str]:
    matches: Set[str] = set()
    for label, regexes in NORMALIZED_PATTERNS.items():
        if any(regex.search(phrase) for regex in regexes):
            matches.add(label)

    if "Engineering (General)" in matches:
        if matches & SPECIFIC_ENGINEERING_LABELS:
            matches.discard("Engineering (General)")
    return matches


def analyze(records: Sequence[JobRecord]) -> AnalysisResult:
    total_jobs = len(records)
    phrase_counter: Counter[str] = Counter()
    label_counter: Counter[str] = Counter()
    jobs_with_major = 0

    for record in records:
        seen_phrase_keys: Set[str] = set()
        seen_labels: Set[str] = set()
        has_major = False

        for phrase in record.phrases:
            if not phrase:
                continue
            normalized_phrase_key = phrase.lower()
            labels = match_normalized_labels(phrase)
            if not labels:
                continue
            has_major = True
            if normalized_phrase_key not in seen_phrase_keys:
                phrase_counter[phrase] += 1
                seen_phrase_keys.add(normalized_phrase_key)
            for label in labels:
                if label not in seen_labels:
                    label_counter[label] += 1
            seen_labels.update(labels)

        if has_major:
            jobs_with_major += 1

    raw_freqs = _build_frequency_entries(phrase_counter, total_jobs, jobs_with_major)
    normalized_freqs = _build_frequency_entries(label_counter, total_jobs, jobs_with_major)

    return AnalysisResult(
        total_jobs=total_jobs,
        jobs_with_major=jobs_with_major,
        raw_phrase_frequencies=raw_freqs,
        normalized_frequencies=normalized_freqs,
    )


def _build_frequency_entries(
    counter: Counter[str],
    total_jobs: int,
    jobs_with_major: int,
) -> List[FrequencyEntry]:
    entries: List[FrequencyEntry] = []
    for label, jobs in counter.most_common():
        share_all = (jobs / total_jobs * 100) if total_jobs else 0.0
        share_major = (jobs / jobs_with_major * 100) if jobs_with_major else 0.0
        entries.append(
            FrequencyEntry(
                label=label,
                jobs=jobs,
                share_all=share_all,
                share_major=share_major,
            )
        )
    return entries


def render_markdown(result: AnalysisResult, top_n: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []
    lines.append("# Major requirement frequency analysis")
    lines.append("")
    lines.append(f"_Generated: {timestamp}_")
    lines.append("")
    lines.append("## Dataset overview")
    lines.append("")
    lines.append(f"- Job postings analyzed: {result.total_jobs}")
    lines.append(
        f"- Jobs mentioning at least one major: {result.jobs_with_major} "
        f"({result.jobs_with_major / result.total_jobs * 100:.2f}% of dataset)"
    )
    lines.append("")
    lines.append("## Step 1 · Raw phrase frequency")
    lines.append("")
    lines.append(
        "The table below keeps the original phrasing from job descriptions, so it "
        "captures how employers word their degree requirements."
    )
    lines.append("")
    lines.append("| Phrase | Jobs | Share of all jobs | Share of jobs w/ majors |")
    lines.append("|---|---:|---:|---:|")
    for entry in result.raw_phrase_frequencies[:top_n]:
        lines.append(
            f"| {entry.label} | {entry.jobs} | {entry.share_all:.2f}% | "
            f"{entry.share_major:.2f}% |"
        )

    lines.append("")
    lines.append("## Step 2 · Normalized major groupings")
    lines.append("")
    lines.append(
        "Here the phrases are mapped to a curated list of academic disciplines so "
        "that similar descriptions are consolidated."
    )
    lines.append("")
    lines.append("| Normalized major | Jobs | Share of all jobs | Share of jobs w/ majors |")
    lines.append("|---|---:|---:|---:|")
    for entry in result.normalized_frequencies[:top_n]:
        lines.append(
            f"| {entry.label} | {entry.jobs} | {entry.share_all:.2f}% | "
            f"{entry.share_major:.2f}% |"
        )

    lines.append("")
    lines.append("## Methodology notes")
    lines.append("")
    lines.append(
        "- Only phrases containing degree-relevant keywords (e.g. *computer*, *engineering*, *business*, *law*) are counted."
    )
    lines.append(
        "- Numeric fragments that stem from experience requirements (such as *\"with 5 years\"*) are filtered out to reduce noise."
    )
    lines.append(
        "- The normalized mapping prioritizes precision, so highly specific majors may not appear if they were mentioned only once."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="majors.csv",
        help="Path to the CSV file produced by web3_major_stats.py",
    )
    parser.add_argument(
        "--output",
        default="reports/major_phrase_statistics.md",
        help="Destination Markdown file for the report",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of rows to show in each frequency table",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    records = load_records(args.input)
    if not records:
        logging.error("No rows found in %s", args.input)
        return 1

    result = analyze(records)
    logging.info(
        "Analyzed %d job postings (%d mention majors)",
        result.total_jobs,
        result.jobs_with_major,
    )

    markdown = render_markdown(result, args.top)
    with open(args.output, "w", encoding="utf-8") as fp:
        fp.write(markdown)
    logging.info("Wrote report to %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
