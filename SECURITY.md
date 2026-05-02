# Security Policy

## Supported Versions

This project currently supports the latest code on the `main` branch. Security fixes are applied there first.

If versioned releases are introduced later, this policy should be updated with a supported-version table.

## Reporting a Vulnerability

Please do not report security vulnerabilities in public issues.

If you believe you have found a vulnerability, contact the maintainers privately through the repository owner's GitHub profile or open a minimal public issue asking for a private contact path. Do not include exploit details, API tokens, private prompts, request logs, customer data, or other sensitive information in public.

Helpful private reports include:

- A short description of the issue and impact.
- Steps to reproduce using dummy data.
- Affected endpoints or files.
- Any relevant configuration, such as `AUTH_MODE=true` or `AUTH_MODE=false`.
- Whether credentials, user data, or Replicate API tokens may be exposed.

## Scope

Security-sensitive areas include:

- Handling of `REPLICATE_API_TOKEN` and Bearer tokens.
- `AUTH_MODE=true` BYOK behavior.
- Request forwarding to Replicate.
- Streaming responses and error handling.
- Model listing and dynamic model resolution.
- Docker and deployment configuration.

## Secrets and Logs

Never commit `.env` files, Replicate API tokens, authorization headers, private prompts, generated URLs that should remain private, or production logs containing user data. If a secret is accidentally exposed, revoke it immediately and rotate the affected credential.

## Response Expectations

Maintainers will aim to acknowledge vulnerability reports promptly, investigate the issue, and coordinate a fix where appropriate. Timelines may vary because this is a small open-source project.

