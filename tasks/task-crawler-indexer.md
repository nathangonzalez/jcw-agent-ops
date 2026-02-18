# Task: Repo Crawler Indexer (Agent: coder)

## Goal
Implement repo crawler to index files into SQLite + JSONL.

## Inputs
- scripts/crawl_repo.py

## Outputs
- repo_index.sqlite
- repo_chunks.jsonl

## Acceptance Criteria
- Skips binaries and large files
- Excludes secret-like filenames
- Produces repeatable index

## Status
Assigned
