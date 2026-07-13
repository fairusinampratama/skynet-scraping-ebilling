# Skynet E-Billing Migration Utilities

Utilities for extracting, cleaning, and preparing legacy ISP billing data for migration into the newer Skynet E-Billing system.

## Security Notice

Real migration exports are intentionally excluded from this repository. Customer records, identity numbers, phone numbers, addresses, coordinates, router account data, payment history, uploaded document URLs, cookies, local databases, and generated exports must remain outside Git.

The current branch is suitable for documenting the migration workflow only. If real data is ever committed, treat it as a security incident: remove it from the current branch, purge it from Git history, and rotate any exposed credentials.

## Repository Scope

This repository is for migration tooling and documentation, not for storing operational data.

Expected private/generated artifacts include:

- `migration_data/*.json`
- `*.csv`, `*.xls`, `*.xlsx`
- `.env`
- `cookies.txt`
- `*.db`, `*.sqlite`, `*.sql`
- scraped HTML pages
- logs and temporary exports

These files are ignored by `.gitignore` and should be shared only through approved private channels when legally and operationally required.

## Safe Migration Workflow

1. Export legacy data into a private local working directory.
2. Clean and validate the data locally.
3. Replace real records with anonymized fixtures before committing examples.
4. Import only from the private environment into the target database.
5. Rotate any credential that appears in a repository, issue, log, artifact, or screenshot.

## Portfolio Note

This project may be referenced publicly as a migration and data-cleaning utility, but public materials must describe the workflow without exposing customer data or infrastructure secrets.
