# Security Policy

PR-Insight is an open-source tool to help efficiently review and handle pull requests. Repolens Merge is a paid version of PR-Insight, designed for companies and teams that require additional features and capabilities.

This document describes the security policy of PR-Insight. For Repolens Merge's security policy, see [here](https://repolense-merge-docs.khulnasoft.com/overview/data_privacy/#repolense-merge).

## PR-Insight Self-Hosted Solutions

When using PR-Insight with your OpenAI (or other LLM provider) API key, the security relationship is directly between you and the provider. We do not send your code to Repolens servers.

Types of [self-hosted solutions](https://repolense-merge-docs.khulnasoft.com/installation):

- Locally
- GitHub integration
- GitLab integration
- BitBucket integration
- Azure DevOps integration

## PR-Insight Supported Versions

This section outlines which versions of PR-Insight are currently supported with security updates.

### Docker Deployment Options

#### Latest Version

For the most recent updates, use our latest Docker image which is automatically built nightly:

```yaml
uses: repolens-ai/pr-insight@main
```

#### Specific Release Version

For a fixed version, you can pin your action to a specific release version. Browse available releases at:
[PR-Insight Releases](https://github.com/repolens-ai/pr-insight/releases)

For example, to github action:

```yaml
steps:
  - name: PR Insight action step
    id: prinsight
    uses: docker://khulnasoft/pr-insight:0.26-github_action
```

#### Enhanced Security with Docker Digest

For maximum security, you can specify the Docker image using its digest:

```yaml
steps:
  - name: PR Insight action step
    id: prinsight
    uses: docker://khulnasoft/pr-insight@sha256:14165e525678ace7d9b51cda8652c2d74abb4e1d76b57c4a6ccaeba84663cc64
```

## Reporting a Vulnerability

We take the security of PR-Insight seriously. If you discover a security vulnerability, please report it immediately to:

Email: security@khulnasoft.com

Please include a description of the vulnerability, steps to reproduce, and the affected PR-Insight version.
