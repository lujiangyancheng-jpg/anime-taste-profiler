# Anime Taste Profiler / 动画口味画像

Anime Taste Profiler is a small Streamlit app that analyzes a user's completed anime ratings and turns them into a readable taste profile.

这是一个小型 Streamlit 应用，用来分析用户的动画评分习惯，并生成可读的“动画口味画像”。

## What It Does / 功能

- Supports AniList and Bangumi public anime lists.
- 支持读取 AniList 和 Bangumi 的公开动画收藏。
- Supports English and Simplified Chinese UI/report output.
- 支持英文和简体中文界面与报告。
- Uses only completed/watched anime with a score greater than zero.
- 只分析已完成/看过且评分大于 0 的动画。
- Normalizes scores to a 10-point scale.
- 将不同来源的评分统一到 10 分制。
- Computes rating stats, score distribution, liked/disliked genres and tags, scoring style, and taste archetype.
- 计算评分统计、评分分布、偏好/低偏好类型与标签、评分风格和口味原型。
- Generates a natural language taste report.
- 生成自然语言口味报告。
- Includes a simple optional recommendation section.
- 附带一个简单的候选推荐模块。

## Why It Is Not Just A Recommender / 为什么不是普通推荐器

Most recommenders answer "what should I watch next?" This app starts with "what does my rating history say about me?"

普通推荐器主要回答“下一部看什么”。这个应用更关注“我的评分历史说明了什么”：你是否严格打分、哪些类型或标签经常高于你的个人均分、哪些元素容易被你低评，以及你更接近哪种观看口味。

The recommendation section is intentionally simple and secondary. The profile report is the main output.

推荐只是附加功能，核心输出是画像报告。

## Data Sources / 数据来源

### AniList

AniList uses the GraphQL API and `MediaListCollection`. The app analyzes completed anime entries with a positive score.

AniList 使用 GraphQL API 的 `MediaListCollection`，分析已完成且已评分的动画。

### Bangumi

Bangumi uses the public v0 API endpoint:

```text
/v0/users/{username}/collections?subject_type=2&type=2
```

The app analyzes public watched anime collections with a positive score. Bangumi does not provide the same genre field as AniList, so the app uses Bangumi subject tags as the main taste signal and maps common tags such as 科幻, 恋爱, 日常, 悬疑, 动作, 奇幻, and 治愈 into genre-like buckets.

Bangumi 使用公开 v0 API。应用会读取公开的“看过”动画收藏并分析已评分条目。由于 Bangumi 没有 AniList 那样的独立 genre 字段，应用会使用 Bangumi 条目标签作为主要口味信号，并把常见标签映射成类型信号。

## Project Structure / 项目结构

```text
anime-taste-profiler/
  app.py
  anilist_api.py
  bangumi_api.py
  analyzer.py
  profile_generator.py
  recommender.py
  i18n.py
  requirements.txt
  README.md
```

## How To Run / 运行方式

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit, choose a language and data source, enter a public username, and click the analyze button.

启动后，在页面里选择语言和数据来源，输入公开用户名，再点击分析按钮。

For a persistent online version, see [DEPLOYMENT.md](DEPLOYMENT.md). For a local one-click launcher on Windows, double-click `start_app.bat`.

如果想要以后直接通过固定网页打开，请看 [DEPLOYMENT.md](DEPLOYMENT.md)。如果只是想在本机以后快速再打开，可以双击 `start_app.bat`。

## Notes / 注意事项

- No AniList or Bangumi login is required.
- 不需要 AniList 或 Bangumi 登录。
- The app does not permanently store user data.
- 应用不会永久保存用户数据。
- The anime-flavored report voice uses an internal phrase library. It does not bulk scrape or reuse comment-section text from anime websites.
- 二次元文风使用的是内置语感词库，不会批量抓取或复用各动画网站评论区原文。
- Streamlit caching is used to avoid repeated API calls during a session.
- 使用 Streamlit 缓存减少同一会话中的重复请求。
- If the user has fewer than 10 scored completed anime, the app still runs but shows a reliability warning.
- 如果已评分完成动画少于 10 部，应用仍会运行，但会显示可靠性提醒。

## Future Improvements / 后续改进

- Compare two users' taste profiles.
- 对比两个用户的口味画像。
- Generate shareable taste profile cards.
- 生成可分享的口味卡片。
- Analyze dropped anime if available.
- 分析弃番数据。
- Add MyAnimeList support.
- 增加 MyAnimeList 支持。
- Add clustering or embeddings.
- 引入聚类或向量表示。
- Improve recommendations using collaborative filtering.
- 用协同过滤改进推荐。
- Export reports as Markdown or PDF.
- 导出 Markdown 或 PDF 报告。
