"""Generate country and city statistics for web3.career job postings.

This utility consumes the CSV produced by ``web3_major_stats.py`` and
aggregates how often each location appears across the dataset.  The report is
split into two complementary perspectives:

* **City focus.** Highlights the most common metro areas (with a "Remote /
  Anywhere" bucket for fully distributed roles).
* **Country focus.** Shows the geographic distribution at the national level,
  including remote roles when they list specific country eligibility.

The script assumes that ``web3_major_stats.py`` has already been executed with
the refreshed schema that records structured location details extracted from
the JSON-LD metadata embedded in each posting.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
from collections import Counter
from datetime import datetime, timezone
import logging
import re
from typing import List, Mapping, Optional, Sequence


@dataclasses.dataclass(frozen=True)
class LocationRecord:
    url: str
    title: str
    company: str
    raw_locations: Sequence[str]
    city_labels: Sequence[str]
    region_labels: Sequence[str]
    country_labels: Sequence[str]
    applicant_requirements: Sequence[str]
    location_type: str
    is_remote: bool


@dataclasses.dataclass(frozen=True)
class AggregateRow:
    label: str
    jobs: int
    share: float


@dataclasses.dataclass(frozen=True)
class LocationAnalysis:
    total_jobs: int
    jobs_with_location: int
    remote_jobs: int
    location_type_counts: Mapping[str, int]
    city_rows: Sequence[AggregateRow]
    country_rows: Sequence[AggregateRow]


COUNTRY_ALIASES: Mapping[str, str] = {
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "uae": "United Arab Emirates",
    "u.a.e.": "United Arab Emirates",
    "gb": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "prc": "China",
    "hong kong sar": "Hong Kong",
    "viet nam": "Vietnam",
    "south korea": "South Korea",
    "republic of korea": "South Korea",
    "korea, republic of": "South Korea",
    "czech republic": "Czechia",
}

REMOTE_LABEL = "Remote / Anywhere"
MONTH_NAMES = {
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="majors.csv",
        help="Path to the majors/location CSV produced by web3_major_stats.py",
    )
    parser.add_argument(
        "--output",
        default="reports/location_statistics.md",
        help="Destination path for the Markdown summary",
    )
    parser.add_argument(
        "--top-cities",
        type=int,
        default=25,
        help="Number of cities to include in the ranking table",
    )
    parser.add_argument(
        "--top-countries",
        type=int,
        default=25,
        help="Number of countries to include in the ranking table",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def parse_semicolon_field(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def normalize_country(name: str) -> str:
    lowered = name.strip().lower()
    if not lowered:
        return ""
    if lowered in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lowered]
    return name.strip()


def load_records(path: str) -> List[LocationRecord]:
    records: List[LocationRecord] = []
    with open(path, newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            raw_locations = parse_semicolon_field(row.get("location_raw"))
            city_labels = parse_semicolon_field(row.get("location_cities"))
            region_labels = parse_semicolon_field(row.get("location_regions"))
            country_labels = [
                normalize_country(value)
                for value in parse_semicolon_field(row.get("location_countries"))
            ]
            applicant_requirements = [
                normalize_country(value)
                for value in parse_semicolon_field(
                    row.get("applicant_location_requirements")
                )
            ]
            if not country_labels:
                country_labels = infer_countries(raw_locations, applicant_requirements)
            if not city_labels:
                city_labels = infer_city_labels(raw_locations, country_labels)
            location_type = (row.get("location_type") or "").strip()
            is_remote = (row.get("location_is_remote") or "").strip().lower() == "true"
            if not is_remote:
                combined = " ".join(value.lower() for value in raw_locations)
                if "remote" in combined or "anywhere" in combined:
                    is_remote = True
            records.append(
                LocationRecord(
                    url=row.get("url", ""),
                    title=row.get("title", ""),
                    company=row.get("company", ""),
                    raw_locations=raw_locations,
                    city_labels=city_labels,
                    region_labels=region_labels,
                    country_labels=country_labels,
                    applicant_requirements=applicant_requirements,
                    location_type=location_type,
                    is_remote=is_remote,
                )
            )
    return records


def infer_city_labels(
    raw_locations: Sequence[str], country_hints: Sequence[str]
) -> List[str]:
    labels: List[str] = []
    placeholders = {"remote", "anywhere", "global"}
    normalized_countries = {normalize_country(name).lower() for name in country_hints}
    for raw in raw_locations:
        if not raw:
            continue
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        if not parts:
            continue
        parts_lower = [part.lower() for part in parts]
        if all(part in placeholders for part in parts_lower):
            continue
        filtered_parts = [part for part in parts if part.lower() not in placeholders]
        if not filtered_parts:
            continue
        if len(filtered_parts) >= 2:
            candidate = ", ".join(filtered_parts[:2])
        else:
            candidate = filtered_parts[0]
            if candidate.lower() in normalized_countries:
                continue
        candidate_lower = candidate.lower()
        if candidate_lower in placeholders or "anywhere" in candidate_lower:
            continue
        if candidate not in labels:
            labels.append(candidate)
    return labels


def infer_countries(
    raw_locations: Sequence[str], applicant_requirements: Sequence[str]
) -> List[str]:
    countries: List[str] = []
    for raw in raw_locations:
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        if parts:
            candidate = parts[-1]
            normalized = normalize_country(candidate)
            if not normalized:
                continue
            normalized_lower = normalized.lower()
            if normalized_lower in {"remote", "anywhere"}:
                continue
            if normalized_lower in MONTH_NAMES:
                continue
            if re.search(r"\d", normalized):
                continue
            if normalized not in countries:
                countries.append(normalized)
    if not countries:
        for requirement in applicant_requirements:
            normalized = normalize_country(requirement)
            if not normalized:
                continue
            normalized_lower = normalized.lower()
            if normalized_lower in {"remote", "anywhere"}:
                continue
            if normalized_lower in MONTH_NAMES:
                continue
            if re.search(r"\d", normalized):
                continue
            if normalized not in countries:
                countries.append(normalized)
    return countries


def aggregate_statistics(
    records: Sequence[LocationRecord],
    *,
    top_cities: int,
    top_countries: int,
) -> LocationAnalysis:
    total_jobs = len(records)
    remote_jobs = sum(1 for record in records if record.is_remote)
    jobs_with_location = sum(1 for record in records if record.raw_locations)
    location_type_counts: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    country_counter: Counter[str] = Counter()

    for record in records:
        location_type = record.location_type or "Unspecified"
        location_type_counts[location_type] += 1

        city_seen: set[str] = set()
        for label in record.city_labels:
            cleaned = label.strip()
            if not cleaned:
                continue
            normalized = cleaned
            normalized_lower = normalized.lower()
            if normalized_lower in {"remote", "anywhere"}:
                continue
            if "anywhere" in normalized_lower or "remote" in normalized_lower:
                continue
            if normalized_lower in MONTH_NAMES:
                continue
            if re.search(r"\d", normalized):
                continue
            if normalized not in city_seen:
                city_seen.add(normalized)
                city_counter[normalized] += 1
        if not city_seen and record.is_remote:
            city_counter[REMOTE_LABEL] += 1

        country_seen: set[str] = set()
        for value in record.country_labels:
            cleaned = value.strip()
            if not cleaned:
                continue
            normalized = normalize_country(cleaned)
            if normalized.lower() in {"remote", "anywhere"}:
                continue
            if normalized not in country_seen:
                country_seen.add(normalized)
                country_counter[normalized] += 1
        if not country_seen and record.is_remote:
            country_counter[REMOTE_LABEL] += 1

    city_rows = build_rows(city_counter, total_jobs, top_cities)
    country_rows = build_rows(country_counter, total_jobs, top_countries)

    return LocationAnalysis(
        total_jobs=total_jobs,
        jobs_with_location=jobs_with_location,
        remote_jobs=remote_jobs,
        location_type_counts=dict(sorted(location_type_counts.items())),
        city_rows=city_rows,
        country_rows=country_rows,
    )


def build_rows(counter: Mapping[str, int], total_jobs: int, limit: int) -> List[AggregateRow]:
    rows: List[AggregateRow] = []
    for label, jobs in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        share = (jobs / total_jobs * 100.0) if total_jobs else 0.0
        rows.append(AggregateRow(label=label, jobs=jobs, share=share))
    return rows


def render_markdown(result: LocationAnalysis) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    onsite_jobs = result.total_jobs - result.remote_jobs
    location_coverage = (
        result.jobs_with_location / result.total_jobs * 100.0
        if result.total_jobs
        else 0.0
    )
    lines = [
        "# Web3 Job Location Overview",
        "",
        f"- Generated: {timestamp}",
        f"- Total job postings analyzed: {result.total_jobs}",
        f"- Jobs with structured location data: {result.jobs_with_location} ({location_coverage:.1f}% of listings)",
        f"- Remote-friendly postings: {result.remote_jobs} ({(result.remote_jobs / result.total_jobs * 100.0 if result.total_jobs else 0.0):.1f}% of listings)",
        f"- On-site / hybrid postings: {onsite_jobs} ({(onsite_jobs / result.total_jobs * 100.0 if result.total_jobs else 0.0):.1f}% of listings)",
        "",
    ]

    if result.location_type_counts:
        lines.append("## Location type breakdown")
        lines.append("")
        lines.append("| Location type | Jobs | Share |")
        lines.append("| --- | ---: | ---: |")
        for label, jobs in sorted(
            result.location_type_counts.items(), key=lambda item: (-item[1], item[0])
        ):
            share = jobs / result.total_jobs * 100.0 if result.total_jobs else 0.0
            pretty_label = prettify_location_type(label)
            lines.append(f"| {pretty_label} | {jobs} | {share:.1f}% |")
        lines.append("")

    if result.city_rows:
        lines.append("## Top cities / metro areas")
        lines.append("")
        lines.append("| Rank | City | Jobs | Share of listings |")
        lines.append("| ---: | --- | ---: | ---: |")
        for idx, row in enumerate(result.city_rows, start=1):
            lines.append(f"| {idx} | {row.label} | {row.jobs} | {row.share:.1f}% |")
        lines.append("")

    if result.country_rows:
        lines.append("## Top countries")
        lines.append("")
        lines.append("| Rank | Country | Jobs | Share of listings |")
        lines.append("| ---: | --- | ---: | ---: |")
        for idx, row in enumerate(result.country_rows, start=1):
            lines.append(f"| {idx} | {row.label} | {row.jobs} | {row.share:.1f}% |")
        lines.append("")

    lines.append("### Notes")
    lines.append("")
    lines.append(
        "- Remote-first postings without a fixed city or country appear under "
        f"\"{REMOTE_LABEL}\" so they remain visible in the rankings."
    )
    lines.append(
        "- Country aliases (for example *USA* → *United States*) are normalized "
        "before aggregation; regional restrictions listed under applicant "
        "requirements are used when explicit job locations are missing."
    )
    lines.append("")

    return "\n".join(lines)


def prettify_location_type(location_type: str) -> str:
    normalized = location_type.strip()
    if not normalized:
        return "Unspecified"
    mapping = {
        "TELECOMMUTE": "Telecommute",
        "TITLE_INFERRED": "Title inferred",
    }
    return mapping.get(normalized, normalized.replace("_", " ").title())


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    records = load_records(args.input)
    logging.info("Loaded %d job records", len(records))
    if not records:
        raise SystemExit("No job records found; run web3_major_stats.py first.")
    analysis = aggregate_statistics(
        records,
        top_cities=args.top_cities,
        top_countries=args.top_countries,
    )
    report = render_markdown(analysis)
    with open(args.output, "w", encoding="utf-8") as fp:
        fp.write(report)
    logging.info("Wrote location report to %s", args.output)


if __name__ == "__main__":
    main()
