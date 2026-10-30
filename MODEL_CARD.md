# Model card: pawnlink-lgbm v4

PawnLink scores a URL from 0 to 1 for how likely it is to be malicious. Version 4 is the model in production since 30 October 2026. It catches 97.8% of malicious URLs in the held-out test set, but only 68% of phishing URLs reported live on that day, mostly because it misses phishing pages served over HTTPS.

## Model details

| Item | Value |
|-|-|
| Registry name | `pawnlink-lgbm`, version 4, alias `@champion` in MLflow |
| Algorithm | LightGBM binary classifier, 172 trees (early stopping on validation log loss) |
| Input | The URL string only. No page content, DNS, WHOIS or redirects |
| Features | 23 lexical features from `pawnlink.features.extract`, the same code in training and serving |
| Output | `score` between 0 and 1, and `is_phishing` when the score is at least 0.3844 |
| Threshold | 0.3844, the value with the best F1 on the validation set |
| Served at | Cloud Run service `pawnlink-api` in `us-central1` |

The features cover length and character mix (URL length, digit and special character shares, entropy), structure (path length, query parameters, subdomain count, IP address host, HTTPS) and the domain (TLD length, popular TLD, hyphen in the host, file extensions).

## Intended use

PawnLink is a fast first check. It answers in a few milliseconds without opening the page, which makes it useful for triage: putting a warning next to a link, choosing which URLs a slower scanner should visit first, or flagging links in a stream of email or chat messages.

It should not be the only reason to block a URL or to trust one. A low score means the URL looks like the legitimate URLs in the training data. It does not mean the page is safe.

## Training data

**LegitPhish** (Potpelwar, Kulkarni and Waghmare, 2025, Mendeley Data, version 2, [doi:10.17632/hx4m73v2sf.2](https://doi.org/10.17632/hx4m73v2sf.2), CC BY 4.0). After removing duplicate URLs it has 80,755 rows, of which 62.5% are malicious. When the same URL carried both labels, it was kept as malicious. The dataset's precomputed feature columns are not used, because several of them disagree with the URLs they belong to (see `reports/feature_comparison.md`).

The malicious URLs in this dataset are largely malware distribution URLs, and 92% of them use plain HTTP. In practice the label means "malicious URL", not only phishing pages.

**Legitimate URLs with paths.** Almost every legitimate URL in LegitPhish is a bare homepage, while most malicious URLs have a path. Version 3 learned that shortcut and flagged 72% of ordinary legitimate pages such as `github.com/login`. Version 4 adds 8,260 real legitimate URLs with paths:

1. The 1,000 most popular domains from the [Tranco list](https://tranco-list.eu/) `PYK6J` (29 October 2026), skipping any domain that appears among the malicious URLs.
2. Up to 15 HTML pages per domain from the [Common Crawl](https://commoncrawl.org/) index `CC-MAIN-2026-43`, found for 602 of those domains.

These URLs are split by domain, so no domain appears in more than one split.

| Split | Rows | Malicious |
|-|-:|-:|
| Train | 62,343 | 56.6% |
| Validation | 13,356 | 56.7% |
| Test (LegitPhish only, unchanged since v3) | 12,114 | 62.5% |
| Legit paths test (unseen domains) | 1,202 | 0% |

## Evaluation

Every candidate model is compared with the current champion on the same files. It is promoted only if all three rules hold: test AUC drops by at most 0.005, test recall drops by at most 0.01, and fewer legitimate URLs with paths are flagged.

| Metric | v3 | v4 |
|-|-:|-:|
| Test ROC AUC | 0.9873 | 0.9867 |
| Test precision | 0.971 | 0.972 |
| Test recall | 0.980 | 0.978 |
| Legit URLs with paths flagged (1,202 URLs, unseen domains) | 71.8% | 4.2% |

### Live check, 30 October 2026

The first run of the monthly job scored URLs that appeared after training.

| Set | URLs | Result |
|-|-:|-|
| [OpenPhish](https://openphish.com/) community feed, phishing active that day | 300 | 68.0% caught |
| ...of which HTTPS | 210 | 55.2% caught |
| ...of which HTTP | 90 | 97.8% caught |
| Legit URLs with paths from 150 new Tranco domains (ranks 1,001 to 10,000) | 232 | 2.6% flagged |

## Limitations

**HTTPS phishing is often missed.** In the training data 95% of legitimate URLs use HTTPS and only 8% of malicious ones do, so `has_https` is now the strongest feature. Modern phishing sites mostly use HTTPS, and the live check above shows the cost: almost half of them pass as legitimate.

**It only sees the URL.** Shortened links such as `bit.ly/...` get high scores whatever they point to. A malicious page on a trusted host (a hacked WordPress site, a file on a cloud drive) looks legitimate.

**Legitimate file downloads look suspicious.** URLs ending in `.exe` or `.zip` score high even on trusted hosts, for example a GitHub release asset (0.99) or a Python installer on python.org (0.98). The added legitimate data contains HTML pages only.

**The data ages.** Attackers change their URLs faster than a fixed dataset can follow. The monthly job measures this drift, and the numbers above should be read together with the latest row of `pawnlink.monthly_metrics`.

**Popularity bias.** The added legitimate URLs come from the most visited sites. Small legitimate sites with unusual URLs may be flagged more often than the 4.2% above suggests.

## Monitoring and updates

- **Live predictions:** every prediction from the API or a Pub/Sub message is logged as one JSON line and copied into BigQuery (`pawnlink.run_googleapis_com_stdout`, kept 90 days).
- **Dashboard:** Cloud Monitoring shows requests, latency, instances and predictions by verdict.
- **Monthly job:** on the 1st of each month it scores the OpenPhish feed and fresh legitimate URLs, saves the results to `pawnlink.batch_predictions` and `pawnlink.monthly_metrics`, and uploads a drift report to Cloud Storage.
- **New versions:** retrain, pass the promotion gate, export the champion to Cloud Storage, then bump `MODEL_VERSION` in the CI workflow. Reverting that change rolls back.

## Next version

- **Goal:** catch more HTTPS phishing, since that is where v4 misses the most.
- **Data:** the monthly job already saves about 300 labelled phishing URLs per month in `pawnlink.batch_predictions`.
- **Note:** URLs used to train v5 cannot be reused to evaluate it.
