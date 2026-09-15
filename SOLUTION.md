# Solution Steps

1. Add a privacy boundary that removes sensitive case fields recursively and redacts both seeded values and common identifier formats from free text.

2. Assemble model context as serialized reference data rather than executable instructions. Strip obvious prompt-injection sentences from uploaded material and explicitly state that all retrieved content is evidence only.

3. Evaluate policy on every answer and draft turn, not only the first answer in a session. Add deterministic blocks for privacy, cross-site data, medical advice, and policy-override attempts, then use the real model for remaining scope classification with fail-closed parsing.

4. Return an actionable redirect for every blocked category and write a sanitized `policy_intervention` audit event for every refusal.

5. Hash session identifiers before using them as history keys or audit identifiers, and retain only redacted requests and outputs in conversation history.

6. Remove the seeded adapter-error data leak. Case records supplied to generation now contain only sanitized operational fields, while processing failures return a fixed safe message without exception or record contents.

7. Apply a final output privacy filter after generation. Record a `privacy_intervention` whenever the filter changes model output, followed by a sanitized completion event.

8. Make the audit store sanitize all nested details as defense in depth, so requests, records, outputs, and errors cannot persist seeded identifiers.

9. Replace FastAPI's default validation response because it may echo invalid request input. Map configuration and unexpected failures to generic safe API errors.

10. Keep readiness independent from the provider key, while retaining the OpenAI integration and optional keyed model ping for end-to-end verification.

11. Start PostgreSQL, run `python -m app.readiness`, place `OPENAI_API_KEY` in `.env` for live requests, and launch the service with `./run.sh`.

