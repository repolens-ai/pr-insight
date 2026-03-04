<a href="https://github.com/khulnasoft/pr-insight/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/khulnasoft/pr-insight/main?style=for-the-badge" height="20">
</a>

<br />

# 🚀 PR Insight - The Original Open-Source PR Reviewer.

 This repository contains the open-source PR Insight Project. 
 It is not the Repolens free tier.
 
Try the free version on our website.

👉[Get Started Now](www.khulnasoft.com/get-started/)

PR-Insight is an open-source, AI-powered code review agent and a community-maintained legacy project of Repolens. It is distinct from Repolens’s primary AI code review offering, which provides a feature-rich, context-aware experience. Repolens now offers a free tier that integrates seamlessly with GitHub, GitLab, Bitbucket, and Azure DevOps for high-quality automated reviews.

## Table of Contents

- [Getting Started](#getting-started)
- [Why Use PR-Insight?](#why-use-pr-insight)
- [Features](#features)
- [See It in Action](#see-it-in-action)
- [Try It Now](#try-it-now)
- [How It Works](#how-it-works)
- [Data Privacy](#data-privacy)
- [Contributing](#contributing)

## Getting Started

### 🚀 Quick Start for PR-Insight

#### 1. Try it Instantly (No Setup)
Test PR-Insight on any public GitHub repository by commenting `@KhulnaSoft-Agent /improve`

#### 2. GitHub Action (Recommended)
Add automated PR reviews to your repository with a simple workflow file:
```yaml
# .github/workflows/pr-insight.yml
name: PR Insight
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  pr_insight_job:
    runs-on: ubuntu-latest
    steps:
    - name: PR Insight action step
      uses: khulnasoft/pr-insight@main
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
[Full GitHub Action setup guide](https://repolense-merge-docs.khulnasoft.com/installation/github/#run-as-a-github-action)

#### 3. CLI Usage (Local Development)
Run PR-Insight locally on your repository:
```bash
pip install pr-insight
export OPENAI_KEY=your_key_here
pr-insight --pr_url https://github.com/owner/repo/pull/123 review
```
[Complete CLI setup guide](https://repolense-merge-docs.khulnasoft.com/usage-guide/automations_and_usage/#local-repo-cli)

#### 4. Other Platforms
- [GitLab webhook setup](https://repolense-merge-docs.khulnasoft.com/installation/gitlab/)
- [BitBucket app installation](https://repolense-merge-docs.khulnasoft.com/installation/bitbucket/)
- [Azure DevOps setup](https://repolense-merge-docs.khulnasoft.com/installation/azure/)

[//]: # (## News and Updates)

[//]: # ()
[//]: # (## Aug 8, 2025)

[//]: # ()
[//]: # (Added full support for GPT-5 models. View the [benchmark results]&#40;https://repolense-merge-docs.khulnasoft.com/pr_benchmark/#pr-benchmark-results&#41; for details on the performance of GPT-5 models in PR-Insight.)

[//]: # ()
[//]: # ()
[//]: # (## Jul 17, 2025)

[//]: # ()
[//]: # (Introducing `/compliance`, a new Repolens Merge 💎 tool that runs comprehensive checks for security, ticket requirements, codebase duplication, and custom organizational rules. )

[//]: # ()
[//]: # (<img width="384" alt="compliance-image" src="https://khulnasoft.com/images/pr_insight/compliance_partial.png"/>)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://repolense-merge-docs.khulnasoft.com/tools/compliance/&#41;)

[//]: # ()
[//]: # ()
[//]: # (## Jul 1, 2025)

[//]: # (You can now receive automatic feedback from Repolens Merge in your local IDE after each commit. Read more about it [here]&#40;https://github.com/repolens-ai/agents/tree/main/agents/repolense-merge-post-commit&#41;.)

[//]: # ()
[//]: # ()
[//]: # (## Jun 21, 2025)

[//]: # ()
[//]: # (v0.30 was [released]&#40;https://github.com/repolens-ai/pr-insight/releases&#41;)

[//]: # ()
[//]: # ()
[//]: # (## Jun 3, 2025)

[//]: # ()
[//]: # (Repolens Merge now offers a simplified free tier 💎.)

[//]: # (Organizations can use Repolens Merge at no cost, with a [monthly limit]&#40;https://repolense-merge-docs.khulnasoft.com/installation/repolense_merge/#cloud-users&#41; of 75 PR reviews per organization.)

[//]: # ()
[//]: # ()
[//]: # (## Apr 30, 2025)

[//]: # ()
[//]: # (A new feature is now available in the `/improve` tool for Repolens Merge 💎 - Chat on code suggestions.)

[//]: # ()
[//]: # (<img width="512" alt="image" src="https://khulnasoft.com/images/pr_insight/improve_chat_on_code_suggestions_ask.png" />)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://repolense-merge-docs.khulnasoft.com/tools/improve/#chat-on-code-suggestions&#41;.)

[//]: # ()
[//]: # ()
[//]: # (## Apr 16, 2025)

[//]: # ()
[//]: # (New tool for Repolens Merge 💎 - `/scan_repo_discussions`.)

[//]: # ()
[//]: # (<img width="635" alt="image" src="https://khulnasoft.com/images/pr_insight/scan_repo_discussions_2.png" />)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://repolense-merge-docs.khulnasoft.com/tools/scan_repo_discussions/&#41;.)

## Why Use PR-Insight?

### 🎯 Built for Real Development Teams

**Fast & Affordable**: Each tool (`/review`, `/improve`, `/ask`) uses a single LLM call (~30 seconds, low cost)

**Handles Any PR Size**: Our [PR Compression strategy](https://repolense-merge-docs.khulnasoft.com/core-abilities/#pr-compression-strategy) effectively processes both small and large PRs

**Highly Customizable**: JSON-based prompting allows easy customization of review categories and behavior via [configuration files](pr_insight/settings/configuration.toml)

**Platform Agnostic**: 
- **Git Providers**: GitHub, GitLab, BitBucket, Azure DevOps, Gitea
- **Deployment**: CLI, GitHub Actions, Docker, self-hosted, webhooks
- **AI Models**: OpenAI GPT, Claude, Deepseek, and more

**Open Source Benefits**:
- Full control over your data and infrastructure
- Customize prompts and behavior for your team's needs
- No vendor lock-in
- Community-driven development

## Features

<div style="text-align:left;">

PR-Insight offers comprehensive pull request functionalities integrated with various git providers:

|                                                         |                                                                                        | GitHub | GitLab | Bitbucket | Azure DevOps | Gitea |
|---------------------------------------------------------|----------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|
| [TOOLS](https://repolense-merge-docs.khulnasoft.com/tools/)         | [Describe](https://repolense-merge-docs.khulnasoft.com/tools/describe/)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Review](https://repolense-merge-docs.khulnasoft.com/tools/review/)                                |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Improve](https://repolense-merge-docs.khulnasoft.com/tools/improve/)                              |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Ask](https://repolense-merge-docs.khulnasoft.com/tools/ask/)                                      |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | ⮑ [Ask on code lines](https://repolense-merge-docs.khulnasoft.com/tools/ask/#ask-lines)            |   ✅   |   ✅   |           |              |       |
|                                                         | [Help Docs](https://repolense-merge-docs.khulnasoft.com/tools/help_docs/?h=auto#auto-approval)     |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Update CHANGELOG](https://repolense-merge-docs.khulnasoft.com/tools/update_changelog/)            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [USAGE](https://repolense-merge-docs.khulnasoft.com/usage-guide/)   | [CLI](https://repolense-merge-docs.khulnasoft.com/usage-guide/automations_and_usage/#local-repo-cli)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [App / webhook](https://repolense-merge-docs.khulnasoft.com/usage-guide/automations_and_usage/#github-app)                      |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Tagging bot](https://github.com/khulnasoft/pr-insight#try-it-now)                                                     |   ✅   |        |           |              |       |
|                                                         | [Actions](https://repolense-merge-docs.khulnasoft.com/installation/github/#run-as-a-github-action)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [CORE](https://repolense-merge-docs.khulnasoft.com/core-abilities/) | [Adaptive and token-aware file patch fitting](https://repolense-merge-docs.khulnasoft.com/core-abilities/compression_strategy/) |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Chat on code suggestions](https://repolense-merge-docs.khulnasoft.com/core-abilities/chat_on_code_suggestions/)                |   ✅   |  ✅   |           |              |       |
|                                                         | [Dynamic context](https://repolense-merge-docs.khulnasoft.com/core-abilities/dynamic_context/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Fetching ticket context](https://repolense-merge-docs.khulnasoft.com/core-abilities/fetching_ticket_context/)                  |   ✅    |  ✅    |     ✅     |              |       |
|                                                         | [Incremental Update](https://repolense-merge-docs.khulnasoft.com/core-abilities/incremental_update/)                            |   ✅    |       |           |              |       |
|                                                         | [Interactivity](https://repolense-merge-docs.khulnasoft.com/core-abilities/interactivity/)                                      |   ✅   |  ✅   |           |              |       |
|                                                         | [Local and global metadata](https://repolense-merge-docs.khulnasoft.com/core-abilities/metadata/)                               |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Multiple models support](https://repolense-merge-docs.khulnasoft.com/usage-guide/changing_a_model/)                            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [PR compression](https://repolense-merge-docs.khulnasoft.com/core-abilities/compression_strategy/)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [RAG context enrichment](https://repolense-merge-docs.khulnasoft.com/core-abilities/rag_context_enrichment/)                    |   ✅    |       |    ✅     |              |       |
|                                                         | [Self reflection](https://repolense-merge-docs.khulnasoft.com/core-abilities/self_reflection/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |

[//]: # (- Support for additional git providers is described in [here]&#40;./docs/Full_environments.md&#41;)
___

## See It in Action

</div>
<h4><a href="https://github.com/khulnasoft/pr-insight/pull/530">/describe</a></h4>
<div align="center">
<p float="center">
<img src="https://www.khulnasoft.com/images/pr_insight/describe_new_short_main.png" width="512">
</p>
</div>
<hr>

<h4><a href="https://github.com/khulnasoft/pr-insight/pull/732#issuecomment-1975099151">/review</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.khulnasoft.com/images/pr_insight/review_new_short_main.png" width="512">
</kbd>
</p>
</div>
<hr>

<h4><a href="https://github.com/khulnasoft/pr-insight/pull/732#issuecomment-1975099159">/improve</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.khulnasoft.com/images/pr_insight/improve_new_short_main.png" width="512">
</kbd>
</p>
</div>

<div align="left">

</div>
<hr>

## Try It Now

Try the GPT-5 powered PR-Insight instantly on _your public GitHub repository_. Just mention `@KhulnaSoft-Agent` and add the desired command in any PR comment. The agent will generate a response based on your command.
For example, add a comment to any pull request with the following text:

```
@KhulnaSoft-Agent /review
```

and the agent will respond with a review of your PR.

Note that this is a promotional bot, suitable only for initial experimentation.
It does not have 'edit' access to your repo, for example, so it cannot update the PR description or add labels (`@KhulnaSoft-Agent /describe` will publish PR description as a comment). In addition, the bot cannot be used on private repositories, as it does not have access to the files there.


## How It Works

The following diagram illustrates PR-Insight tools and their flow:

![PR-Insight Tools](https://www.khulnasoft.com/images/pr_insight/diagram-v0.9.png)

## Data Privacy

### Self-hosted PR-Insight

- If you host PR-Insight with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy


