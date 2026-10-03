# -*- coding: utf-8 -*-
"""
awesome-github-star 数据自动更新脚本
每日由 GitHub Actions 触发：拉取 tongtong2011 最新星标数据，
重新生成 README.md（含最新星数/数量/更新日期）和 data.js（导航页数据源）。
"""
import json
import os
import time
import urllib.request
import urllib.parse

OWNER = "tongtong2011"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 分类映射：full_name -> (类别序号)。新增分类时在此登记即可。
CATS = [
 ("video", "🎬", "AI 视频 / 短剧创作", "AI 生成短视频、短剧、动画、分镜的完整创作工具链", [
  "calesthio/OpenMontage", "harry0703/MoneyPrinterTurbo", "chatfire-AI/huobao-drama", "HBAI-Ltd/Toonflow-app",
  "linyqh/NarratoAI", "ArcReel/ArcReel", "eternityspring/shuohao-skills", "zenstory-ai/drama-skills",
  "liangdabiao/Seedance2-Storyboard-Generator", "fogsightai/fogsight", "gnipbao/story-to-handdrawn-video",
  "lixiaoxiao9888-create/manju-laoli-skill", "Narrator-AI/Narrator-AI-Master-Coze", "UllrAI/CineGen-ShortDrama",
  "A-cat-with-carrots/OnlyShot", "QwenAudio/qwen-audio-agent"]),
 ("agent", "🤖", "Agent / Skills 生态", "AI 智能体框架、Claude/Agent Skills、MCP 与提示词工程", [
  "NousResearch/hermes-agent", "deepseek-ai/deepseek-harness", "nextlevelbuilder/ui-ux-pro-max-skill",
  "op7418/guizang-ppt-skill", "JimLiu/baoyu-skills", "jnMetaCode/agency-agents-zh", "anthropics/commerce-agents",
  "yaojingang/yao-open-prompts", "yaojingang/yao-meta-skill", "nateherkai/scroll-craft", "OpenBMB/UltraRAG",
  "s1dashu/ip-as-logo-skill", "KKKKhazix/human-writing", "Yacey/agnes-ai-generation-skill", "itwanger/PaiAgent",
  "HA7CH/ha7ch-school"]),
 ("quant", "📈", "量化交易 / 金融", "多智能体金融交易、量化框架与股票分析", [
  "TauricResearch/TradingAgents", "HKUDS/Vibe-Trading", "hsliuping/TradingAgents-CN", "ZhuLinsen/daily_stock_analysis",
  "vnpy/vnpy", "xbtlin/ai-berkshire", "myhhub/stock"]),
 ("media", "📢", "自媒体 / 内容营销", "公众号、小红书运营，爆款选题、SEO 与 AI 变现", [
  "yikart/AiToEarn", "XiaomingX/ai-money-maker-handbook", "TeamWiseFlow/xiaobei", "otter1101/blogger-distiller",
  "iniwap/AIWriteX", "BetaStreetOmnis/xhs_ai_publisher", "yaojingang/GEOFlow", "goenning/google-indexing-script",
  "bmpi-dev/awesome-seo"]),
 ("download", "📥", "视频 / 音频下载", "yt-dlp 系下载器、转码与各平台内容抓取", [
  "yt-dlp/yt-dlp", "jely2002/youtube-dl-gui", "HandBrake/HandBrake", "qiye45/wechatDownload",
  "DangJin/awesome-social-media-downloader", "shiquda/xyz-dl", "vincentnussbaum303/youtube-download"]),
 ("aitool", "🧠", "AI 工具 / 语音", "语音识别、LLM 网关、图像处理与办公自动化", [
  "modelscope/FunASR", "guillaumemeyer/watermarks-remover", "tashfeenahmed/freellmapi", "AgnesAI-Labs/AgnesAI-Models",
  "CoderWanFeng/python-office"]),
 ("learn", "📚", "学习资源 / 教程", "大模型、智能体、编程与 NLP 的系统化学习材料", [
  "EbookFoundation/free-programming-books", "trimstray/the-book-of-secret-knowledge", "fighting41love/funNLP",
  "datawhalechina/hello-agents", "Lordog/dive-into-llms", "lintsinghua/claude-code-book",
  "Advanced-Frontend/Daily-Interview-Question", "EvanLi/Github-Ranking", "lzt-code/blog"]),
 ("edu", "🎓", "教育 / 英语学习", "儿童学习、英语学习与教材资源", [
  "TapXWorld/ChinaTextbook", "ZuodaoTech/everyone-can-use-english", "tangshimin/MuJing", "xckevin/magic-english-buddy",
  "chenichangzi/jianfei-bozhu-knowledge-base"]),
 ("wechat", "💬", "微信 / 飞书生态", "微信 SDK、小程序资源与飞书 MCP/OpenAPI", [
  "JeffreySu/WeiXinMPSDK", "opendigg/awesome-github-wechat-weapp", "larksuite/lark-openapi-mcp", "cso1z/Feishu-MCP",
  "ConnectAI-E/feishu-openai"]),
 ("dev", "🛠️", "前端 / 开发工具", "UI 组件库、跨端框架、建站与商城系统", [
  "flutter/flutter", "vueComponent/ant-design-vue", "buuing/lucky-canvas", "crmeb/CRMEB",
  "JCodesMore/ai-website-cloner-template", "o8oo8o/WebCurl"]),
 ("ebook", "📖", "电子书 / 资源库", "电子书入口与私人书单", [
  "z-libraryopp/z-libraryopp.github.io", "Dujltqzv/Some-Many-Books"]),
 ("tool", "🔧", "实用工具", "手机与系统效率工具", [
  "pppscn/SmsForwarder"]),
]


def fetch_starred():
    """分页拉取全部星标仓库（带 token 时限速 5000/h，足够）。"""
    items, page = [], 1
    headers = {"User-Agent": "awesome-github-star", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    while True:
        url = f"https://api.github.com/users/{OWNER}/starred?per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read().decode("utf-8"))
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(1)
    return items


def fmt_stars(n):
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def build_cats_with_new(items):
    """在固定分类之后，动态追加「最新收录」分类，收纳尚未登记分类的新星标仓库。"""
    known = {n for _cid, _i, _n, _d, repos in CATS for n in repos}
    new_repos = sorted((n for n in items if n not in known),
                       key=lambda n: -items[n]["stargazers_count"])
    cats = list(CATS)
    if new_repos:
        cats.append(("new", "🆕", "最新收录（待分类）",
                     "刚加入星标、还没来得及归档分类的新金矿", new_repos))
    return cats


def gen_readme(items, today):
    total = sum(r["stargazers_count"] for r in items.values())
    n10k = sum(1 for r in items.values() if r["stargazers_count"] >= 10000)
    L = []
    A = L.append
    A("# ⭐ 星标淘金图鉴：AI 应用层仓库导航")
    A("")
    cats = build_cats_with_new(items)
    A("> 2026，AI 应用元年，Agent 遍地开花。这里只收「**用大模型做事**」的仓库：AI 内容创作（图/视频/动画/短剧）、自媒体 AI 化运营、Agent 框架/平台/工具、MCP、Skill、专家 Agent、多智能体协作编排……基于大模型的应用项目都算。")
    A(f"> 共 **{len(items)}** 个仓库，全部亲自验证、真正在用，总计 **{total/10000:.0f} 万+** 星。")
    A("")
    A(f"🤖 **本清单由 GitHub Actions 每日自动更新**（当前数据更新于 **{today}**，星标数与仓库数量实时有效）")
    A("")
    A("**🚀 [打开可搜索导航页（GitHub Pages）](https://%s.github.io/awesome-github-star/)** —— 支持关键词搜索、分类筛选，比 README 更好用" % OWNER)
    A("")
    A("## 🤔 为什么做这个清单")
    A("")
    A("大模型已经泛滥，训练、微调、原理拆解的红利期已经过去。2026 年是 AI 应用的元年：**Agent 遍地开花，把大模型用起来才是主战场**——做图、做视频、做动画、做短剧，自媒体运营从纯手工搞素材/撰写/设计，变成由 Agent 和 Skill 驱动的全流程智能化。")
    A("")
    A("但应用层的仓库散落在 GitHub 各处，Trending 上却全是面试指南和复读机。这个清单是我的私人淘金记录：**只收录 AI 应用方向、我亲自验证过、真正在用的仓库**。省下你 90% 的筛选时间。")
    A("")
    A("## ✨ 特性")
    A("")
    A(f"- 🎯 **{len(items)} 个仓库，全部亲自验证**，拒绝云收藏")
    A(f"- ⭐ **总计 {total/10000:.0f} 万+ 星**，含 {n10k} 个万星项目")
    A(f"- 🗂️ **{len(cats)} 大功能分类**，覆盖 AI 视频/短剧、Agent、量化、自媒体四大主线")
    A("- 🔍 **可搜索导航页**（GitHub Pages），支持关键词过滤与分类跳转")
    A(f"- 🔄 **每日自动更新**：星标数、仓库数量由 Actions 定时刷新，永不过期")
    A("- 🌐 中英双语仓库混合，简介均为一句话说清用途")
    A("")
    A("## 📂 目录")
    A("")
    cats = build_cats_with_new(items)
    for i, (_cid, icon, name, desc, _repos) in enumerate(cats, 1):
        A(f"- {icon} **[{name}](#{i}-{name.replace(' ', '-').replace('/', '')})**（{len(_repos)} 个）— {desc}")
    A("")
    A("---")
    A("")
    for i, (_cid, icon, name, desc, repos) in enumerate(cats, 1):
        A(f"## {i}. {icon} {name}")
        A("")
        A(f"> {desc}")
        A("")
        A("| 仓库 | Stars | 语言 | 一句话简介 |")
        A("|------|------:|------|-----------|")
        rs = sorted(repos, key=lambda n: -items[n]["stargazers_count"])
        for n in rs:
            r = items[n]
            d = (r.get("description") or "").replace("|", "/").replace("\n", " ").strip()
            if len(d) > 80:
                d = d[:77] + "..."
            lang = r.get("language") or "-"
            A(f"| [{n}]({r['html_url']}) | {fmt_stars(r['stargazers_count'])} | {lang} | {d} |")
        A("")
    A("---")
    A("")
    A("## 🗺️ Roadmap（画个饼）")
    A("")
    A("- [x] 每日自动更新：GitHub Actions 定时刷新星标数据")
    A("- [ ] 新增「星标增速榜」：近 30 天涨星最快的收藏")
    A("- [ ] 英文版 README（TODO）")
    A("- [ ] 按使用场景的「组合配方」：例如 AI 短剧全流程要用哪 5 个仓库")
    A("")
    A("## 🤝 如何贡献")
    A("")
    A(f"发现失效链接？有好仓库推荐？欢迎提 [Issue](https://github.com/{OWNER}/awesome-github-star/issues) 或 PR。")
    A("")
    A("## 📄 License")
    A("")
    A("[MIT](LICENSE) —— 清单随意转载，注明出处即可。")
    A("")
    return "\n".join(L)


def gen_data_js(items):
    import datetime
    today = datetime.date.today().isoformat()
    cats_js = []
    for cid, icon, name, desc, repos in build_cats_with_new(items):
        rs = []
        for n in sorted(repos, key=lambda x: -items[x]["stargazers_count"]):
            r = items[n]
            rs.append({"n": n, "s": r["stargazers_count"], "l": r.get("language") or "-",
                       "d": ((r.get("description") or "").strip()[:150])})
        cats_js.append({"id": cid, "icon": icon, "name": name, "desc": desc, "repos": rs})
    total = sum(r["stargazers_count"] for r in items.values())
    payload = {"updated": today, "totalStars": total, "cats": cats_js}
    return "window.NAV_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"


def main():
    import datetime
    today = datetime.date.today().isoformat()
    raw = fetch_starred()
    items = {r["full_name"]: r for r in raw}
    print(f"fetched {len(items)} starred repos")

    missing = [n for _cid, _i, _n, _d, repos in CATS for n in repos if n not in items]
    if missing:
        print("WARN: repos no longer starred / renamed:", missing)
        for _cid, _i, _n, _d, repos in CATS:
            repos[:] = [n for n in repos if n in items]

    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(gen_readme(items, today))
    with open(os.path.join(ROOT, "data.js"), "w", encoding="utf-8") as f:
        f.write(gen_data_js(items))
    print("README.md and data.js regenerated")


if __name__ == "__main__":
    main()
