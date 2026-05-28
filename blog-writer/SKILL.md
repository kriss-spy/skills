---
name: blog-writer
description: Writes and structures long-form blog posts, creates tutorial outlines. Use when the user asks to write a blog post, article, how-to guide, tutorial, technical writeup, thought leadership piece, or long-form content.
---

# Blog Post Writing Skill

## Research First (Required)

**Before writing any blog post, you MUST delegate research:**

1. Use subagents to explore the topic
2. After research completes, read the findings file before writing

## Blog Post Structure

Every blog post should follow this structure:

### 1. Hook (Opening)

- Start with a compelling question, statistic, or statement
- Make the reader want to continue
- Keep it to 2-3 sentences

### 2. Context (The Problem)

- Explain why this topic matters
- Describe the problem or opportunity
- Connect to the reader's experience

### 3. Main Content (The Solution)

- Break into 3-5 main sections with H2 headers
- Each section covers one key point
- Include code examples, diagrams, or screenshots where helpful
- Use bullet points for lists

### 4. Practical Application

- Show how to apply the concepts
- Include step-by-step instructions if applicable
- Provide code snippets or templates

### 5. Conclusion & CTA

- Summarize key takeaways (3 bullets max)
- End with a clear call-to-action
- Link to related resources

## Images & Visuals (Required)

Proper images significantly improve readability and engagement. Every blog post MUST include relevant images embedded at suitable locations.

### Image Strategy

1. **Generate diagrams** for concepts, architectures, workflows, or comparisons using Mermaid syntax or code-based graphics
2. **Gather screenshots** when demonstrating UI, tools, or step-by-step processes
3. **Create visual summaries** (tables, charts, infographics) for data-heavy sections
4. **Use code output visuals** (terminal output, rendered results) where applicable

### Placement Rules

- **Hero image** at the top — a relevant visual that represents the topic
- **One image per major section** (minimum) to break up text walls
- **Before/after visuals** when showing transformations or improvements
- **Diagrams near complex explanations** — don't make readers scroll to find them
- **Screenshots with annotations** (arrows, highlights, callouts) to draw attention

### Image Quality Standards

- All images must have descriptive `alt` text
- Diagrams should use consistent styling and readable fonts
- Screenshots must be cropped to relevant areas only
- Code snippets shown as images should use syntax-highlighted themes
- Prefer vector/SVG diagrams over raster when possible

### Image Sourcing

- Generate diagrams programmatically (Mermaid, Python matplotlib, etc.)
- Use browser automation (`agent-browser` skill) to capture live screenshots
- Create comparison tables as formatted markdown or images
- Never use placeholder images or broken links

### Math & Formula Visualizations

- **Inline and block LaTeX** — use native markdown LaTeX support (`$...$` and `$$...$$`) for all equations and derivations
- **Python plots only when needed** — use `matplotlib`/`numpy` for function graphs, 3D surfaces, vector fields, or geometric constructions that can't be expressed in LaTeX
- **Label axes and regions** with mathematical notation matching surrounding text

## Quality Checklist

Before finishing:

- [ ] Hook grabs attention in first 2 sentences
- [ ] Each section has a clear purpose
- [ ] Images are embedded at logical breakpoints (not all at the end)
- [ ] Every image has meaningful alt text
- [ ] Diagrams are readable and use consistent styling
- [ ] Screenshots are annotated to highlight key areas
- [ ] Conclusion summarizes key points
- [ ] CTA tells reader what to do next
