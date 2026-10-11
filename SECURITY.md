# Security Considerations

## Authorized Laboratory Use

Use synthetic documents and canaries or explicitly authorized data.
The included canaries are test markers, not real secrets.

The vulnerable variant deliberately bypasses document authorization.
Do not connect this harness to confidential corpora or expose it as a service.

## Identity and Access

Principal identity is supplied by trusted local configuration.
Selecting a CLI principal does not authenticate a user.

Document permissions are separate from untrusted document text.
Authorization occurs before protected retrieval and context assembly.

## Model and Output Trust

The model receives no execution tools.
Generated content remains untrusted even when JSON and source checks pass.

Citation identifiers are checked for context membership, not semantic support.
Raw responses are retained for analysis, including invalid responses.

Do not treat generated advice as an approved operational procedure.

## Runtime and Resource Boundaries

The adapter uses the loopback Ollama endpoint without configured proxies.
Do not expose the Ollama service to untrusted network clients.

Character, corpus-byte and generation limits reduce resource exposure,
but do not provide exact tokenizer budgeting or process isolation.

An HTTP timeout may leave server-side computation running.
Input files must remain stable during reading.

## Reports and Filesystem

Reports may contain complete prompts and document content.
Keep generated reports and private inputs outside public Git repositories.

Exports use owner-only temporary files and exclusive hard-link publication.
Use directories controlled by the current user.

Model and corpus fingerprints identify bytes; they do not prove authenticity.

## Reporting Issues

Use minimized synthetic reproductions.
Do not attach credentials, private documents or confidential model outputs.
