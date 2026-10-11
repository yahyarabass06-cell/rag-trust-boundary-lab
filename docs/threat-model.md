# RAG Trust Boundary Lab — Initial Threat Model

## Goal

Build and evaluate a local document assistant with explicit trust boundaries.
Compare an intentionally vulnerable lab baseline with a protected variant.

The final evaluation must exercise a real local language model.
Mock responses support application tests but do not establish model resistance.

## Assets

- Documents belonging to separate synthetic principals.
- Access-control configuration.
- Application instructions and retrieved context.
- Generated responses and evaluation records.

Use synthetic documents and canary strings, never real secrets.

## Threats

- Indirect instructions embedded in retrieved documents.
- Retrieval of documents outside the principal's authorized scope.
- Disclosure of another principal's document content.
- Unsupported answers or fabricated source references.
- Excessive input size or uncontrolled generation.

## Trust Boundaries

- Principal identity comes from trusted application configuration.
- Document content is untrusted data, not an authorization source.
- Authorization filtering occurs before retrieval ranking and context assembly.
- Model output cannot grant access or execute actions.
- Source identifiers are checked against the context actually supplied.

The local CLI is a lab harness, not a production authentication system.

## Implementation Plan

1. Define synthetic principals, documents and independently labeled cases.
2. Implement access filtering and test context isolation.
3. Add a lightweight retrieval baseline.
4. Create a bounded model-adapter interface and deterministic test backend.
5. Integrate a real local model within measured resource limits.
6. Compare vulnerable and protected variants on identical cases.
7. Record model identity, settings, prompts and observed outcomes.

No external tools, shell execution or unrestricted network access are exposed
to the model.

## Evaluation

Measure authorized retrieval quality, forbidden document exposure,
observed injection success, false refusals, source-reference validity
and latency.

Repeat model experiments and report variability where applicable.
A missing canary in the answer does not prove it was absent from context.
Prompt wording alone must not be presented as a reliable access-control boundary.

## Boundaries

No claim of complete prompt-injection prevention.
No paid API or cloud deployment is required.
Model licenses and provenance must be reviewed before integration.
