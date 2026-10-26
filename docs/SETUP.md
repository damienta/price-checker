# Setup guide

About 20 minutes for the core, plus 10 minutes each for the optional extras.

## 1. Merge the pull requests

Merge them in order. Each one builds on the previous:

1. **Core checker**: watchlist, product pages, PriceSpy and PriceRunner
2. **More sources**: HotUKDeals, eBay, Google Shopping
3. **Digest and schedule**: Discord message, 8am workflow, Claude routine

## 2. Make the Discord webhook

1. In Discord, create a server just for this (**+** in the server list → **Create My Own** →
   **For me and my friends**), or use one you already have.
2. Create a text channel, e.g. `#prices`.
3. Click the ⚙️ next to the channel → **Integrations** → **Webhooks** → **New Webhook**.
4. Name it "Price Checker", then **Copy Webhook URL**.

Treat that URL like a password: anyone who has it can post to your channel.

## 3. Add it to GitHub as a secret

1. Go to <https://github.com/damienta/price-checker/settings/secrets/actions>.
2. **New repository secret**: name `DISCORD_WEBHOOK_URL`, value is the URL you copied.

## 4. Test the morning run

1. Go to <https://github.com/damienta/price-checker/actions/workflows/check.yml>.
2. **Run workflow** → **Run workflow**.
3. Within a minute or two, Discord should say your watchlist is empty. That means it works.

If the "Save prices to the repo" step fails with a permissions error, go to
**Settings → Actions → General → Workflow permissions**, choose **Read and write permissions**
and save.

From now on it runs by itself at 8am UK time. GitHub sometimes starts scheduled runs 10 to 30
minutes late.

## 5. Add your first items

On your PC:

```bash
cd C:\Coding\price-checker
git checkout main
git pull
```

Open Claude Code in `C:\Coding\price-checker` and say what you want, for example:

> Track the Sony WH-1000XM5 in black, alert me under £250.
> Also track this: https://www.currys.co.uk/products/...

Claude follows the instructions in `CLAUDE.md`: it finds the PriceSpy and PriceRunner pages,
checks each link with `price-checker probe`, picks search words and a HotUKDeals tag, runs a
first check, then commits and pushes. Tomorrow's 8am digest will include it.

To run the commands yourself you need [uv](https://docs.astral.sh/uv/) installed, then:

```bash
uv sync
uv run price-checker list
```

## 6. Set up the Claude routine

Follow [claude-routine.md](claude-routine.md). It runs at 7:15 on your Claude subscription,
searches each item by name (including Amazon and Argos), double-checks the script's prices and
adds new links it finds. Its results show up in the 8am digest under 🔍 Claude.

## 7. Optional: eBay (free)

1. Sign up at <https://developer.ebay.com> with your eBay account.
2. **Hi, <name>** → **Application Keysets** → create a **Production** keyset.
   (eBay may ask you to fill in the "marketplace account deletion" notice. Choosing the
   exemption "I do not persist eBay data" is accurate here: the script keeps prices, not
   eBay user data.)
3. Add two repository secrets: `EBAY_CLIENT_ID` (the **App ID**) and `EBAY_CLIENT_SECRET`
   (the **Cert ID**).

## 8. Optional: Google Shopping (free, 250 searches a month)

1. Sign up at <https://serpapi.com> and copy your API key from the dashboard.
2. Add a repository secret `SERPAPI_KEY`.

The script spends at most about 8 searches a day, rotating through your items, and stops for
the month before reaching the free limit. To change the budget, add a repository **variable**
(same settings page, **Variables** tab) called `SERPAPI_MONTHLY_BUDGET`.

## Good to know

- **Amazon and Argos** block scripts, so they're covered by the Claude routine rather than the
  8am check. For alerts on Amazon specifically, a free [camelcamelcamel](https://uk.camelcamelcamel.com)
  alert works well alongside this.
- **"Couldn't check" lines** mean a site blocked the request or the page changed. If one keeps
  appearing, ask Claude to replace that link.
- **Public repo:** anyone can see what you're tracking and the prices. Make the repo private if
  that bothers you. Actions stays free for private repos at this usage (about 2 minutes a day
  out of 2,000 free minutes a month).
- **If the 8am run stops:** GitHub turns off scheduled workflows in repos with no activity for
  60 days. The daily data commits should count as activity, but if it ever stops, re-enable it
  in the Actions tab.
