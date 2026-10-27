# Architecture decision records

Short notes on why the project is built the way it is, so later changes (a frontend, other
users, a database) can be made knowing what each choice was trading off.

| # | Decision | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-files-in-git-not-a-database.md) | Store state as files in git, not a database | Accepted |
| [0003](0003-github-actions-for-scheduling.md) | Run the daily check on GitHub Actions | Accepted |
| [0004](0004-discord-webhook-for-alerts.md) | Send alerts through a Discord webhook | Accepted |
| [0005](0005-structured-data-over-html-scraping.md) | Read prices from structured data, not page HTML | Accepted |
| [0006](0006-respect-robots-and-identify-honestly.md) | Respect robots.txt and identify the bot honestly | Accepted |
| [0007](0007-comparison-sites-as-primary-sources.md) | Use price comparison sites as the main sources | Accepted |
| [0008](0008-optional-api-sources-behind-keys.md) | Keep paid-tier APIs optional and budgeted | Accepted |
| [0009](0009-claude-as-second-opinion.md) | Use Claude as a second opinion, not the main checker | Accepted |
| [0010](0010-how-prices-are-verified.md) | How prices are verified before you're alerted | Accepted |

## Adding one

Copy [template.md](template.md) to the next number, e.g. `0011-short-title.md`, and add it to
the table. Write one when a choice would be expensive to reverse, or when someone could
reasonably ask "why didn't you just...?". If a later decision replaces an earlier one, mark the
old one `Superseded by 00NN` rather than deleting it.
