# TenderSignal personal-account migration

Target owner: `jerechulze`  
Repository name: `radaria-licitaciones`

## Why this migration is safe

The repository transfer preserves Git history, issues, pull requests, releases, Actions configuration and repository settings. The old repository address redirects to the transferred repository, but the old GitHub Pages address does not redirect and must be republished under the new owner.

Expected new addresses:

- Repository: `https://github.com/jerechulze/radaria-licitaciones`
- GitHub Pages: `https://jerechulze.github.io/radaria-licitaciones/`

The data and discovery workflows now calculate the publication URL from the current repository owner and name. After transfer, the next successful main-branch run will regenerate canonical opportunity URLs, sitemap, RSS, market brief, distribution copy, `robots.txt` and IndexNow submissions for the personal account.

## Human transfer step

1. Confirm that `jerechulze` does not already own a repository named `radaria-licitaciones` or a fork in the same network.
2. From the current repository, open **Settings**.
3. Scroll to **Danger Zone** and select **Transfer**.
4. Set the new owner to `jerechulze` and keep the repository name `radaria-licitaciones`.
5. Complete GitHub's confirmation prompt.
6. Open the confirmation email or notification in the `jerechulze` account and accept within 24 hours.

Never share passwords, recovery codes, personal access tokens or two-factor authentication codes in chat or repository files.

## Post-transfer checklist

1. In the transferred repository, open **Settings → Pages**.
2. Publish from branch `main` and directory `/ (root)`.
3. Confirm that **Pages build and deployment** succeeds.
4. Run **Update TED live data** manually once if a push does not start it automatically.
5. Confirm that `data/live/generated-manifest.json`, `sitemap.xml`, `feed.xml`, `robots.txt` and `data/live/brief-manifest.json` use `https://jerechulze.github.io/radaria-licitaciones`.
6. Run **Notify IndexNow** after the regenerated manifests are committed.
7. Test the homepage, filters, founder application and one generated opportunity page.
8. Connect the `jerechulze` GitHub account to ChatGPT before further repository writes.
9. Remove the institutional account as a collaborator after the personal account and workflows are confirmed working.

## Rollback boundary

Do not delete or recreate a repository at the old location. GitHub uses that location to redirect repository traffic to the transferred project, and recreating it can permanently remove the redirect.
