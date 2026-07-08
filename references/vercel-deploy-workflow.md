# Vercel Deploy Workflow for VOC Reports

When the user asks to deploy the generated HTML report as a public URL, you push it as a static site to Vercel.

## Prerequisites

- Vercel CLI installed: `npm install -g vercel`
- Vercel token available (base64-encoded in deploy scripts)
- `index.html` + `vercel.json` in the same directory

## Standard Deploy Script

```python
import base64, subprocess, os, shutil, re

# Get token (usually base64-encoded from deploy_smart_ring.py or memory)
T = base64.b64decode('<base64-token>').decode()
V = os.path.expanduser('~/.npm-global/bin/vercel')
D = '/tmp/voc-deploy'

# Prepare directory
os.makedirs(D, exist_ok=True)
shutil.copy2('voc_report.html', D + '/index.html')
with open(D + '/vercel.json', 'w') as f:
    f.write('{"version":2}')

# Clean old .vercel cache
c = os.path.join(D, '.vercel')
if os.path.exists(c):
    shutil.rmtree(c)

# Deploy
e = os.environ.copy()
e['PATH'] = os.path.expanduser('~/.npm-global/bin') + ':' + e['PATH']

r = subprocess.run([V, 'deploy', '--token', T, '--prod', '--yes', '--force'],
    capture_output=True, text=True, cwd=D, env=e, timeout=90)

url = re.search(r'https://[a-z0-9-]+\\.vercel\\.app', r.stdout)
print(url.group(0) if url else 'Deploy URL not found')
```

## Quick One-Liner (when Vercel is already linked)

```bash
mkdir -p /tmp/voc-deploy && \
cp data/voc/voc_report_full.html /tmp/voc-deploy/index.html && \
echo '{"version":2}' > /tmp/voc-deploy/vercel.json && \
vercel deploy --prod --yes --force --cwd /tmp/voc-deploy
```

## Pitfalls

1. **Token expiry**: Vercel tokens have no expiry by default, but if deployment fails with 401, the token needs to be regenerated. Token is a `vcp_...` string, typically base64-encoded in deploy scripts.

2. **New project vs existing**: The first deploy creates a new project and assigns a random URL. Subsequent deploys with `--prod` update the same URL. To force a new project, delete `.vercel/` cache directory before deploying.

3. **Vercel.json is required**: Without it, Vercel may try to build the HTML as a Node.js app and fail. The minimal `{"version":2}` tells Vercel to treat it as static.

4. **Project linking**: If the CLI prompts for "Set up and deploy?" use `--yes --force` to skip. If a previous `.vercel/project.json` exists from a different project, clear `.vercel/` first.

5. **Domain propagation**: After a successful deploy, the URL is immediately live. No CDN warmup needed for static HTML.

6. **Size limit**: Vercel's free tier has a 50MB file limit. The VOC HTML report is typically ~100KB, well within limits.
