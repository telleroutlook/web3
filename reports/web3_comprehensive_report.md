# Web3 Job Market Comprehensive Report

- Generated: 2025-10-31 04:33 UTC
- Job URLs discovered: 7,500 (listing crawl up to page 500)
- Job descriptions processed: 7,477 (23 pages responded with HTTP 403 and are listed below)
- Output dataset: `majors.csv` with per-job major phrases, normalized categories, and structured location metadata

## Executive Highlights
- Remote-first hiring is effectively universal: 7,465 of 7,477 postings (99.8%) allow telecommute/"Anywhere" arrangements, and every major hiring hub stays above 99% remote share.
- Degree requirements surface more often at scale: 4,236 jobs (56.7%) reference at least one major, with Computer Science, Business/Management, and Finance each appearing in over 18% of the full corpus.
- Remote availability spans functions—legal, finance, operations, and marketing titles all register ≥99.8% remote share—indicating Web3 employers advertise globally across every business unit.
- Tether, Binance, Crypto.com, Coinbase, and Zscaler top the list of organisations repeatedly referencing majors, signalling structured screening criteria among high-volume hirers.

## Data Collection Summary
- The listing crawler now filters to canonical job detail paths (`/<slug>/<id>`), eliminating static asset links and “hire talent” landing pages from the URL pool.
- Crawl coverage: 500 listing pages traversed with throttled concurrency (sleep 0.2s between requests) to mitigate HTTP 429 responses.
- Remaining gaps are concentrated in legal roles that reply with HTTP 403 (likely gated behind regional restrictions or bot protection).

## Major Requirement Signals

### Coverage Snapshot
- Job postings analyzed: 7,477
- Jobs mentioning at least one major: 4,236 (56.7% of dataset)

### Top Raw Degree Phrases (jobs citing each phrase)
| Phrase | Jobs | Share of all jobs | Share of jobs w/ majors |
| --- | ---: | ---: | ---: |
| computer science | 2,024 | 27.07% | 47.78% |
| business | 1,061 | 14.19% | 25.05% |
| finance | 769 | 10.28% | 18.15% |
| engineering | 240 | 3.21% | 5.67% |
| marketing | 226 | 3.02% | 5.34% |
| accounting | 225 | 3.01% | 5.31% |
| computer information systems | 197 | 2.63% | 4.65% |
| design | 162 | 2.17% | 3.82% |
| business administration | 159 | 2.13% | 3.75% |
| legal | 96 | 1.28% | 2.27% |

### Normalized Major Groupings
| Normalized major | Jobs | Share of all jobs | Share of jobs w/ majors |
| --- | ---: | ---: | ---: |
| Computer Science | 2,030 | 27.15% | 47.92% |
| Business Administration & Management | 1,213 | 16.22% | 28.64% |
| Finance | 778 | 10.41% | 18.37% |
| Engineering (General) | 258 | 3.45% | 6.09% |
| Marketing | 248 | 3.32% | 5.85% |
| Accounting | 230 | 3.08% | 5.43% |
| Information Technology & Systems | 221 | 2.96% | 5.22% |
| Design & UX | 194 | 2.59% | 4.58% |
| Law | 167 | 2.23% | 3.94% |
| Statistics | 81 | 1.08% | 1.91% |

## Location Analytics

### Location Type Breakdown
| Location type | Jobs | Share |
| --- | ---: | ---: |
| Telecommute | 7,463 | 99.8% |
| Title inferred | 14 | 0.2% |

### Top Cities / Metro Areas
| Rank | City | Jobs | Share of listings |
| ---: | --- | ---: | ---: |
| 1 | Remote / Anywhere | 2,618 | 35.0% |
| 2 | New York, United States | 1,728 | 23.1% |
| 3 | New York, NY, United States | 478 | 6.4% |
| 4 | San Francisco, United States | 388 | 5.2% |
| 5 | Hong Kong, Hong Kong | 323 | 4.3% |
| 6 | London, United Kingdom | 321 | 4.3% |
| 7 | Dallas, United States | 276 | 3.7% |
| 8 | Buenos Aires, Argentina | 249 | 3.3% |
| 9 | Dubai, United Arab Emirates | 208 | 2.8% |
| 10 | Toronto, Canada | 207 | 2.8% |

