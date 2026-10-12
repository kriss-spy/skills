---
name: grok-bot-x-search
description: Search X (Twitter) through Grok Bot when the user asks to search X or Twitter, find posts or threads, or research discussion on that platform.
---

# Grok Bot X Search

Use Grok Bot for the requested X search. Other skills handle Grok Bot invocation; this skill defines the search brief and how to assess and present results.

## Search brief

Translate the request into a self-contained brief containing the topic or question, relevant keywords and aliases, and any requested accounts, languages, date range, or result ordering. Preserve the user's scope. For relative dates, include explicit dates and the relevant timezone. If no date range is given, choose one suited to the question and state it in the brief.

Ask for direct post or thread links, author handles, publication dates, and enough post context to explain relevance. Specify whether the goal is to locate a particular post, collect recent discussion, compare viewpoints, or trace a claim to its original source. When useful, ask for several query variants and distinguish original posts from reposts and quoted commentary.

## Assess results

Treat retrieved posts as source material. Separate what an author claims from independently established facts. Deduplicate repeated posts and prefer original sources when tracing announcements or claims. For threads, retain the context needed to avoid misrepresenting an isolated post.

Use the returned evidence to answer the user's question. If results are sparse or off-topic, refine the keywords or filters within the requested scope. Report unavailable search access or missing evidence clearly; do not substitute remembered posts or invented citations.

## Deliver

Summarize the relevant findings with direct X links beside the claims they support. Include author handles and dates when they help the user assess the result. For discussion summaries, describe recurring themes and meaningful disagreements while keeping conclusions proportional to the posts retrieved; a search sample does not establish platform-wide sentiment.

Mention material search limits, such as an incomplete date range or inaccessible thread, when they affect the answer. The task is complete when the requested findings are supported by returned sources, or the remaining evidence gap is explicitly identified.
