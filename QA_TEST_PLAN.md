# Ledger Classifier + Manual Review QA Plan

## Functional Tests

### Ledger Classifier
- [ ] Correctly classifies standard transactions (happy path)
- [ ] Handles malformed/incomplete data gracefully
- [ ] Flags transactions needing manual review per rules
- [ ] Marks ambiguous transactions as review
- [ ] Ignores duplicate transactions
- [ ] Supports bulk processing
- [ ] Handles empty inputs

### Manual Review Workflow
- [ ] Pending queue loads correctly
- [ ] Detail view shows full fields + history
- [ ] Approve updates status and removes from queue
- [ ] Reject updates status and logs reason
- [ ] Escalate captures reason
- [ ] Bulk actions work; partial failures handled
- [ ] Refresh updates list without stale data
- [ ] Prevents actions on already-completed items
- [ ] Blocks review if required data is missing

## Edge Cases
- [ ] Transaction arrives during queue load
- [ ] Two reviewers act on same item
- [ ] Crash during approve/reject; state consistent on reload
- [ ] Very large batch (1000+)
- [ ] Non-UTF8 characters in fields
- [ ] Multi-tab or multi-device conflicts
- [ ] Manual modification after review is recorded and visible

## Data Integrity
- [ ] No transaction reviewed twice
- [ ] History is complete and tamper-evident
- [ ] All actions persist to DB
- [ ] Status is consistent across UI/API/DB
- [ ] Approved/rejected items not returned to queue
- [ ] Required fields present for classified rows
- [ ] Clear rollback or error state on action failure

## Audit Logging
- [ ] Log who/when/what/why for each action
- [ ] Log any data changes after submission
- [ ] Log bulk actions per item
- [ ] Log access to manual review queue
- [ ] Logs are immutable and timestamped
- [ ] Automated classifier actions logged separately

## Security/Permissions
- [ ] Only authorized users can access
- [ ] No unauthorized actions via direct API
- [ ] Reviewer self-approval rules enforced

## Regression
- [ ] Legacy data compatible
- [ ] Migrations preserve queue integrity

## Pipeline QA Checklist

### CSV Ingestion
- [ ] Accepts only supported file types (CSV)
- [ ] Handles files with headers, missing headers, or extra columns
- [ ] Rejects files with invalid format or encoding
- [ ] Validates required fields are present in each row
- [ ] Skips or reports duplicate records on upload
- [ ] Handles empty files or rows gracefully
- [ ] Accurately processes large files (stress test 10k+ rows)
- [ ] Supports special characters and multiple encodings
- [ ] Provides clear error reporting for invalid rows or files
- [ ] Records each ingestion event in system logs (filename, user, timestamp)

### Classification Rules
- [ ] Applies rules to each ingested record as specified
- [ ] Correctly classifies typical examples
- [ ] Flags records with no match for manual review
- [ ] Handles unexpected, malformed, or missing data fields
- [ ] Maintains rule order and logic
- [ ] Rule engine does not modify non-target fields in records
- [ ] Allows rule updates or reloads without interrupting ingest
- [ ] Logs rule evaluation results and errors per record

### Review Queue Integration
- [ ] All flagged records appear in manual review queue
- [ ] Records show accurate metadata (source file, ingest time, rule trigger)
- [ ] Queue only includes unreviewed or flagged records
- [ ] Review actions update queue correctly
- [ ] Prevents duplicate, missing, or orphaned queue entries
- [ ] Queue refresh reflects real-time changes
- [ ] Approved or rejected records are removed from queue
- [ ] Review actions are logged with user, time, and action taken

### Data Integrity and Logging
- [ ] No partial data loss on ingest or classification failures
- [ ] Every pipeline step is logged (ingest, rule execution, queue insert)
- [ ] All actions are timestamped and traceable to source or user
- [ ] Prevents unauthorized or duplicate changes to queue records
- [ ] All errors, warnings, and unusual events are audit-logged

### Edge Cases
- [ ] Handles malformed CSVs (uneven columns, invalid delimiters)
- [ ] Multiple CSV uploads do not cause race conditions or data loss
- [ ] Retries of failed ingest do not create duplicates
- [ ] Handles very long strings, odd encodings, date edge cases
- [ ] Idempotent ingest if the same file is uploaded multiple times

### Security and Access
- [ ] Only authenticated users may upload, classify, or review
- [ ] Prevents file-based attacks (CSV injection, code in data fields)
- [ ] All access and modification actions are audit-logged
