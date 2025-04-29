import os, subprocess, json, glob, frontmatter, requests, markdown
# 先頭で
from openai import OpenAI
client = OpenAI()  

def changed_files():
    base = os.getenv('GITHUB_SHA')
    prev = subprocess.check_output(['git','rev-parse',f'{base}^']).decode().strip()
    diff = subprocess.check_output(['git','diff','--name-only',prev,base]).decode().splitlines()
    return [f for f in diff if f.startswith('docs/logs/') and f.endswith('.md')]

 # 環境変数 OPENAI_API_KEY を自動読込

def summarize(md_text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",      # または gpt-4o 等
        messages=[
            {"role": "system", "content": "あなたはプロの技術ライターです。"},
            {"role": "user", "content": f"次の Markdown を初心者にも分かる7行以内の箇条書きで要約してください：\n\n{md_text}"}
        ],
        max_tokens=256,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()

def post_slack(title, summary, url):
    payload = {"text": f"*{title}* の3分サマリ\n{summary}\n<{url}|全文はこちら>"}
    requests.post(os.environ['SLACK_WEBHOOK_URL'], json=payload, timeout=10)

for path in changed_files():
    post = frontmatter.load(path)
    summary = summarize(post.content)
    summary_path = path.replace('logs', 'summaries')
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w') as f: f.write(summary)
    html_url = os.environ.get('GITHUB_SERVER_URL') + '/' + os.environ.get('GITHUB_REPOSITORY') + '/blob/gh-pages/' + summary_path.replace('docs/', '')
    post_slack(post.get('title', path), summary, html_url)
