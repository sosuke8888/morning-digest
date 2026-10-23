#!/usr/bin/env python3
import feedparser
import anthropic
import datetime
import html as html_module
import os
from pathlib import Path

FEEDS = {
    "📈 米国株・市場動向": [
        ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
        ("MarketWatch Top Stories", "http://feeds.marketwatch.com/marketwatch/topstories"),
        ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"),
    ],
    "💻 テクノロジー・IT": [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("Hacker News", "https://hnrss.org/frontpage"),
    ],
    "🏢 ビジネス・経営": [
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ],
    "🌍 国内・海外経済": [
        ("Reuters Top News", "https://feeds.reuters.com/reuters/topNews"),
        ("NHK World", "https://www3.nhk.or.jp/nhkworld/en/news/feeds/"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ],
}


def fetch_articles(feed_url: str, max_items: int = 5) -> list[dict]:
    try:
        feed = feedparser.parse(feed_url, request_headers={"User-Agent": "MorningDigest/1.0"})
        articles = []
        for entry in feed.entries[:max_items]:
            summary = entry.get("summary", entry.get("description", ""))
            # HTMLタグを除去
            import re
            summary = re.sub(r"<[^>]+>", "", summary)[:600]
            articles.append({
                "title": entry.get("title", ""),
                "summary": summary,
                "link": entry.get("link", ""),
            })
        return articles
    except Exception as e:
        print(f"  [エラー] {feed_url}: {e}")
        return []


def summarize_with_claude(category: str, articles: list[dict]) -> str:
    if not articles:
        return "本日は該当ニュースを取得できませんでした。"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    articles_text = "\n\n".join([
        f"【{a['title']}】\n{a['summary']}"
        for a in articles[:8]
    ])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": f"""以下の英語ニュース記事を、日本語でビジネスパーソン向けに要約してください。

カテゴリ: {category}

重要なニュースを3〜5件選び、それぞれ以下のフォーマットで簡潔にまとめてください。
仕事・投資判断に役立つ視点を含めてください。

フォーマット:
▶ ニュースタイトル（日本語）
要点を2〜3行で。重要な数字や動向を含める。

---

記事:
{articles_text}
"""
        }]
    )
    return message.content[0].text


def generate_html(summaries: dict[str, str], date_str: str) -> str:
    sections_html = ""
    for category, summary in summaries.items():
        lines = summary.split("\n")
        formatted_lines = []
        for line in lines:
            line = html_module.escape(line)
            if line.startswith("▶"):
                formatted_lines.append(f'<p class="news-title">{line}</p>')
            elif line.strip() == "---":
                formatted_lines.append('<hr class="divider">')
            elif line.strip():
                formatted_lines.append(f'<p class="news-body">{line}</p>')
        sections_html += f"""
    <section class="card">
      <h2>{category}</h2>
      <div class="content">{"".join(formatted_lines)}</div>
    </section>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>Morning Digest {date_str}</title>
  <style>
    :root {{
      --bg: #f2f2f7;
      --card: #ffffff;
      --text: #1c1c1e;
      --sub: #6c6c70;
      --accent: #007aff;
      --border: rgba(60,60,67,0.12);
      --divider: rgba(60,60,67,0.08);
      --title-color: #007aff;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #000000;
        --card: #1c1c1e;
        --text: #ffffff;
        --sub: #8e8e93;
        --accent: #0a84ff;
        --border: rgba(255,255,255,0.08);
        --divider: rgba(255,255,255,0.06);
        --title-color: #0a84ff;
      }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 0 0 40px;
      max-width: 640px;
      margin: 0 auto;
      font-size: 15px;
      line-height: 1.65;
    }}
    header {{
      padding: 52px 20px 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 16px;
      background: var(--card);
    }}
    header h1 {{
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}
    header .date {{
      color: var(--sub);
      font-size: 13px;
      margin-top: 5px;
      letter-spacing: 0.2px;
    }}
    .cards {{ padding: 0 12px; }}
    .card {{
      background: var(--card);
      border-radius: 14px;
      padding: 18px 16px;
      margin-bottom: 12px;
      border: 1px solid var(--border);
    }}
    .card h2 {{
      font-size: 14px;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 14px;
      letter-spacing: 0.1px;
    }}
    .news-title {{
      font-size: 14px;
      font-weight: 700;
      color: var(--text);
      margin: 14px 0 4px;
      line-height: 1.4;
    }}
    .news-title:first-child {{ margin-top: 0; }}
    .news-body {{
      font-size: 13.5px;
      color: var(--sub);
      line-height: 1.65;
      margin-bottom: 2px;
    }}
    hr.divider {{
      border: none;
      border-top: 1px solid var(--divider);
      margin: 14px 0;
    }}
    footer {{
      text-align: center;
      font-size: 11px;
      color: var(--sub);
      padding-top: 8px;
      letter-spacing: 0.3px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>📰 Morning Digest</h1>
    <div class="date">{date_str}</div>
  </header>
  <div class="cards">
{sections_html}
    <footer>Powered by Claude · {date_str}</footer>
  </div>
</body>
</html>"""


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    date_str = now.strftime("%Y年%-m月%-d日 (%a)")

    print(f"📰 Morning Digest 生成開始: {date_str}\n")

    summaries = {}
    for category, feeds in FEEDS.items():
        print(f"{category} を取得中...")
        all_articles = []
        for feed_name, feed_url in feeds:
            articles = fetch_articles(feed_url, max_items=4)
            all_articles.extend(articles)
            print(f"  {feed_name}: {len(articles)} 件取得")
        summary = summarize_with_claude(category, all_articles)
        summaries[category] = summary
        print(f"  → 要約完了\n")

    html_content = generate_html(summaries, date_str)
    Path("index.html").write_text(html_content, encoding="utf-8")
    print(f"✅ index.html を生成しました ({len(html_content):,} bytes)")


if __name__ == "__main__":
    main()
