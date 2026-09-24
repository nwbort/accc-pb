# accc-pb
Every 10 minutes a GitHub Action (`.github/workflows/accc-public-benefit-monitor.yml`)
checks the [ACCC acquisitions register filtered to the public benefit phase](https://www.accc.gov.au/public-registers/acquisitions-and-mergers-registers/acquisitions-register?f%5B0%5D=stage%3Apublic_benefit_phase).
If any items are listed, it sends a single ntfy notification to
[ntfy.sh/accc-pb-21d918be437e](https://ntfy.sh/accc-pb-21d918be437e) and commits a
`.ntfy-sent` marker so it never notifies again. Delete `.ntfy-sent` to re-arm it.
