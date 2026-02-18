# Ops Metrics and Alerts

## Latency (Agent Response Time)
- Track median and P95 response time per agent.
- Warning: P95 > 2s for more than 5 minutes.
- Critical: P95 > 5s or any agent unresponsive more than 30s.

## Error Rate
- Measure percentage of agent requests returning error (per minute or hour).
- Warning: error rate > 2 percent sustained for 5 minutes.
- Critical: error rate > 5 percent over any 1-minute interval.

## Queue Depth
- Monitor number of tasks waiting in each agent queue.
- Warning: more than 10 tasks pending for any agent.
- Critical: more than 50 tasks or queue not draining.

## System Cost
- Monitor projected and actual spend per hour, day, and week.
- Warning: more than 75 percent of daily or weekly budget reached.
- Critical: over budget or spending rate doubles vs baseline.

## Approval Latency
- Track time approvals wait unresolved.
- Warning: more than 10 minutes pending.
- Critical: more than 30 minutes pending or backlog over 5 items.