### Top Countries
| Rank | Country | Jobs | Share of listings |
| ---: | --- | ---: | ---: |
| 1 | United States | 3,146 | 42.1% |
| 2 | Remote / Anywhere | 1,779 | 23.8% |
| 3 | United Kingdom | 347 | 4.6% |
| 4 | Canada | 329 | 4.4% |
| 5 | Hong Kong | 323 | 4.3% |
| 6 | Brazil | 283 | 3.8% |
| 7 | Argentina | 253 | 3.4% |
| 8 | United Arab Emirates | 230 | 3.1% |
| 9 | Belgium | 200 | 2.7% |
| 10 | Singapore | 170 | 2.3% |

## Remote Intensity by Discipline
| Category | Jobs | Remote share |
| --- | ---: | ---: |
| Other / Unspecified | 5,853 | 99.9% |
| Computer Science / Software Engineering | 2,604 | 100.0% |
| Finance / Economics / Business | 2,374 | 99.9% |
| Data Science / Analytics | 716 | 99.9% |
| Marketing / Communications | 528 | 99.8% |
| Design / UX | 443 | 100.0% |
| Engineering (Non-CS) | 361 | 100.0% |
| Law / Legal | 177 | 100.0% |

*Role-level note:* representative titles illustrate the same pattern—Engineers (2,112 of 2,114), Product roles (651 of 652), and all sampled Marketing, Design, Data, Legal, Finance, and Operations titles show ≥99.8% remote availability, with Support positions just behind at 99.4%.

## Employer Demand Signals
| Company | Postings | % mentioning majors |
| --- | ---: | ---: |
| Tether | 826 | 90.4% |
| Binance | 310 | 74.2% |
| Crypto.com | 233 | 77.3% |
| Coinbase | 202 | 67.8% |
| Zscaler | 191 | 69.1% |
| Bitpanda | 161 | 68.9% |
| Kraken | 160 | 76.9% |
| Zinnia | 123 | 73.2% |
| Okx | 117 | 75.2% |
| Coins.ph | 112 | 86.6% |

These organisations combine high posting volume with explicit major requirements, reinforcing the prevalence of formal education filters within top-tier Web3 employers.

## Unreachable Job Postings (HTTP 403)
https://web3.career/legal-admin-assistant-bcbgroup/103494
https://web3.career/legal-admin-menyala/104593
https://web3.career/legal-advisor-wallet/108194
https://web3.career/legal-associate-crypto-echobase/124828
https://web3.career/legal-compliance-counsel-foundrydigital/104245
https://web3.career/legal-compliance-officer-colombia-easygo/137625
https://web3.career/legal-counsel-arbitrum-opco/138318
https://web3.career/legal-counsel-bitpanda/138862
https://web3.career/legal-counsel-capital-markets-european-union-eu-crypto-com/106838
https://web3.career/legal-counsel-coinflowlabs/138499
https://web3.career/legal-counsel-driftprotocol/108197
https://web3.career/legal-counsel-eea-legal-malta-crypto-com/132846
https://web3.career/legal-counsel-gravity-team/104690
https://web3.career/legal-counsel-junior-senior-metawealth/105158
https://web3.career/legal-counsel-matterlabs/138885
https://web3.career/legal-counsel-staff-pintu/132643
https://web3.career/legal-intern-quicknode/104963
https://web3.career/legal-operations-manager-bloxstaking/92755
https://web3.career/legal-operations-manager-chainalysis/106693
https://web3.career/legal-ops-kiln/105976
https://web3.career/legal-ounsel-corporate-ommercial-wallet/107847
https://web3.career/legal-response-lead-global-okx/108319
https://web3.career/legal-response-manager-global-okx/108320

## How to Regenerate This Report
1. Refresh job URLs via the listing crawler (example: `python3 -c "from web3_major_stats import discover_job_links_from_listing; print(len(discover_job_links_from_listing(max_pages=500, workers=4)))"`).
2. Fetch job details with throttling: `python web3_major_stats.py --job-url-input job_urls_extended.txt --workers 6 --sleep 0.2 --csv-output majors.csv`.
3. Update downstream summaries:
   - `python analyze_majors.py --input majors.csv --output reports/major_phrase_statistics.md --top 25`
   - `python analyze_locations.py --input majors.csv --output reports/location_statistics.md --top-cities 25 --top-countries 25`
4. Re-run custom notebooks or scripts (see `reports/web3_comprehensive_report.md`) to refresh aggregate insights and regenerate this document.

