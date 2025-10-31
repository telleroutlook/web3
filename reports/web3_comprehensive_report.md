# Web3 Job Market Comprehensive Report

- Generated: 2025-10-31 00:09 UTC
- Job URLs discovered: 3,152 (listing crawl cached in `job_urls.txt`)
- Job descriptions processed: 3,144 (8 pages returned HTTP 403 and were excluded)
- Output dataset: `majors.csv` with major phrases, normalized categories, and structured locations per posting

## Executive Highlights
- Remote-friendly hiring dominates: 3,089 of 3,144 listings (98.3%) flag telecommute or "Anywhere" placement, with every top hiring hub showing at least 93% remote eligibility.
- Computer Science, Business/Management, and Finance remain the only majors cited in more than 20% of postings that mention a degree, underscoring the technical and commercial core of Web3 demand.
- Remote expectations span disciplines: even traditionally on-site functions (Legal, Marketing, Design) list remote support in ≥99% of roles.
- Tether, Binance, Bitpanda, Crypto.com, and Kraken lead the volume of postings explicitly referencing majors, signalling structured hiring requirements among the largest employers.

## Data Collection Summary
- Crawl pipeline attempted 3,152 job detail pages; 3,144 were successfully scraped.
- Eight URLs consistently returned HTTP 403 and are listed under "Unreachable job postings" below.
- The dataset powers both major phrase analysis (`analyze_majors.py`) and location aggregation (`analyze_locations.py`).

## Major Requirement Signals

### Coverage Snapshot
- Job postings analyzed: 3,144
- Jobs mentioning at least one major: 1,601 (50.92% of dataset)

### Top Raw Degree Phrases (jobs citing each phrase)
| Phrase | Jobs | Share of all jobs | Share of jobs w/ majors |
| --- | ---: | ---: | ---: |
| computer science | 774 | 24.62% | 48.34% |
| finance | 344 | 10.94% | 21.49% |
| business | 332 | 10.56% | 20.74% |
| accounting | 100 | 3.18% | 6.25% |
| engineering | 95 | 3.02% | 5.93% |
| marketing | 85 | 2.70% | 5.31% |
| computer information systems | 84 | 2.67% | 5.25% |
| design | 73 | 2.32% | 4.56% |
| business administration | 70 | 2.23% | 4.37% |
| legal | 33 | 1.05% | 2.06% |

### Normalized Major Groupings
| Normalized major | Jobs | Share of all jobs | Share of jobs w/ majors |
| --- | ---: | ---: | ---: |
| Computer Science | 776 | 24.68% | 48.47% |
| Business Administration & Management | 395 | 12.56% | 24.67% |
| Finance | 347 | 11.04% | 21.67% |
| Accounting | 103 | 3.28% | 6.43% |
| Engineering (General) | 101 | 3.21% | 6.31% |
| Marketing | 97 | 3.09% | 6.06% |
| Information Technology & Systems | 92 | 2.93% | 5.75% |
| Design & UX | 89 | 2.83% | 5.56% |
| Law | 56 | 1.78% | 3.50% |
| Communications & Media | 35 | 1.11% | 2.19% |

## Location Analytics

### Location Type Breakdown
| Location type | Jobs | Share |
| --- | ---: | ---: |
| Telecommute | 3,087 | 98.2% |
| Title inferred | 56 | 1.8% |
| Unspecified | 1 | 0.0% |

### Top Cities / Metro Areas
| Rank | City | Jobs | Share of listings |
| ---: | --- | ---: | ---: |
| 1 | Remote / Anywhere | 1,065 | 33.9% |
| 2 | New York, United States | 740 | 23.5% |
| 3 | New York, NY, United States | 235 | 7.5% |
| 4 | San Francisco, United States | 201 | 6.4% |
| 5 | Hong Kong, Hong Kong | 149 | 4.7% |
| 6 | Austin, United States | 148 | 4.7% |
| 7 | London, United Kingdom | 120 | 3.8% |
| 8 | Dallas, United States | 118 | 3.8% |
| 9 | Buenos Aires, Argentina | 116 | 3.7% |
| 10 | Dubai, United Arab Emirates | 91 | 2.9% |

### Top Countries
| Rank | Country | Jobs | Share of listings |
| ---: | --- | ---: | ---: |
| 1 | United States | 1,392 | 44.3% |
| 2 | Remote / Anywhere | 824 | 26.2% |
| 3 | Hong Kong | 149 | 4.7% |
| 4 | United Kingdom | 132 | 4.2% |
| 5 | Brazil | 130 | 4.1% |
| 6 | Canada | 123 | 3.9% |
| 7 | Argentina | 117 | 3.7% |
| 8 | United Arab Emirates | 97 | 3.1% |
| 9 | Italy | 70 | 2.2% |
| 10 | Singapore | 69 | 2.2% |

## Remote Intensity by Discipline
| Category | Jobs | Remote share |
| --- | ---: | ---: |
| Other / Unspecified | 2,417 | 97.8% |
| Computer Science / Software Engineering | 1,072 | 99.9% |
| Finance / Economics / Business | 913 | 99.9% |
| Data Science / Analytics | 321 | 99.7% |
| Marketing / Communications | 271 | 100.0% |
| Design / UX | 211 | 100.0% |
| Engineering (Non-CS) | 137 | 100.0% |
| Law / Legal | 63 | 100.0% |

*Role-level note:* job titles containing "Engineer", "Product", "Marketing", "Design", "Data", "Legal", "Finance", or "HR" each exhibit ≥98.9% remote availability, with Marketing, Legal, Finance, and HR postings reaching a full 100% remote share.

## Employer Demand Signals
| Company | Postings | % mentioning majors |
| --- | ---: | ---: |
| Tether | 265 | 85.7% |
| Unknown | 138 | 62.3% |
| Binance | 128 | 71.9% |
| Bitpanda | 94 | 72.3% |
| Crypto.com | 92 | 81.5% |
| Zscaler | 68 | 60.3% |
| Kraken | 65 | 70.8% |
| Coins.ph | 48 | 87.5% |
| Zinnia | 43 | 76.7% |
| Okx | 42 | 71.4% |

These organisations combine high posting volume with explicit major requirements, indicating formalised screening heuristics. The elevated "Unknown" bucket stems from postings where the employer name was missing or redacted in the source HTML.

## Unreachable Job Postings (HTTP 403)
- https://web3.career/legal-associate-crypto-echobase/124828
- https://web3.career/legal-compliance-officer-colombia-easygo/137625
- https://web3.career/legal-counsel-arbitrum-opco/138318
- https://web3.career/legal-counsel-bitpanda/138862
- https://web3.career/legal-counsel-coinflowlabs/138499
- https://web3.career/legal-counsel-eea-legal-malta-crypto-com/132846
- https://web3.career/legal-counsel-matterlabs/138885
- https://web3.career/legal-counsel-staff-pintu/132643

## How to Regenerate This Report
1. Run `python web3_major_stats.py --job-url-output job_urls.txt --workers 12 --sleep 0.05 --csv-output majors.csv` to refresh the dataset.
2. Produce statistical summaries:
   - `python analyze_majors.py --input majors.csv --output reports/major_phrase_statistics.md --top 25`
   - `python analyze_locations.py --input majors.csv --output reports/location_statistics.md --top-cities 25 --top-countries 25`
3. Execute a custom analysis script (e.g. `python3 scripts/summarize_insights.py`) or reuse the ad-hoc notebooks to update derived sections like remote intensity and employer demand.

