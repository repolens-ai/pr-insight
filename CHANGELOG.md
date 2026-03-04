# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-04

### Added
- Gitea provider support (`pr_insight/git_providers/gitea_provider.py`)
- AWS Secrets Manager provider (`pr_insight/secret_providers/aws_secrets_manager_provider.py`)
- Agent module for command orchestration (`pr_insight/agent/`)
- Lambda webhook handlers for GitHub and GitLab
- New tool: `help_docs` for generating help documentation
- New tool: `generate_labels` for automatic label generation
- New tool: `add_docs` for documentation updates
- VSCode workspace configuration (extensions, settings, launch, tasks)
- Docker Compose for local development
- Renovate configuration for automated dependency updates
- Mypy type checking configuration

### Changed
- Migrated from pip to uv for dependency management
- Updated to Python 3.12+
- Updated dependencies to latest versions
- Improved Docker build with uv caching

### Fixed
- Test expectations for `insert_br_after_x_chars` function

## [0.2.5] - Previous

### Added
- Initial release with core features
- GitHub, GitLab, Bitbucket, Azure DevOps support
- CLI tools: review, describe, improve, ask, config
- Multiple AI handler support (OpenAI, LiteLLM, Anthropic)

---

For older releases, please refer to the git history.
