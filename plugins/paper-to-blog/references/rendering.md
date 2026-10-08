# Rendering images and posters

Read this guide before rendering or exporting from either `paper-to-image` or `paper-to-poster`. Resolve paths relative to the invoking `SKILL.md`; this guide is bundled within the same plugin package and does not depend on loading the other skill. Keep the invoking skill's layout, editable-source, output-format, and verification requirements.

## Check the environment before execution

Discover available runtimes and renderers through the environment's dependency tools, executable discovery, or installed-package metadata. Do not hard-code browser paths or runtime paths from a particular computer. Select a renderer that is allowed in the current environment and supports the required output format and features.

A Playwright package does not establish that its browsers are installed. Before launching, obtain the executable path from the selected Playwright browser type (for example, `chromium.executablePath()`) and check that the file exists. If selecting an alternative executable explicitly, discover and check that path too. File existence does not prove that execution is permitted or that the browser will start.

## Diagnose failures before retrying

Preserve the launch error, browser/process logs, exit code, and termination signal when available. Use the evidence to choose the next action:

| Evidence | Interpretation and next action |
| --- | --- |
| `Executable doesn't exist` | Treat as a missing browser installation or a path mismatch. Check the installed browser and resolved executable path; do not repeat the same launch. |
| `Target page, context or browser has been closed` | This message alone does not identify the cause. Inspect process termination signals and logs before classifying the failure. |
| On macOS, `SIGABRT` together with `_RegisterApplication` or `___RegisterApplication_block_invoke` | Classify as a crash during application registration. Explain that sandbox or execution-permission restrictions may be involved, without presenting either as a confirmed cause. |

Do not retry the same execution without changing a relevant condition. Retry only when the installation state, execution environment, or renderer has changed in a way that addresses the observed failure. Do not assume `--no-sandbox` removes sandbox restrictions imposed by the host app or tool.

## Choose an allowed alternative

Explore other available renderers that are permitted in the current environment and support the requested format: for example, another browser/export tool, an SVG rasterizer for SVG source, or a PDF renderer with suitable print-CSS support. Check feature support before relying on an alternative; availability alone does not establish faithful output.

Do not bypass permission restrictions. If installation or additional execution permission is needed, follow that environment's approval procedure for the specific action. Do not require advance approval for every execution; proceed with already permitted rendering operations.

Whichever renderer is used, verify the actual output against the invoking skill's requirements: exact image pixel dimensions, font loading and substitution, SVG text and connectors, local assets, clipping and image resolution, and, for print output, physical page dimensions and page count. Inspect the exported PNG or rendered PDF pages for visual fidelity. A successful process exit or a source preview alone does not verify the exported artifact.

## Preserve and report incomplete work

Continue to pursue the requested exports using suitable allowed routes; renderer failure does not make editable source alone the normal completed deliverable. If no suitable permitted renderer works, preserve the editable HTML/SVG and all required local assets in the final package. Report which requested PNG/PDF exports remain incomplete and which checks could not be performed, with the observed failure and any required next step. Distinguish an export that was not produced from one that exists but has not been verified.

Do not claim rendering success or visual verification without inspecting the actual output. Apply the invoking skill's final checks to any completed exports, and disclose the remaining limitations for incomplete ones.
