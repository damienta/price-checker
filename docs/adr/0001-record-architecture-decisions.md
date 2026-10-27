# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

The project starts as a personal tool but is meant to grow: a frontend next, maybe other users
later. Several early choices (files instead of a database, GitHub Actions instead of a cloud
function) are deliberately "good enough for one person" and will need revisiting. Without a
record, it's hard to tell a shortcut that's still fine from one that's now in the way.

## Decision

Keep short ADRs in `docs/adr/`, one per significant decision, using `template.md`. Claude
sessions working in this repo add one when they make a decision of that size (see `CLAUDE.md`).

## Consequences

A few minutes of writing per decision. In return, each decision lists what would make us revisit
it, so growth triggers a reread instead of a rewrite.
