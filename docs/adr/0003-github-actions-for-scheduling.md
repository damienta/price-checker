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

GitHub Actions, `.github/workflows/check.yml`. GitHub cron is UTC with no daylight saving, so it's
scheduled at both 07:00 and 08:00 UTC and a gate step keeps whichever is 8am in London.

## Consequences

- Scheduled runs can start 10 to 30 minutes late. Fine for a morning digest.
- GitHub turns off schedules in repos with no activity for 60 days. The daily data commits
  should count as activity.
- Requests come from GitHub's data-centre IP addresses, which some shops block more readily than
  a home connection. Blocked pages show under "Couldn't check" and the Claude routine covers them.

**Revisit when:** timing needs to be exact, checks need to run more than a few times a day, or
there are other users (the workflow runs for one watchlist only).
