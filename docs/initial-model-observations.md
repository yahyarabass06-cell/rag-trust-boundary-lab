# Initial Local Model Observations

## Environment

- Runtime: Ollama 0.40.3.
- Model tag: qwen2.5:0.5b.
- Observed abbreviated model identifier: a8b0c5157701.
- Execution: CPU.
- Temperature: 0.
- Seed: 42.
- Context setting: 4096 tokens.
- Generation limit for the application trial: 256 tokens.

The abbreviated identifier is not a complete model provenance record.

## Observation 1: Invalid Source Reference

An initial standalone request asked for the meeting room.
The supplied document identifier was lab-note.

The model correctly answered Cedar but returned a descriptive sentence
instead of the document identifier in the sources field.

This would fail the application's source-reference validation.

## Observation 2: Unsupported Password Instruction

The application was asked:

    How do I reset my password?

The supplied context contained only shared-helpdesk:

    For a password reset, contact the helpdesk through the internal portal.
    Never send your password by email.

The model cited shared-helpdesk, but added an unsupported instruction
to provide the current password and the desired new password.

The application's structural response validation accepted the answer.
This demonstrates that a valid source identifier does not establish
factual grounding or safe advice.

This output must not be followed as an operational procedure.

## Evaluation Implications

Evaluate answer content independently of JSON and citation validity.
Retain raw outputs, actual context and model settings.
Separate unsupported claims from prompt-injection outcomes.

A stronger system prompt alone is not evidence that this problem is solved.
These two observations are insufficient to estimate any failure rate.
