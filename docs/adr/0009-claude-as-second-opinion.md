# 0009. Use Claude as a second opinion, not the main checker

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Claude can search the whole web, read pages that publish no structured data, and judge whether
two listings are the same product. But its results vary between runs, it uses subscription
limits, and it can occasionally misread a page. The script is the opposite: consistent and free,
but blind to anything it can't parse.

## Options considered

- **Script only**: misses Amazon, Argos and any site without structured data.
- **Claude only**: broad, but nothing to compare it against, and a bad run means a bad digest.
- **Script first, Claude checks it**: each covers the other's blind spots.

## Decision

A Claude routine runs at 7:15 (before the 8am script) on the subscription and:

1. Searches each item by name, including Amazon and Argos.
2. Compares what it sees with the script's previous results and records a finding: `cheaper`,
   `confirmed`, `mismatch`, or a general `note`.
3. Probes any new product pages it finds and adds readable ones to the watchlist, so the script's
   coverage grows over time.
4. Writes `data/claude_findings.json` and pushes it. It never posts to Discord itself.

The 8am digest shows Claude's findings in their own section. Claude never overrides the script's
"best price".

## Consequences

- Claude's prices are labelled as Claude's, so a misread can't silently become the headline.
- One place posts to Discord and one format is used, so the message stays consistent.
- Claude checks the previous day's script results, so a price that changed overnight can show
  as a mismatch. The digest shows both prices, so it's visible rather than hidden.
- If the routine fails or doesn't run, the digest still goes out without the Claude section.

**Revisit when:** the routine is consistently right about a source the script can't read. That's
a sign to add a proper source for it.
