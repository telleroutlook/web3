# web3

A small utility for analyzing the university major requirements mentioned in job postings on [web3.career](https://web3.career/).

## Usage

The `web3_major_stats.py` script crawls job postings, extracts sentences that mention degrees/majors, and aggregates the requirements by high-level major categories.

### Quick start

```bash
# Discover job URLs (writes job_urls.txt) and process them immediately
python web3_major_stats.py \
  --job-url-output job_urls.txt \
  --workers 12 \
  --sleep 0.05 \
  --csv-output majors.csv
```

To rerun the analysis without crawling the listing pages again, pass the cached URL list:

```bash
python web3_major_stats.py --job-url-input job_urls.txt --workers 12 --sleep 0 --csv-output majors.csv
```

### Useful flags

- `--limit`: Restrict the number of job pages to process (handy for quick tests).
- `--sleep`: Minimum delay (seconds) enforced between consecutive requests.
- `--workers`: Number of worker threads for downloading job descriptions.
- `--csv-output`: Save a CSV file with the per-job findings.
- `--job-url-input`: Read job URLs from a file instead of crawling the site.
- `--job-url-output`: Persist the discovered job URLs to a file for reuse.
- `--no-sitemap`: Skip sitemap discovery and crawl listing pages directly.
- `--listing-workers`: Degree of concurrency when crawling listing pages.
- `--max-pages`: Limit the number of listing pages when not using the sitemap.

> **Note**
> Running the script requires internet access to `web3.career`. In restricted environments the network calls may fail.
