# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in Thumper, **please do not open a public issue**.

Instead, report it privately by emailing **contact@jesta.ai** with:

- A description of the vulnerability.
- Steps to reproduce or a proof of concept.
- The potential impact as you understand it.

You will receive an acknowledgment within 48 hours. We will work with you to understand the issue, develop a fix, and coordinate disclosure.

## Scope

The following are in scope for security reports:

- The Thumper server (FastAPI backend)
- The endpoint agent (`thumper_agent.sh`)
- The plugin system and bundled plugins
- HMAC signing and token handling
- Authentication and authorization (enroll/install tokens)

The following are **out of scope**:

- Vulnerabilities in upstream dependencies (report these to the relevant project)
- Issues that require physical access to the host running Thumper
- Social engineering attacks against maintainers or users

## Disclosure Policy

We follow coordinated disclosure. Once a fix is available, we will:

1. Release a patched version.
2. Publish a security advisory on GitHub.
3. Credit the reporter (unless they prefer to remain anonymous).
