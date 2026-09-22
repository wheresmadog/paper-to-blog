# Paper to Blog

Turn a research paper into a reader-friendly, source-faithful HTML article. The plugin accepts a local PDF or an `arxiv.org` paper URL, preserves the paper's version, explains the evidence and limits, and includes the paper's informative figures.

The HTML article is standalone by default. Every editorial section has exactly three paragraphs; figures contain the source pixels, descriptive alternative text, and a faithful caption.

## Before you install

This is a private GitHub repository. Your GitHub account must have access to `wheresmadog/paper-to-blog`, and your computer must be able to authenticate with GitHub over SSH. If access is missing, ask the repository owner to invite you before continuing.

## Install in Codex

The marketplace supports Codex Desktop and Codex CLI. Use Codex CLI once to add the repository as a marketplace and install the plugin; restart Codex Desktop or begin a new Codex session afterwards so the installed plugin is available.

```sh
codex plugin marketplace add git@github.com:wheresmadog/paper-to-blog.git
codex plugin add paper-to-blog@paper-to-blog
```

Alternatively, clone the repository and register the checked-out folder as a local marketplace:

```sh
git clone git@github.com:wheresmadog/paper-to-blog.git
codex plugin marketplace add /absolute/path/to/paper-to-blog
codex plugin add paper-to-blog@paper-to-blog
```

In Codex Desktop, start a new chat and select or `@`-mention **Paper to Blog** if you want to force use of the plugin. Codex can also select the installed skill automatically for a request that clearly asks for a paper-to-blog conversion.

## Install in Claude Code

From inside Claude Code, add the private repository as a marketplace and install the plugin for your user account:

```text
/plugin marketplace add git@github.com:wheresmadog/paper-to-blog.git
/plugin install paper-to-blog@paper-to-blog
```

Choose **User scope** when prompted to make it available in all of your projects. If Claude Code asks you to reload plugins, run `/reload-plugins` before using the command.

## Use it

The source must be either a path to a PDF available to the current agent or an `arxiv.org` `/abs/` or `/pdf/` URL. Quote a local path that contains spaces.

In Claude Code, the installed plugin skill is namespaced:

```text
/paper-to-blog:paper-to-blog /path/to/paper.pdf
/paper-to-blog:paper-to-blog https://arxiv.org/abs/2609.05364
```

In Codex, use the skill after selecting or mentioning the plugin:

```text
/paper-to-blog /path/to/paper.pdf
/paper-to-blog https://arxiv.org/abs/2609.05364
```

You can add an explicit preference after the source, for example: “write for a product manager” or “keep it under 1,000 words.” The plugin returns a complete HTML document by default; request an HTML fragment only when you need to embed it in an existing page.

## What the output guarantees

- Claims, numbers, and qualifications are grounded in the inspected paper.
- Every editorial HTML `<section>` contains exactly three `<p>` elements.
- Informative paper figures are included with actual image pixels, captions, and descriptive `alt` text; any omitted unreadable or redundant figure is disclosed.
- The article states limitations where the paper's evidence is narrower than its broadest claim.

## Updating or removing

Update the marketplace using the client’s plugin manager, then reinstall the plugin. To remove it, use the same manager or uninstall `paper-to-blog@paper-to-blog` from the relevant client.

For platform-specific plugin management details, see the [Codex plugin documentation](https://learn.chatgpt.com/docs/plugins) and [Claude Code marketplace documentation](https://code.claude.com/docs/en/discover-plugins).

