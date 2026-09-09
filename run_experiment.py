"""
Reproducible security/reliability evaluation harness for MCP-Swarm (TPS 2026
submission). Run with: python3 run_experiment.py

Produces metrics.json. Seed is fixed for reproducibility; re-running yields
identical output.
"""
import json
import time
import numpy as np

from gateway import MCPGateway, UngatedBaseline, CapabilityToken, SCOPE_TABLE, HIGH_RISK_TOOLS
from council import (RotationalCouncil, MODELS, run_compromise_robustness_trial,
                      run_single_model_baseline_trial)
from memory import run_poisoning_defense_trial
from injection import run_injection_regression_suite

SEED = 20260808



# Each scenario below is labeled with the taxonomy category (from
# MCPSecBench, Yang et al. 2025) its underlying attack pattern is modeled
# on. Scenario 1 is a positive control, not an attack.
GATEWAY_SCENARIOS = [
    ("legitimate_call_allowed", None,
     dict(agent_role="supervisor", task_id="task-A"), "council.invoke", "task-A", 1),
    ("out_of_scope_denied", "MCPSecBench:ToolMisuse_ConfusedDeputy",
     dict(agent_role="document_intelligence", task_id="task-B"), "memory.expire", "task-B", 1),
    ("high_risk_requires_supervisor_denied", "MCPSecBench:PrivilegeEscalation",
     dict(agent_role="memory_agent", task_id="task-C"), "memory.expire_all", "task-C", 1),
    ("cross_task_delegation_denied", "TAMAS:ColludingAgents_analog",
     dict(agent_role="council_model", task_id="task-D"), "council.respond", "task-E", 1),
    ("expired_token_denied", "MCPSecBench:VulnerableClient_replay",
     dict(agent_role="external_tool_agent", task_id="task-F"), "api.invoke_readonly", "task-F", 45),
]


def _run_scenarios(gw):
    now = time.time()
    results = []
    for name, taxonomy, token_kwargs, tool, invoked_task_id, delay in GATEWAY_SCENARIOS:
        tok = CapabilityToken(issued_at=now, ttl_seconds=30, **token_kwargs)
        r = gw.enforce(tok, tool, invoked_task_id, now=now + delay)
        # For the positive control we expect "allowed"; for the four attack
        # scenarios we expect "denied" under a correctly enforcing gateway.
        expected_denied = name != "legitimate_call_allowed"
        passed = (not r.allowed) if expected_denied else r.allowed
        results.append({
            "name": name, "taxonomy": taxonomy, "passed": passed,
            "allowed": r.allowed, "reason": r.reason,
        })
    return results


def gateway_regression_suite():
    gw = MCPGateway()
    mcp_swarm_results = _run_scenarios(gw)

    baseline = UngatedBaseline()
    baseline_results = _run_scenarios(baseline)

    attack_scenarios = [r for r in mcp_swarm_results if r["name"] != "legitimate_call_allowed"]
    baseline_attack_scenarios = [r for r in baseline_results if r["name"] != "legitimate_call_allowed"]

    return {
        "mcp_swarm": {
            "tests": mcp_swarm_results,
            "passed": sum(1 for r in mcp_swarm_results if r["passed"]),
            "total": len(mcp_swarm_results),
            "attacks_blocked": sum(1 for r in attack_scenarios if r["passed"]),
            "attacks_total": len(attack_scenarios),
        },
        "ungated_baseline": {
            "tests": baseline_results,
            "attacks_blocked": sum(1 for r in baseline_attack_scenarios if r["passed"]),
            "attacks_total": len(baseline_attack_scenarios),
            "note": (
                "Allow-all baseline modeling an undefended MCP integration "
                "(cf. MCPSecBench's <30% cross-platform protection success "
                "rate). Expected to block 0 of 4 attack scenarios by "
                "construction; included as the comparison point the gateway "
                "is measured against, not as a novel finding."
            ),
        },
        "scope_table": {k: sorted(v) for k, v in SCOPE_TABLE.items()},
        "high_risk_tools": sorted(HIGH_RISK_TOOLS),
    }


def council_suite(rng):
    council = RotationalCouncil(rng)
    stats = council.fairness_over(n_queries=2000)
    robustness = run_compromise_robustness_trial(rng, n_trials=2000)
    baseline = run_single_model_baseline_trial(rng, n_trials=2000)
    return {
        "rotation_fairness": {
            "n_queries": 2000,
            "council_size": 4,
            "n_models": len(MODELS),
            "selection_counts": stats.counts,
            "coefficient_of_variation": round(stats.coefficient_of_variation, 4),
        },
        "single_model_compromise_robustness": robustness,
        "single_model_baseline_no_consensus": baseline,
    }


def main():
    rng = np.random.default_rng(SEED)

    gateway_results = gateway_regression_suite()
    council_results = council_suite(rng)
    memory_results = run_poisoning_defense_trial()
    injection_results = run_injection_regression_suite()

    metrics = {
        "seed": SEED,
        "harness": "supplemental/run_experiment.py",
        "note": (
            "Synthetic, seeded, reproducible evaluation of the security "
            "control logic described in the paper (MCP gateway scope "
            "enforcement vs. an ungated baseline, rotational council "
            "consensus robustness vs. a single-model baseline, TF-IDF-"
            "backed memory provenance gating, and a T2 prompt-injection "
            "channel-separation regression suite modeled on the published "
            "MCPSecBench/TAMAS attack taxonomies). Does not call real LLM "
            "APIs, a real MCP client/server, or a trained embedding model; "
            "see paper Sec. Limitations for scope and honesty boundaries."
        ),
        "mcp_gateway_regression_suite": gateway_results,
        "rotational_council": council_results,
        "memory_provenance_gate": memory_results,
        "prompt_injection_regression_suite": injection_results,
    }

    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
