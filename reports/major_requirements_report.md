# Web3.career Major Requirement Analysis

_Date generated: 2025-10-31 04:33 UTC_

## Data collection summary

- Job URLs discovered: 7,500 (listing crawl cached in `job_urls_extended.txt`)
- Job descriptions processed: 7,477 (23 pages returned HTTP 403 and could not be retrieved)
- Output dataset: `majors.csv` containing per-job major phrases, categories, and structured locations

### Unreachable job postings

The following job pages consistently returned HTTP 403 errors and were excluded from the analysis:

- https://web3.career/legal-admin-assistant-bcbgroup/103494
- https://web3.career/legal-admin-menyala/104593
- https://web3.career/legal-advisor-wallet/108194
- https://web3.career/legal-associate-crypto-echobase/124828
- https://web3.career/legal-compliance-counsel-foundrydigital/104245
- https://web3.career/legal-compliance-officer-colombia-easygo/137625
- https://web3.career/legal-counsel-arbitrum-opco/138318
- https://web3.career/legal-counsel-bitpanda/138862
- https://web3.career/legal-counsel-capital-markets-european-union-eu-crypto-com/106838
- https://web3.career/legal-counsel-coinflowlabs/138499
- https://web3.career/legal-counsel-driftprotocol/108197
- https://web3.career/legal-counsel-eea-legal-malta-crypto-com/132846
- https://web3.career/legal-counsel-gravity-team/104690
- https://web3.career/legal-counsel-junior-senior-metawealth/105158
- https://web3.career/legal-counsel-matterlabs/138885
- https://web3.career/legal-counsel-staff-pintu/132643
- https://web3.career/legal-intern-quicknode/104963
- https://web3.career/legal-operations-manager-bloxstaking/92755
- https://web3.career/legal-operations-manager-chainalysis/106693
- https://web3.career/legal-ops-kiln/105976
- https://web3.career/legal-ounsel-corporate-ommercial-wallet/107847
- https://web3.career/legal-response-lead-global-okx/108319
- https://web3.career/legal-response-manager-global-okx/108320

## Category distribution

| Category | Job count | Share |
|---|---:|---:|
| Other / Unspecified | 5,853 | 78.28% |
| Computer Science / Software Engineering | 2,604 | 34.83% |
| Finance / Economics / Business | 2,374 | 31.75% |
| Data Science / Analytics | 716 | 9.58% |
| Marketing / Communications | 528 | 7.06% |
| Design / UX | 443 | 5.92% |
| Engineering (Non-CS) | 361 | 4.83% |
| Law / Legal | 177 | 2.37% |
| Mathematics / Statistics | 56 | 0.75% |
| Sciences | 10 | 0.13% |

*Notes:*
- "Other / Unspecified" captures listings where no deterministic major keywords surfaced.
- Counts can exceed the total number of jobs because a posting may map to multiple categories.

## Most common phrases

Overall top 10 phrases extracted from job descriptions:

1. computer science (2,024 mentions)
2. business (1,061)
3. finance (769)
4. engineering (240)
5. marketing (226)
6. accounting (225)
7. computer information systems (197)
8. design (162)
9. business administration (159)
10. legal (96)

Category highlights:

- **Computer Science / Software Engineering** postings frequently cite computer science, computer information systems, and machine-learning-adjacent skillsets.
- **Finance / Economics / Business** emphasises finance, business administration, accounting, and digital asset literacy.
- **Data Science / Analytics** references quantisation, model optimisation, and analytics tooling in addition to core data science terminology.
- **Marketing / Communications** roles highlight cross-functional coordination, brand storytelling, and go-to-market experience.

These findings show that explicit degree requirements increase with the larger sample (56.7% vs. ~51% previously), while the relative dominance of computer science and business-aligned disciplines remains stable.

## Reference reports

- Phrase-level and normalized statistics: `reports/major_phrase_statistics.md`
- Geographic distribution summary: `reports/location_statistics.md`
- Combined insight report: `reports/web3_comprehensive_report.md`

