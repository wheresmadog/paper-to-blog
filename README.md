# Paper to Blog

Turn a research paper into a reader-friendly blog article, a visual conference poster, or a single explainer image. The plugin includes three skills: `paper-to-blog`, `paper-to-poster`, and `paper-to-image`. All accept a local PDF or an `arxiv.org` paper URL, preserve the paper's version, and explain the evidence and limits with source figures.

The blog skill returns standalone HTML by default. Every editorial section has exactly three paragraphs; figures contain the source pixels, descriptive alternative text, and a faithful caption. The poster skill uses concise text and selected visuals in a printable layout, with an editable HTML source and PDF export when available.

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

In Codex Desktop, start a new chat and select or `@`-mention **Paper to Blog** if you want to force use of the plugin. Codex can also select the appropriate installed skill automatically for a request that clearly asks for a blog article, conference poster, or paper explainer image.

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

You can add an explicit preference after the source, for example: “write for a product manager” or “keep it under 1,000 words.” The blog skill returns a complete HTML document by default; request an HTML fragment only when you need to embed it in an existing page.

### Create a conference poster

In Codex, select or mention the plugin and invoke:

```text
/paper-to-poster /path/to/paper.pdf
/paper-to-poster https://arxiv.org/abs/2609.05364
```

In Claude Code, use the plugin namespace:

```text
/paper-to-blog:paper-to-poster https://arxiv.org/abs/2609.05364
```

Add a venue, year, template, dimensions, or format when relevant, for example: “make a wide landscape poster for an AI research audience.” For NeurIPS, ICML, or another named conference, the skill checks supplied or current official poster requirements before claiming venue compliance. Its generic default is wide 2:1 landscape (1200 × 600 mm), not a conference-specific requirement.

The poster uses a compact header and a two-row grid of visual panels with blue section bars, following the bundled conference-poster template. It includes the problem, contribution, method, strongest evidence, and visible limitations. It selects informative figures rather than reproducing all of them, and uses concise text rather than the blog skill's three-paragraph rule. It delivers editable, printable HTML with local assets and a single-page PDF when a suitable exporter is available; unavailable export or verification is disclosed.

### Create a single explainer image

```text
/paper-to-image https://arxiv.org/abs/2610.05538
```

In clients that namespace plugin skills:

```text
/paper-to-blog:paper-to-image https://arxiv.org/abs/2610.05538
```

The default is a dark 1080 × 1920 portrait graphic with a large headline, one connected flowchart explaining the method’s inputs, operations, and outputs. It omits takeaway cards and detailed experimental results; necessary branches and feedback loops stay within the same chart. You can specify a different size, style, language, or output destination.

The skill returns `image.png`, editable HTML or SVG, and a claim-to-source record under `output/<paper-slug>-image/`. It reads the full paper, preserves the source version, and inspects the exported image before delivery. This is a concise visual explanation of one central idea, rather than a conference poster.

## Blog output requirements

- Claims, numbers, and qualifications are grounded in the inspected paper.
- Every editorial HTML `<section>` contains exactly three `<p>` elements.
- Informative paper figures are included with actual image pixels, captions, and descriptive `alt` text; any omitted unreadable or redundant figure is disclosed.
- The article states limitations where the paper's evidence is narrower than its broadest claim.

## Poster output requirements

- Claims, numbers, author information, and source version are grounded in the inspected paper.
- Selected figures preserve source evidence, labels, and caption meaning.
- The visual hierarchy supports quick scanning and discussion, with readable text and visible limitations.
- The skill verifies the final layout, page size, and one-page print output when tools are available, and reports any unverified export or venue requirements.

## Updating or removing

Update the marketplace using the client’s plugin manager, then reinstall the plugin. To remove it, use the same manager or uninstall `paper-to-blog@paper-to-blog` from the relevant client.

For platform-specific plugin management details, see the [Codex plugin documentation](https://learn.chatgpt.com/docs/plugins) and [Claude Code marketplace documentation](https://code.claude.com/docs/en/discover-plugins).
