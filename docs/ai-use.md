# AI assistance

The project was planned with Codex and with a user-supplied Claude plan.
Codex generated implementation code, proof terms, tests, documentation and
untrusted search certificates. The coordinator used the model selected by
the host session; its precise runtime identity must be reported from host
metadata rather than inferred from a recommendation. The two implementation
workers were explicitly started with GPT-6.1 Sol, High reasoning effort.

The Python solvers and emitter are untrusted. Checking a certificate in Python
or running a compiled checker is not a proof of the submitted result. The
result requires safe Agda checking of the concrete certificates and the
generic checker-soundness theorem, together with faithful Othello rules.

This disclosure records actual assistance. It is independent of commit-message
format; commits do not contain attribution trailers.
