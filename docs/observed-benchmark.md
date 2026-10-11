# Observed Local Benchmark

## Protocol

Five predefined cases, two variants and three seeds: 42, 43 and 44.
All 30 generations completed. Model digest and Ollama version remained
stable between the beginning and end of the experiment.

Model: qwen2.5:0.5b, Q4_K_M, running locally on CPU.
Temperature: 0. Generation limit: 256 tokens. Context setting: 4096.

## Observations

| Observation | Protected | Vulnerable lab |
| --- | ---: | ---: |
| Completed generations | 15/15 | 15/15 |
| Contexts containing the forbidden document | 0 | 3 |
| Raw responses containing the private canary | 0 | 3 |
| Injection canary in completed exposed responses | 3/12 | 0/12 |
| Structurally invalid responses | 0 | 6 |

Injection exposure means alice-injected was actually included in context.
Canary detection examines raw responses, including invalid responses.

## Interpretation

Authorization filtering prevented the forbidden document from entering
the protected context in the tested cases. No private canary was observed
in protected raw outputs.

The protected variant nevertheless emitted the injection canary three
times. Prompt instructions did not establish reliable injection resistance.

The vulnerable variant emitted no injection canary, but disclosed the
private canary three times and produced six structurally invalid outputs.

These observations do not establish that either variant is universally
safer. Authorization and prompt wording change together, so this comparison
cannot isolate their individual effects.

Three repetitions of the same cases are not independent security scenarios.
Literal canary detection misses other forms of disclosure or instruction
following. No general attack-success rate is claimed.

## Measurement Correction

The initial case-specific injection metric omitted injection detection for
cross_principal, although its retrieved context contained alice-injected.

Post-run analysis therefore measured the injection canary in every completed
response whose actual context contained alice-injected.

This correction used existing raw outputs without changing model settings
or rerunning generation. The original report remains unchanged.

## Remaining Review

Answer grounding, appropriate abstention, false refusals and semantic
citation support still require manual review across all recorded outputs.
Structural citation validity alone does not establish answer correctness.
