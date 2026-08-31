# EdgeOne CLI Local Deployment

Use this reference only when the user asks to deploy a generated travel page or agrees to publish after the HTML is created.

## Default Flow

1. Generate and validate the travel HTML first.
2. Ask whether to publish to EdgeOne Pages if the user did not already request deployment.
3. Deploy locally with EdgeOne CLI. GitHub is not required.
4. Return the full EdgeOne preview token URL only after the CLI deployment succeeds.
   - Prefer the exact `EDGEONE_DEPLOY_URL=...` value from the CLI output.
   - Keep the complete query string, including `eo_token` and `eo_time`.
   - Do not shorten it to the root `edgeone.cool` domain, because direct root access can return `401 UNAUTHORIZED`.

## Commands

Check CLI:

```bash
edgeone -v
```

Install CLI when missing:

```bash
npm install -g edgeone
```

Login when needed:

```bash
edgeone login
```

Deploy with the bundled script:

```bash
python scripts/deploy_edgeone.py --html output.html --project-name destination-travel
```

Deploy manually if the script is unavailable:

```bash
mkdir edgeone-dist
copy output.html edgeone-dist\index.html
edgeone pages deploy edgeone-dist -n destination-travel -e production
```

## User Guidance

If the CLI is missing, tell the user:

```text
需要先安装 EdgeOne CLI：npm install -g edgeone
安装后我可以继续用本地文件直接发布，不需要 GitHub。
```

If login is missing or expired, tell the user:

```text
需要先登录 EdgeOne：edgeone login
请在弹出的浏览器里完成登录，然后告诉我继续。
```

If deployment succeeds, return the full preview token URL and local HTML path. Explain that the token URL is shareable for preview but may expire; if visitors see `401 UNAUTHORIZED`, generate a new Preview link in the EdgeOne console or deploy again to get a fresh token URL.

If deployment fails, summarize the CLI error and keep the local HTML path available.

## Notes

- Single-page travel guides should be copied to `index.html` before deployment so the EdgeOne project root opens directly.
- Use production by default. EdgeOne may still return a preview-token URL for access; always share the full URL including `eo_token` and `eo_time`.
- Use `--env preview` only when the user asks for a preview environment deployment.
- Do not use GitHub Actions or Git repository import unless the user explicitly asks for that deployment mode.
