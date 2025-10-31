"""Scrape major requirements from web3.career job listings.

This script crawls the https://web3.career job board, downloads all job
postings, extracts the sentences that mention university degrees or majors,
and aggregates the requirements into high level categories.  The goal is to
understand which academic backgrounds are most frequently requested for Web3
roles.

The scraper is intentionally conservative: it starts by consuming the
``sitemap.xml`` feed to discover job detail pages and falls back to traversing
paginated listing pages when the sitemap is not available.  Each request uses a
simple ``urllib`` opener with a desktop browser user agent so that the script
works in minimal Python environments without third party dependencies.

Because job descriptions are free-form text, the major extraction relies on a
set of regular expressions as well as a small keyword taxonomy to map the free
text into coarse-grained categories.  The default mapping can be adjusted via
``CATEGORY_KEYWORDS`` if needed.

Example usage::

    python web3_major_stats.py --limit 200 --sleep 1.5

Running without ``--limit`` will visit every job detail page advertised in the
sitemap.  A CSV report with the per-job findings can be written with
``--csv-output``.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import logging
import re
import sys
import time
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from typing import Dict, Iterable, List, Optional, Sequence, Set
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://web3.career"
SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_jobs.xml",
]
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Mapping of category name to the keywords that should trigger it.
CATEGORY_KEYWORDS: Dict[str, Sequence[str]] = {
    "Computer Science / Software Engineering": (
        "computer science",
        "software engineering",
        "computer engineering",
        "computing",
        "information technology",
        "information systems",
        "informatics",
        "computer science or related",
        "cs",
        "electrical and computer engineering",
        "software development",
    ),
    "Engineering (Non-CS)": (
        "engineering",
        "electrical engineering",
        "mechanical engineering",
        "industrial engineering",
        "civil engineering",
        "chemical engineering",
        "materials science",
        "stem field",
    ),
    "Finance / Economics / Business": (
        "finance",
        "economics",
        "business",
        "commerce",
        "accounting",
        "mba",
        "management",
        "quantitative finance",
        "financial engineering",
    ),
    "Mathematics / Statistics": (
        "mathematics",
        "statistics",
        "math",
        "statistical",
        "applied math",
        "quantitative discipline",
        "quantitative field",
        "physics",
    ),
    "Data Science / Analytics": (
        "data science",
        "analytics",
        "machine learning",
        "artificial intelligence",
        "ai",
    ),
    "Design / UX": (
        "design",
        "ux",
        "user experience",
        "human computer interaction",
        "graphic design",
        "visual communication",
    ),
    "Marketing / Communications": (
        "marketing",
        "communications",
        "communication",
        "public relations",
        "journalism",
        "media",
    ),
    "Law / Legal": (
        "law",
        "legal",
        "juris doctor",
        "jd",
    ),
    "Sciences": (
        "physics",
        "chemistry",
        "biology",
        "biochemistry",
        "life sciences",
    ),
}

MAJOR_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(
        r"(?i)(?:degree|major|background|education|qualification)s?\s+(?:in|within)\s+([A-Za-z0-9&/.,\- ]+)"
    ),
    re.compile(
        r"(?i)(?:BA|BS|BSc|MA|MS|MSc|MBA|PhD|Doctorate|Bachelor's|Master's|Doctorate)\s+(?:degree\s+)?in\s+([A-Za-z0-9&/.,\- ]+)"
    ),
    re.compile(r"(?i)(?:B\.S\.|B\.A\.|M\.S\.|M\.A\.)\s+in\s+([A-Za-z0-9&/.,\- ]+)"),
    re.compile(r"(?i)(?:study|studies)\s+(?:in|of)\s+([A-Za-z0-9&/.,\- ]+)")
)

SCRIPT_STYLE_TAG = re.compile(r"(?is)<(script|style)[^>]*>.*?</\\1>")
TAG_RE = re.compile(r"(?s)<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
JSON_LD_RE = re.compile(
    r"<script[^>]*type=\"application/ld\+json\"[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


def _http_get(
    url: str,
    *,
    timeout: float = 30.0,
    retries: int = 3,
    backoff: float = 5.0,
) -> Optional[str]:
    """Fetch a URL and return the decoded body as UTF-8 text.

    The function sets a user agent so that the server treats the request as a
    regular browser visit.  Network errors are logged and result in ``None`` to
    make the caller resilient to transient issues.
    """

    req = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    for attempt in range(retries):
        try:
            with urlopen(req, timeout=timeout) as resp:
                encoding = resp.headers.get_content_charset() or "utf-8"
                body = resp.read().decode(encoding, errors="replace")
                logging.debug("Fetched %s (%d bytes)", url, len(body))
                return body
        except HTTPError as exc:  # pragma: no cover - network dependent
            if exc.code in {429, 500, 502, 503, 504} and attempt + 1 < retries:
                delay = backoff * (attempt + 1)
                logging.warning(
                    "HTTP error %s for %s; retrying in %.1fs", exc.code, url, delay
                )
                time.sleep(delay)
                continue
            logging.warning("HTTP error %s for %s", exc.code, url)
        except URLError as exc:  # pragma: no cover - network dependent
            logging.warning("Failed to fetch %s: %s", url, exc)
        break
    return None


def discover_job_links_from_sitemap() -> List[str]:
    """Return job detail URLs discovered in the sitemap feeds."""

    discovered: Set[str] = set()
    pending: List[str] = [urljoin(BASE_URL, path) for path in SITEMAP_PATHS]
    seen: Set[str] = set()

    while pending:
        sitemap_url = pending.pop()
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        body = _http_get(sitemap_url)
        if not body:
            continue
        # Capture all <loc> entries regardless of surrounding namespace.
        for loc in re.findall(r"<loc>(.*?)</loc>", body):
            loc = loc.strip()
            if not loc.startswith(BASE_URL):
                continue
            parsed = urlparse(loc)
            path = parsed.path
            if loc.endswith(".xml"):
                pending.append(loc)
                continue
            if re.search(r"/\d+$", path) or "job-" in path:
                discovered.add(loc)
    return sorted(discovered)


def discover_job_links_from_listing(
    max_pages: int = 200, *, workers: int = 8
) -> List[str]:
    """Fallback crawler that walks the paginated listing pages."""

    urls: Set[str] = set()
    page_numbers = list(range(1, max_pages + 1))
    batch_size = max(1, workers)

    for batch_start in range(0, len(page_numbers), batch_size):
        batch = page_numbers[batch_start : batch_start + batch_size]
        bodies: Dict[int, Optional[str]] = {}

        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            future_to_page = {
                executor.submit(
                    _http_get,
                    BASE_URL if page == 1 else f"{BASE_URL}/?page={page}",
                ): page
                for page in batch
            }
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    bodies[page] = future.result()
                except Exception:  # pragma: no cover - defensive logging
                    logging.exception("Failed to fetch listing page %s", page)
                    bodies[page] = None

        batch_new = 0
        for page in sorted(bodies):
            body = bodies[page]
            page_url = BASE_URL if page == 1 else f"{BASE_URL}/?page={page}"
            if not body:
                continue
            before = len(urls)
            for match in re.findall(r'href="(/[^"?#]+)"', body):
                if match.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif")):
                    continue
                full_url = urljoin(BASE_URL, match)
                parsed = urlparse(full_url)
                parts = [segment for segment in parsed.path.split("/") if segment]
                if len(parts) != 2:
                    continue
                if not parts[1].isdigit():
                    continue
                if "/companies" in full_url or "/salary" in full_url:
                    continue
                urls.add(full_url)
            added = len(urls) - before
            batch_new += added
            logging.info("Discovered %d potential job links from %s", len(urls), page_url)
        if batch_new == 0:
            logging.info(
                "No new job links found in listing pages %d-%d; stopping crawl",
                batch[0],
                batch[-1],
            )
            break
    return sorted(urls)


def html_to_text(html: str) -> str:
    """Convert HTML to readable plain text."""

    html = SCRIPT_STYLE_TAG.sub(" ", html)
    html = TAG_RE.sub(" ", html)
    html = unescape(html)
    text = WHITESPACE_RE.sub(" ", html)
    return text.strip()


def extract_major_phrases(text: str) -> List[str]:
    """Return raw major requirement phrases extracted from job text."""

    phrases: List[str] = []
    for pattern in MAJOR_PATTERNS:
        for match in pattern.findall(text):
            if isinstance(match, tuple):
                match = match[0]
            cleaned = clean_major_phrase(match)
            if cleaned:
                phrases.append(cleaned)
    return phrases


def clean_major_phrase(phrase: str) -> str:
    phrase = phrase.lower()
    phrase = phrase.split(";", 1)[0]
    phrase = phrase.split(".", 1)[0]
    phrase = phrase.split(",", 1)[0]
    phrase = phrase.replace("related field", "")
    phrase = phrase.replace("or equivalent", "")
    phrase = phrase.replace("or a related discipline", "")
    phrase = phrase.replace("or similar", "")
    phrase = phrase.replace("or related discipline", "")
    phrase = re.sub(r"[^a-z0-9&/ ]", " ", phrase)
    phrase = WHITESPACE_RE.sub(" ", phrase)
    return phrase.strip()


def categorize_phrase(phrase: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in phrase:
                return category
    # Some heuristics for general fallbacks.
    if "science" in phrase:
        return "Sciences"
    if "engineering" in phrase:
        return "Engineering (Non-CS)"
    if "design" in phrase or "ux" in phrase:
        return "Design / UX"
    if "marketing" in phrase or "communication" in phrase:
        return "Marketing / Communications"
    if "finance" in phrase or "economics" in phrase:
        return "Finance / Economics / Business"
    if "math" in phrase or "stat" in phrase:
        return "Mathematics / Statistics"
    if "data" in phrase or "analytics" in phrase:
        return "Data Science / Analytics"
    return "Other / Unspecified"


def _parse_jsonld_blocks(html: str) -> List[dict]:
    """Return JSON-LD dictionaries embedded in the page."""

    postings: List[dict] = []

    def handle_payload(payload: object) -> None:
        if isinstance(payload, list):
            for item in payload:
                handle_payload(item)
            return
        if not isinstance(payload, dict):
            return
        if payload.get("@type") == "JobPosting":
            postings.append(payload)

    for match in JSON_LD_RE.finditer(html):
        raw_json = match.group(1).strip()
        if not raw_json:
            continue
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            logging.debug("Failed to decode JSON-LD block")
            continue
        handle_payload(data)
    return postings


def _append_unique(container: List[str], value: Optional[str], *, skip_anywhere: bool = False) -> None:
    if not value:
        return
    candidate = WHITESPACE_RE.sub(" ", value).strip()
    if not candidate:
        return
    if skip_anywhere and candidate.lower() == "anywhere":
        return
    if candidate not in container:
        container.append(candidate)


def infer_location_from_title(title: str) -> Optional[str]:
    """Best-effort location extraction from the page title."""

    cleaned = WHITESPACE_RE.sub(" ", title).strip()
    if not cleaned:
        return None
    if re.search(r"\bremote\b", cleaned, re.IGNORECASE):
        return "Remote"
    if " in " in cleaned:
        candidate = cleaned.rsplit(" in ", 1)[1].strip(" -–—")
        if candidate:
            return candidate
    dash_match = re.search(r"[-–—]\s*([A-Za-z][A-Za-z0-9 .,/'&()-]+)$", cleaned)
    if dash_match:
        candidate = dash_match.group(1).strip()
        if candidate:
            return candidate
    trailing_match = re.search(r"([A-Za-z][A-Za-z0-9 .,/'&()-]+)$", cleaned)
    if trailing_match:
        candidate = trailing_match.group(1).strip()
        if candidate:
            return candidate
    return None


def extract_location_info(html: str, title: Optional[str] = None) -> JobLocation:
    """Extract structured location details from a job posting page."""

    location = JobLocation()
    postings = _parse_jsonld_blocks(html)

    def add_entry(
        raw: Optional[str],
        city: Optional[str],
        region: Optional[str],
        country: Optional[str],
        source: str,
    ) -> None:
        if not raw:
            return
        normalized_raw = WHITESPACE_RE.sub(" ", raw).strip()
        if not normalized_raw:
            return
        for existing in location.entries:
            if existing.raw == normalized_raw:
                return
        location.entries.append(
            LocationEntry(
                raw=normalized_raw,
                city=WHITESPACE_RE.sub(" ", city).strip() if city else None,
                region=WHITESPACE_RE.sub(" ", region).strip() if region else None,
                country=WHITESPACE_RE.sub(" ", country).strip() if country else None,
            )
        )
        location.sources.add(source)

    for posting in postings:
        loc_type = posting.get("jobLocationType")
        if loc_type and not location.location_type:
            location.location_type = loc_type
        if loc_type and "telecommute" in loc_type.lower():
            location.is_remote = True

        applicant_req = posting.get("applicantLocationRequirements")
        if isinstance(applicant_req, dict):
            applicant_req = [applicant_req]
        if isinstance(applicant_req, list):
            for req in applicant_req:
                if isinstance(req, dict):
                    name = req.get("name") or req.get("addressCountry")
                    _append_unique(location.applicant_requirements, name, skip_anywhere=False)
                    if name and name.strip().lower() == "anywhere":
                        location.is_remote = True
                elif isinstance(req, str):
                    _append_unique(location.applicant_requirements, req, skip_anywhere=False)
                    if req.strip().lower() == "anywhere":
                        location.is_remote = True

        job_location = posting.get("jobLocation")
        if isinstance(job_location, dict):
            job_location = [job_location]
        if isinstance(job_location, list):
            for item in job_location:
                if not isinstance(item, dict):
                    continue
                address = item.get("address")
                if isinstance(address, dict):
                    city = address.get("addressLocality")
                    region = address.get("addressRegion")
                    country = address.get("addressCountry")

                    placeholders = {"anywhere", "remote", "global"}

                    def sanitize(value: Optional[str]) -> Optional[str]:
                        if not value:
                            return None
                        cleaned = WHITESPACE_RE.sub(" ", value).strip()
                        if not cleaned:
                            return None
                        if cleaned.lower() in placeholders:
                            return None
                        return cleaned

                    city_clean = sanitize(city)
                    region_clean = sanitize(region)
                    country_clean = sanitize(country)

                    for candidate in (city, region, country):
                        if candidate and candidate.strip().lower() in placeholders:
                            location.is_remote = True

                    parts = [value for value in (city_clean, region_clean, country_clean) if value]
                    if parts:
                        add_entry(
                            ", ".join(parts),
                            city_clean,
                            region_clean,
                            country_clean,
                            source="jsonld",
                        )
                    else:
                        name = address.get("name")
                        if name:
                            add_entry(name, None, None, None, source="jsonld")
                else:
                    name = item.get("name") if isinstance(item.get("name"), str) else None
                    if name:
                        add_entry(name, None, None, None, source="jsonld")

    if not location.entries and title:
        inferred = infer_location_from_title(title)
        if inferred:
            add_entry(inferred, None, None, None, source="title")
            if inferred.lower() == "remote":
                location.is_remote = True
            if not location.location_type:
                location.location_type = "TITLE_INFERRED"

    for entry in location.entries:
        if entry.raw.lower() in {"remote", "anywhere"}:
            location.is_remote = True

    if not location.entries and location.is_remote:
        add_entry("Remote", None, None, None, source="derived")

    return location


@dataclasses.dataclass
class LocationEntry:
    raw: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None


@dataclasses.dataclass
class JobLocation:
    entries: List[LocationEntry] = dataclasses.field(default_factory=list)
    location_type: Optional[str] = None
    is_remote: bool = False
    applicant_requirements: List[str] = dataclasses.field(default_factory=list)
    sources: Set[str] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class JobMajorInfo:
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    raw_phrases: List[str] = dataclasses.field(default_factory=list)
    categories: Set[str] = dataclasses.field(default_factory=set)
    location: JobLocation = dataclasses.field(default_factory=JobLocation)


def extract_title_and_company(html: str) -> tuple[Optional[str], Optional[str]]:
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title: Optional[str] = None
    company: Optional[str] = None
    if title_match:
        title_text = unescape(title_match.group(1))
        # Titles often follow the pattern "Role at Company - web3.career"
        title_text = WHITESPACE_RE.sub(" ", title_text).strip()
        if "- web3.career" in title_text.lower():
            title_text = re.sub(r"-\s*web3\.career", "", title_text, flags=re.IGNORECASE)
        if " at " in title_text:
            role, comp = title_text.split(" at ", 1)
            title = role.strip()
            company = comp.strip()
        else:
            title = title_text
    # Fallback: look for meta tags or simple text patterns.
    if not company:
        comp_match = re.search(r"Company\s*[:|-]\s*([A-Za-z0-9 &]+)", html)
        if comp_match:
            company = comp_match.group(1).strip()
    return title, company


def fetch_job_information(
    urls: Sequence[str], *, sleep: float = 1.0, limit: Optional[int] = None, workers: int = 1
) -> List[JobMajorInfo]:
    queue: List[tuple[int, str]] = list(enumerate(urls, start=1))
    if limit is not None:
        queue = queue[:limit]
    total = len(queue)
    if total == 0:
        return []

    throttle_lock = threading.Lock()
    next_request_time = time.monotonic()

    def rate_limited_get(url: str) -> Optional[str]:
        nonlocal next_request_time
        if sleep > 0:
            with throttle_lock:
                now = time.monotonic()
                if now < next_request_time:
                    time.sleep(next_request_time - now)
                    now = time.monotonic()
                next_request_time = now + sleep
        return _http_get(url)

    def process_item(item: tuple[int, str]) -> Optional[tuple[int, JobMajorInfo]]:
        idx, url = item
        body = rate_limited_get(url)
        if not body:
            logging.warning("Skipping %s due to empty body", url)
            return None
        text = html_to_text(body)
        phrases = extract_major_phrases(text)
        categories = {categorize_phrase(phrase) for phrase in phrases}
        title, company = extract_title_and_company(body)
        location = extract_location_info(body, title=title)
        record = JobMajorInfo(
            url=url,
            title=title,
            company=company,
            raw_phrases=phrases,
            categories=categories,
            location=location,
        )
        return idx, record

    records: Dict[int, JobMajorInfo] = {}

    if workers <= 1:
        for item in queue:
            result = process_item(item)
            if result:
                idx, record = result
                records[idx] = record
                if idx % 25 == 0 or idx == total:
                    logging.info("Processed %d/%d job pages", idx, total)
        return [records[idx] for idx in sorted(records)]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_item, item): item[0] for item in queue}
        processed = 0
        for future in as_completed(futures):
            processed += 1
            try:
                result = future.result()
            except Exception:  # pragma: no cover - defensive logging
                logging.exception("Unhandled error while processing job page")
                continue
            if not result:
                continue
            idx, record = result
            records[idx] = record
            if processed % 25 == 0 or processed == total:
                logging.info("Processed %d/%d job pages", processed, total)

    return [records[idx] for idx in sorted(records)]


def aggregate_category_stats(records: Sequence[JobMajorInfo]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        for category in record.categories or {"Other / Unspecified"}:
            counter[category] += 1
    return dict(counter)


def print_report(records: Sequence[JobMajorInfo]) -> None:
    total_jobs = len(records)
    category_counts = aggregate_category_stats(records)
    sorted_categories = sorted(
        category_counts.items(), key=lambda item: item[1], reverse=True
    )

    print(f"Total jobs processed: {total_jobs}")
    print()
    print(f"{'Category':40} {'Count':>8} {'Share':>8}")
    print("-" * 60)
    for category, count in sorted_categories:
        share = (count / total_jobs * 100) if total_jobs else 0.0
        print(f"{category:40} {count:8d} {share:7.2f}%")
    print()

    print("Examples of extracted phrases:")
    sample = 0
    for record in records:
        if not record.raw_phrases:
            continue
        print(f"- {record.title or 'Unknown role'} ({record.url})")
        for phrase in record.raw_phrases[:3]:
            print(f"    • {phrase}")
        sample += 1
        if sample >= 5:
            break


def write_csv(records: Sequence[JobMajorInfo], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow(
            [
                "url",
                "title",
                "company",
                "categories",
                "raw_phrases",
                "location_raw",
                "location_cities",
                "location_regions",
                "location_countries",
                "location_type",
                "location_is_remote",
                "applicant_location_requirements",
                "location_sources",
            ]
        )
        for record in records:
            raw_locations = [entry.raw for entry in record.location.entries]
            city_labels: List[str] = []
            region_labels: List[str] = []
            country_labels: List[str] = []
            for entry in record.location.entries:
                if entry.city and entry.city.strip().lower() != "anywhere":
                    parts = [entry.city.strip()]
                    if entry.region and entry.region.strip().lower() != "anywhere":
                        parts.append(entry.region.strip())
                    if entry.country and entry.country.strip().lower() != "anywhere":
                        parts.append(entry.country.strip())
                    label = ", ".join(parts)
                    if label and label not in city_labels:
                        city_labels.append(label)
                if entry.region:
                    cleaned_region = entry.region.strip()
                    if cleaned_region and cleaned_region.lower() != "anywhere":
                        if cleaned_region not in region_labels:
                            region_labels.append(cleaned_region)
                if entry.country:
                    cleaned_country = entry.country.strip()
                    if cleaned_country and cleaned_country.lower() != "anywhere":
                        if cleaned_country not in country_labels:
                            country_labels.append(cleaned_country)
            writer.writerow(
                [
                    record.url,
                    record.title or "",
                    record.company or "",
                    "; ".join(sorted(record.categories)),
                    "; ".join(record.raw_phrases),
                    "; ".join(raw_locations),
                    "; ".join(city_labels),
                    "; ".join(region_labels),
                    "; ".join(country_labels),
                    record.location.location_type or "",
                    "true" if record.location.is_remote else "false",
                    "; ".join(record.location.applicant_requirements),
                    "; ".join(sorted(record.location.sources)),
                ]
            )
    logging.info("Wrote CSV output to %s", path)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most this many job detail pages",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Seconds to sleep between job detail requests",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent worker threads for fetching job details",
    )
    parser.add_argument(
        "--csv-output",
        help="Optional path to write a CSV export of the per-job findings",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--no-sitemap",
        action="store_true",
        help="Skip sitemap discovery and crawl listing pages directly",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum number of listing pages to crawl when sitemap is unavailable",
    )
    parser.add_argument(
        "--listing-workers",
        type=int,
        default=8,
        help="Number of concurrent requests when crawling listing pages",
    )
    parser.add_argument(
        "--job-url-input",
        help="Path to a file containing job detail URLs to process (one per line)",
    )
    parser.add_argument(
        "--job-url-output",
        help="Optional path to write the discovered job detail URLs",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    job_urls: List[str]
    if args.job_url_input:
        with open(args.job_url_input, "r", encoding="utf-8") as fp:
            job_urls = [line.strip() for line in fp if line.strip()]
    elif args.no_sitemap:
        job_urls = discover_job_links_from_listing(
            max_pages=args.max_pages, workers=max(1, args.listing_workers)
        )
    else:
        job_urls = discover_job_links_from_sitemap()
        if not job_urls:
            logging.warning("Falling back to listing crawl due to missing sitemap")
            job_urls = discover_job_links_from_listing(
                max_pages=args.max_pages, workers=max(1, args.listing_workers)
            )

    if not job_urls:
        logging.error("No job URLs discovered. Aborting.")
        return 1

    job_urls = sorted(dict.fromkeys(job_urls))
    if args.job_url_output:
        with open(args.job_url_output, "w", encoding="utf-8") as fp:
            fp.write("\n".join(job_urls))
        logging.info("Saved %d job URLs to %s", len(job_urls), args.job_url_output)

    logging.info("Discovered %d job URLs", len(job_urls))

    records = fetch_job_information(
        job_urls,
        sleep=args.sleep,
        limit=args.limit,
        workers=max(1, args.workers),
    )
    if not records:
        logging.error("No job descriptions processed successfully.")
        return 1

    print_report(records)

    if args.csv_output:
        write_csv(records, args.csv_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
