# Autmog → ntfy watcher

Checks https://www.autmog.com/collections/currently-available about **every 60 seconds** and
pushes to your ntfy app when:

- a **new product** is posted (tap opens the product page, with photo), and
- a sold-out item becomes **available** (urgent priority — turn off with `NOTIFY_RESTOCK: "false"` in the workflow).

The first run sends one "watcher is running" message and records the current products, so you won't get 149 alerts.

## How the timing works
GitHub starts the job every 5 minutes (its minimum). Each job then checks once a minute for ~4.5 minutes
before the next one takes over. GitHub sometimes starts scheduled jobs late, so expect occasional
gaps of a few minutes.

## Setup (about 5 minutes, free)

1. **ntfy app:** subscribe to a hard-to-guess topic, e.g. `autmog-7f3k9q2x`. Anyone who knows a public ntfy.sh topic name can read it, so don't use something obvious.
2. **GitHub:** create a new **public** repo and upload these files, keeping the folder layout:
   - `monitor.py`
   - `.github/workflows/watch.yml`

   It must be **public**: this runs almost all day, and Actions minutes are unlimited only on public repos (private repos get 2,000/month, which this would use up in a few days). Your ntfy topic stays hidden because it's stored as a secret; the only thing visible is the list of Autmog product titles, which is public anyway.
3. In the repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Name `NTFY_TOPIC`, value = your topic name.
   - (Optional) `NTFY_TOKEN` if you use a protected topic or self-hosted server.
4. **Actions tab → Watch Autmog → Run workflow** to test. You should get the "watcher is running" notification.

That's it — it now runs on its own.

## Tweaks
- Check frequency: change `CHECK_EVERY` (seconds) in the workflow. Please don't go much below 60 — it's a small shop.
- Self-hosted ntfy? Add `NTFY_SERVER: "https://your.server"` under `env:` in the workflow.
- GitHub can pause scheduled workflows after 60 days without repo activity. The bot's commits to `seen.json` usually count, but if alerts go quiet for a long time, check the Actions tab and re-enable.
