# 0003. Run the daily check on GitHub Actions

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

The check needs to run once a day at 8am UK time, for free, with somewhere to keep secrets and
somewhere to write results.

## Options considered

- **AWS Lambda + EventBridge**: reliable timing and good portfolio material, but needs an AWS
  account, IAM, and somewhere to store data other than git.
- **A PC or Raspberry Pi with cron**: free, but only runs when the machine is on.
- **Claude routine only**: no code to maintain, but uses subscription limits on every run, and
  results vary from run to run.
- **GitHub Actions scheduled workflow**: free for public repos, secrets built in, and it can
  commit straight back to the repo where the data lives.

## Decision

GitHub Actions, `.github/workflows/check.yml`.

**Updated 2026-11-08.** The first version ran at 07:00 and 08:00 UTC and only went ahead if it
was exactly 8am in London. In practice GitHub started every scheduled run 6 to 10 hours late
(around 2pm to 6pm), so every run was skipped and no digest was ever posted. Now:

- The workflow is scheduled several times a day at odd minutes (:41), since on-the-hour
  schedules are the most delayed.
- `price-checker due` lets a scheduled run go ahead if it's after 8am UK time and nothing has
  been posted today. Posting records the UK date in `data/digest_state.json`, so later runs skip.
- For an exact 8am, an external free scheduler (cron-job.org) calls the workflow's
  `workflow_dispatch` endpoint at 08:00 Europe/London. Dispatched runs always go ahead.

## Consequences

- Without the external trigger, the digest arrives on the first scheduled run after 8am, which
  may be the afternoon. With it, it arrives at 8am.
- The external trigger needs a fine-grained GitHub token with Actions write access to this repo
  only, stored in cron-job.org. If that token leaks, someone can trigger runs but not change code.
- GitHub turns off schedules in repos with no activity for 60 days. The daily data commits
  should count as activity.
- Requests come from GitHub's data-centre IP addresses, which some shops block more readily than
  a home connection. Blocked pages show under "Couldn't check" and the Claude routine covers them.

**Revisit when:** timing needs to be exact, checks need to run more than a few times a day, or
there are other users (the workflow runs for one watchlist only).
