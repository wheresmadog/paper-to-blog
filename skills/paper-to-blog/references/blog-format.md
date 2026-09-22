# Blog format for HTML output

Use this as the default outline. Rename or merge sections when the paper's genre calls for it.

## Document shell

Return a complete document unless the user requests a fragment:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reader-facing title</title>
    <meta name="description" content="Short source-faithful summary">
  </head>
  <body>
    <main>
      <article>
        <!-- article content -->
      </article>
    </main>
  </body>
</html>
```

Prefer a short, descriptive `<h1>` that adds context without changing the paper's claim. Keep the original title in the attribution line.

## Section paragraph contract

Every editorial `<section>` must contain exactly three `<p>` elements. Use the three paragraphs to establish the point, explain or support it, and then state its implication, qualification, or transition. This applies to the abstract and every named article section below. Figures, asides, tables, and code blocks may supplement the three paragraphs but cannot replace them.

## Figures

Include every informative figure from the paper unless the user requests a selection. Omit only decorative, redundant, or unreadable figures, and disclose omissions in the source note. Put each figure beside the section that explains it. Preserve the original figure number and caption meaning, and add accurate descriptive alternative text.

For a standalone HTML document, embed the extracted image as a data URL when practical:

```html
<figure>
  <img src="data:image/png;base64,..." alt="Descriptive summary of the figure">
  <figcaption><strong>Figure 1.</strong> Original caption, with a brief explanatory gloss if useful.</figcaption>
</figure>
```

If the host supports file artifacts, an HTML file may instead reference co-located extracted images with relative paths such as `assets/figure-1.png`. Never replace the actual figure with a newly invented illustration unless the user explicitly asks for a redraw.

## Abstract

Write exactly three short paragraphs answering:

- What problem does the paper address?
- What is the central idea or contribution?
- What is the strongest reported result or takeaway?

The abstract should stand alone and should not contain a result that appears nowhere in the paper. Place it in a `<section>` with an `<h2>Abstract</h2>` and exactly three `<p>` elements.

## The problem

Open with a concrete situation, failure mode, or question in a `<section>` with exactly three `<p>` elements. Explain why existing approaches are insufficient and define only the background needed to follow the rest.

## The big idea

State the contribution in plain language across exactly three `<p>` elements. Give the reader a mental model, then name the paper's method. If useful, include a compact `<aside>` callout labeled “In one sentence.”

## How it works

Walk through the method in exactly three `<p>` elements, in the order a reader encounters it. Use a small example, `<figure>`, diagram description, or `<pre><code>` block only when it clarifies the mechanism. Connect each component to the problem it addresses.

## What the paper found

Describe the evaluation or proof in exactly three `<p>` elements. Cover the setup, comparison, and key outcome, then explain what the result means. Separate direct observations from interpretation. For a theory paper, replace this with “What is proved” and state assumptions and scope. Use `<table>` only when a tabular comparison materially improves clarity.

## Tradeoffs and limits

Name the most consequential assumptions, costs, missing baselines, restricted evaluation settings, or unresolved failure modes in exactly three `<p>` elements. A limitation should be specific enough that a reader knows what future evidence would change the conclusion. Put this in a section headed “Tradeoffs and limits.”

## Why it matters

Give the narrow implication supported by the paper, then one cautious broader implication, in exactly three `<p>` elements. End with an open question or a practical next step rather than a generic claim that the work is “promising.”

## Source note

Place this in a `<footer>`:

```html
<footer>
  <p>Source: Original Paper Title, version/date, <a href="...">canonical URL</a> or local PDF filename.</p>
</footer>
```
