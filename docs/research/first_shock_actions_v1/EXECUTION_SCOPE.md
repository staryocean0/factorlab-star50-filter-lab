# Owner-authorized Actions fallback, 2026-09-07

User confirmed the repository is now public and explicitly allowed Actions if direct access remained unavailable. GitHub API confirms private=false; this conversation's runtime still fails DNS resolution for raw.githubusercontent.com, on both text and authorized Parquet URLs.

This independent execution branch is based on b725544ff8fef9688877c6c7e1fd4d19081ea75c. The new workflow runs the exact frozen code commit with only ten authorized 2021-2025 minute partitions checked out. No 2026, no other markets, no strategy, no new threshold selection. The public setting supersedes the older storage-visibility instruction, not the data/research/production boundaries. Historical contracts and manifests are not changed.

Only on this isolated branch, legacy ci.yml excludes its push trigger to prevent unrelated old strategy validation. Existing steps and pull-request behavior are preserved; no branch protection is changed, no check is forged. This branch is not intended to merge into main. The dedicated workflow performs its own code/hash/data checks and new tests. No manual or scheduled background research is configured.

Workflow completion is not scientific acceptance. Results and actual commands/exit status must be reviewed in this conversation. Data/schema failures, if found, will be retained rather than silently fixed and relabeled success. Source execution text in the historical runner's receipt is overridden descriptively by the separate Actions runtime receipt, without modifying the frozen runner.
