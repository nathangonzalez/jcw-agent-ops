# Research Backlog (Spikes)

## Focus Areas
- Agent orchestration patterns (planner-worker, critic, debate, A2A routing)
- Memory architectures (short-term, long-term, vector, tool memory)
- Tool safety and approval protocols
- Evaluation harnesses (task success, robustness, drift)
- Retrieval and grounding (RAG, structured data, schemas)
- Autonomy boundaries and guardrails
- Cost and latency optimization
- Prompt injection and sandbox escape mitigation

---

## Candidate Spikes

1. Compare leading agent orchestration frameworks and their tradeoffs.
2. Survey recent research on tool-use safety and approval gating.
3. Collect best practices for multi-agent coordination and task routing.
4. Evaluate memory strategies for long-running agent sessions.
5. Identify evaluation benchmarks for agentic systems in production.
6. Summarize failure modes in autonomous workflows and mitigations.
7. Review agentic coding workflows and CI integration patterns.
8. Scan for recent methods that reduce hallucinations in tool-using agents.
9. Map cost drivers across agent pipelines and propose optimization tactics.
10. Track regulatory and compliance considerations for agentic automation.

---

## Intake Rules
- Each spike includes: goal, scope, sources, findings, and test plan.
- Focus on sources with primary evidence (papers, docs, talks by authors).
- Capture date and version for each finding.

---

## Proposed Spikes (weekly 2026-02-18)

## Proposed Spikes

### 1. Spike: Emergent Communication in LLM-based Multi-Agent Simulations  
- **Goal:** Test if language model agents can develop and utilize communication protocols in cooperative tasks.  
- **Scope:** Simulate 5+ language model agents in a GridWorld collecting and sharing information to complete a shared objective.  
- **Sources:**  
  - Foerster et al., 2016  
  - Stanford CRFM video (2023-10-18)  
- **Experiment:**  
  - Deploy agents with varying communication constraints.  
  - Measure impact of emergent communication strategies on task efficiency.

### 2. Spike: Comparative Benchmarking Using PettingZoo  
- **Goal:** Assess different MARL algorithms on standardized tasks using PettingZoo.  
- **Scope:** Compare DQN, PPO, and actor-critic methods on at least 3 environments (cooperative and competitive).  
- **Sources:**  
  - PettingZoo docs  
  - Wang & Lu (2021) survey  
- **Experiment:**  
  - Implement agent stacks; track win rates, convergence time, and sample efficiency across environments.

### 3. Spike: Robustness of Agentic Alignment Mechanisms  
- **Goal:** Evaluate different alignment protocols for preventing subgoal divergence in autonomous agents.  
- **Scope:** Use simplified MARL scenarios where agents are prone to reward hacking or misaligned delegation.  
- **Sources:**  
  - Christiano (2023)  
  - OpenAI safety alignment docs  
- **Experiment:**  
  - Introduce adversarial goals and test ability of alignment methods to retain intended outcomes.

### 4. Spike: Real-World Multi-Agent Coordination Case Study Replication  
- **Goal:** Replicate a simplified version of the disaster response deployment described by Milind Tambe.  
- **Scope:** Model agents representing emergency units with partial information and communication constraints.  
- **Sources:**  
  - AI Alignment Podcast interview (2023-11-08)  
  - Related case-study papers by Tambe  
- **Experiment:**  
  - Vary communication and resource-sharing policies, measure response time and coverage.

### 5. Spike: Mapping Social Behavior Emergence in Simulated Agent Societies  
- **Goal:** Analyze under what conditions LLM or MARL-based agents manifest social behaviors (e.g., trust, deception).  
- **Scope:** Reproduce and extend Stanford CRFM "society simulation" with different agent objectives and constraints.  
- **Sources:**  
  - Stanford CRFM, 2023-10-18  
  - MARL emergent behavior literature  
- **Experiment:**  
  - Systematically vary interaction protocols, track metrics for social dynamics (cooperation rates, conflict incidents, negotiation outcomes).

---
```

---

## Proposed Spikes (daily 2026-02-18)

## Proposed Spikes

### 1. Spike: Benchmarking Collaboration Modes in LLM-Based Multi-Agent Simulations
- **Goal:** Compare negotiation/cooperation success rates under different environment parameters for simulated LLM agents.
- **Scope:** Reproduce key tasks from Chen et al. (2026-02-14), running agents with and without explicit communication channels.
- **Sources:**  
  - Chen et al., 2026-02-14 (arXiv)  
  - DeepMind tool-use video & benchmarks (2026-02-12)
- **Experiment:**  
  1. Simulate resource-sharing environments.
  2. Log coalition formation, negotiation outcomes, and task efficiency.
  3. Analyze for parameter regimes leading to spontaneous cooperation vs. collapse.

---
```
