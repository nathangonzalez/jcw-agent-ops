# Engineering Notes

## Ingest and Crawler Improvements

### Schema
- Normalize vendors, categories, and accounts into reference tables; store only IDs in transaction rows.
- Add metadata fields: import_source, batch_id, confidence_score, ingested_at, raw_line.
- Add currency and exchange_rate for multi-currency support.
- Add user_id for multi-user linkage where needed.
- Add tags for flexible labeling.
- Add unique constraints for deduplication (example: date, amount, vendor_id, account_id).

### Parsing
- Expand header mapping to handle more column variants.
- Add robust date and number parsing with fallbacks.
- Add vendor alias mapping to canonical forms.
- Log parse errors to a side table.
- Allow partial processing when some rows fail.
- Add inline data quality checks for missing essentials or duplicates.
- Add crawl include or exclude patterns for file discovery.

### Performance
- Use batch inserts and explicit transactions for large loads.
- Stream files and rows to reduce memory use.
- Defer index creation during large ingests.
- Add incremental ingest and resume support using file hashes.
- Parallelize heavy ingest runs across directories.

## Suggested Schema Fields

| Field            | Type            | Description |
|------------------|-----------------|-------------|
| id               | INTEGER/PK      | Transaction ID |
| date             | DATE            | Transaction date |
| amount           | DECIMAL         | Signed amount |
| currency         | TEXT(3)         | Currency code (USD, EUR, etc) |
| vendor_id        | INTEGER         | FK to vendor reference table |
| category_id      | INTEGER         | FK to category reference table |
| account_id       | INTEGER         | FK to account reference table |
| description      | TEXT            | Parsed transaction description |
| raw_line         | TEXT            | Raw source line for debugging |
| import_source    | TEXT            | File or crawler source |
| batch_id         | TEXT/INTEGER    | Import batch grouping |
| confidence_score | REAL            | Classification confidence score |
| tags             | TEXT/JSON       | Freeform or system-applied labels |
| user_id          | INTEGER         | Owner or user reference |
| ingested_at      | DATETIME        | Ingest timestamp |
| status           | ENUM            | imported, needs_review, invalid |
