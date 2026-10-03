# -*- coding: utf-8 -*-
"""
all-10000-star 生成器：分类全站 5603 个万星仓库，产出 README.md / data.js / snapshot.json。
- 本地跑：--source jsonl 初始分类与生成（无翻译）
- Actions 跑：--source snapshot 先补翻译（Google gtx 批量），再重新生成
"""
import json, os, re, sys, time, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # repo root
SUB  = os.path.join(ROOT, "all-10000-star")
SNAP = os.path.join(SUB, "snapshot.json")
JSONL = r"C:/Users/1/AppData/Local/Temp/gh_star10k_repos.jsonl"

SNAPSHOT_DATE = "2026-10-03"

# ---------------- 分类规则（按应用场景；顺序即优先级，先命中先归类） ----------------
CATS = [
 ("agent", "🤖", "AI Agent 生态", "Agent 框架与编排、MCP、Skill、专家角色、多智能体协作"),
 ("ai-create", "🎨", "AI 内容创作", "AI 图像/视频/语音生成与编辑：作图、做视频、TTS、语音识别、数字人"),
 ("ai-chat", "💬", "AI 对话/助手应用", "ChatGPT 类客户端、AI 助手、聊天机器人应用"),
 ("llm-infra", "🧠", "大模型基础设施", "LLM 推理/训练/微调框架、RAG、向量库、模型部署"),
 ("quant", "📈", "量化交易/金融", "交易机器人、量化框架、股票加密货币分析"),
 ("web3", "⛓️", "区块链/Web3", "区块链节点、智能合约、DeFi、NFT、共识协议"),
 ("media", "📢", "自媒体/内容营销", "SEO、社媒运营、营销自动化、内容变现"),
 ("download", "📥", "下载/订阅工具", "视频音频下载器、BT、流媒体录制"),
 ("avtools", "🎬", "音视频处理", "视频剪辑、字幕、转码、IPTV、媒体服务器"),
 ("security", "🔒", "安全/网络", "渗透测试、隐私保护、代理翻墙、密码管理"),
 ("selfhost", "🏠", "自托管/效率生活", "NAS、Docker 自托管应用、家庭自动化、笔记网盘"),
 ("edu", "🎓", "教育/英语学习", "英语学习、儿童教育、教材资源"),
 ("learn", "📚", "学习资源/教程", "编程教程、面试题、awesome 清单、路线图"),
 ("game", "🎮", "游戏/娱乐", "游戏、模拟器、游戏引擎、Minecraft"),
 ("data", "🧪", "数据/爬虫", "爬虫、数据集、数据分析、可视化"),
 ("mobile", "📱", "移动开发", "Android/iOS、跨端框架"),
 ("web", "🌐", "Web/前端", "前端框架、UI 组件、网站模板、低代码"),
 ("backend", "🗄️", "后端/数据库", "后端框架、数据库、API、消息队列"),
 ("devtools", "🛠️", "开发工具", "CLI、编辑器、DevOps、版本管理、调试"),
 ("tools", "🧰", "桌面/实用工具", "系统工具、OCR、PDF、截图、文件管理"),
 ("other", "📦", "其他", "暂未归类的优质仓库"),
]

RULES = {
 "agent": ["agent", "mcp", "skill", "multi-agent", "agentic", "claude code", "codex", "copilot agent",
           "autogen", "crewai", "langgraph", "openai swarm", "ai workforce", "orchestrat", "sub-agent", "subagent",
           "context protocol", "ai coding", "coding assistant", "ai harness", "cli ai", "ai cli"],
 "ai-create": ["stable diffusion", "comfyui", "text-to-image", "image generation", "text-to-video", "video generation",
               "ai image", "ai video", "tts", "text-to-speech", "speech recognition", "automatic speech", "asr",
               "whisper", "voice clone", "voice conversion", "digital human", "数字人", "lip sync", "animatediff",
               "lora", "midjourney", "inpainting", "outpainting", "ai art", "ai music", "suno", "dubbing", "配音",
               "ai 绘画", "ai绘画", "video gen", "ai 写真", "face swap", "faceswap", "ai 换脸", "avatar", "speech synthesis",
               "audio generation", "music generation", "ai photo", "ai 绘图", "生图", "文生图", "文生视频", "图生视频", "抠图",
               "voice ai", "face recognition", "人脸识别", "face verification", "voice model"],
 "ai-chat": ["chatbot", "chatgpt", "chat gpt", "gpt-4", "gpt4", "llm chat", "chat ui", "chatui", "open webui",
             "nextchat", "lobe", "chatbox", "ai assistant", "ai 助手", "聊天机器人", "对话机器人", "roleplay ai",
             "ai girlfriend", "ai 陪伴", "character ai", "virtual girlfriend"],
 "llm-infra": ["llm", "large language model", "large-language-model", "inference engine", "vllm", "ollama",
               "fine-tun", "fine tun", "微调", "transformers", "rag", "retrieval augment", "embedding",
               "vector database", "vector-db", "langchain", "llamaindex", "model deployment", "推理框架",
               "大模型", "深度学习框架", "deep learning framework", "mlops", "ai gateway", "模型训练", "training framework",
               "gpu scheduling", "machine learning framework", "prompt engineering", "diffusion model", "onnx",
               "quantization", "model quantiz", "gguf", "openai compatible", "local ai",
               "machine learning", "deep learning", "neural network", "pytorch", "tensorflow", "keras", "scikit",
               "computer vision", "object detection", "opencv", "yolo", "gpt", "llama", "qwen", "deepseek",
               "reinforcement learning", "强化学习", "nlp", "自然语言", "机器学习", "mnn", "ncnn", "tflite", "jax",
               "hugging face", "huggingface", "model zoo", "多模态", "multimodal", "agent framework"],
 "quant": ["trading", "trade bot", "stock", "quant", "crypto", "bitcoin", "binance", "backtest",
           "finance", "financial", "investment", "投资", "交易", "股票", "量化", "kline", "forex", "币", "期权",
           "hedge fund", "对冲基金"],
 "web3": ["blockchain", "ethereum", "solidity", "evm", "web3", "defi", "nft", "smart contract", "consensus",
          "layer1", "layer 2", "validator", "cryptocurrency", "区块链", "智能合约", "加密货币", "去中心化", "dapp"],
 "media": ["seo", "social media", "自媒体", "公众号", "小红书", "xiaohongshu", "marketing", "tweet", "twitter post",
           "instagram", "tiktok", "youtube video maker", "content creat", "爆款", "涨粉", "wechat official account",
           "公众号运营", "content marketing", "affiliate", "电子书营销", "douyin", "抖音", "video marketing",
           "matomo", "analytics", "plausible", "umami", "newsletter", "landing page builder"],
 "download": ["downloader", "download video", "download manager", "yt-dlp", "youtube-dl", "youtube downloader",
              "bilibili", "torrent", " magnet ", "aria2", "youtube music", "spotify downloader", "video download",
              "subscription downloader", "yt_dlp", "ytdlp", "savefrom", "jdownloader", "视频下载", "下载器", "音乐下载",
              "music downloader", "podcast downloader", "stream download"],
 "avtools": ["video editor", "video editing", "剪辑", "subtitle", "字幕", "ffmpeg", "handbrake", "video converter",
             "media server", "jellyfin", "plex", "emby", "iptv", "screenshot video", "video compression",
             "audio edit", "music tag", "audio visualizer", "video player", "媒体服务器", "影视", "movieplex",
             "tvshow", "movie", "电影", "追剧", "video management", "gif recorder", "screen recorder", "录屏",
             "screen capture", "obs-studio", "streaming media"],
 "security": ["security", "penetration", "pentest", "hacking", "hacker", "cve", "exploit", "malware", "vulnerability",
              "osint", "password manager", "密码管理", "vpn", "proxy tool", "firewall", "clash", "v2ray", "shadowsocks",
              "翻墙", "科学上网", "surge", "wireguard", "adblock", "ad blocker", "广告拦截", "privacy", "隐私",
              "加密", "encryption tool", "steganography", " honeypot", "IDS ", "waf", "burp", "nmap", "渗透"],
 "selfhost": ["self-hosted", "selfhosted", "self hosted", " homelab", "nas", "nextcloud", "home assistant",
              "smart home", "智能家居", "raspberry", "docker management", "portainer", "rss reader", "rss 阅读器",
              "note-taking", "note taking", "obsidian", "笔记", "wiki", "knowledge base", "知识库", "bookmark",
              "网盘", "cloud drive", "file sync", "photo library", "照片管理", "immich", "jellyseerr", "dashy",
              "homepage dashboard", "uptime monitor", "监控面板", "server panel", "面板", "bookmarks manager"],
 "edu": ["english", "ielts", "toefl", "vocabulary", "单词", "英语", "children", " kids ", "儿童", "education",
         "教育", "learning app", "dictation", "背单词", "children book"],
 "learn": ["tutorial", "roadmap", "interview", "面试", "learn-to-code", "learn to code", "course", "cheatsheet",
           "cheat sheet", "awesome-list", "awesome list", "awesome-", "书籍", "book list", "handbook", "指南",
           "学习", "教程", "curriculum", "study plan", "免费书籍", "free books", "programming books", "算法图解",
           "system design", "设计模式", "coding standards", "exercise", "练习", "题库", "leetcode", "coding interview",
           "clean code", "questions", "周刊", "weekly", "100 days", "100天", "从新手", "架构师", "project layout",
           "should-visit", "大白话", "图解", "入门", "计算机科学", "computer science", "cs courses"],
 "game": ["game", "minecraft", "emulator", "模拟器", "unity", "unreal engine", "godot", "roguelike", "rpg",
          "chess", "棋牌", "poker", "game engine", "游戏引擎", "emu", "rom ", "switch ", "psv", "retro", "街机",
          "cheat engine", "mod manager", "游戏", "gta", "mmorpg", "battlestation", "three.js", "3d library",
          "opengl", "vulkan", "图形渲染", "graphics"],
 "data": ["scraper", "crawler", "spider", "爬虫", "dataset", "数据集", "data analysis", "数据分析", "pandas",
          "visualization", "可视化", "chart", "图表", "dashboard data", "jupyter", "notebook data", "etl",
          "data engineering", "bi tool", "报表", "annotation", "标注", "label studio", "data collection"],
 "mobile": ["android", " ios ", "iphone", "flutter", "react native", "react-native", "mobile app", "apk",
            "移动端", "appium", "swiftui", "jetpack compose", "android app"],
 "web": ["react", "vue", "next.js", "nextjs", "nuxt", "svelte", "frontend", "front-end", "css", "tailwind",
         "ui component", "ui-components", "component library", "组件库", "website template", "网页", "admin template",
         "low-code", "低代码", "no-code", "no code", "website builder", "landing page", "个人主页", "portfolio",
         "blog theme", "website theme", "博客主题", "hexo", "hugo theme", "jekyll", "astro", "web editor",
         "富文本", "rich text editor", "wysiwyg", "form builder", "图表库", "data-table", "web rtc", "webrtc"],
 "backend": ["api framework", "fastapi", "django", "flask", "spring boot", "microservice", "微服务", "database",
             "数据库", "redis", "postgres", "mysql", "mongodb", "sqlite", "orm", "graphql", "grpc", "mqtt",
             "kafka", "消息队列", "message queue", "web framework", "backend framework", "rpc", "distributed",
             "分布式", "存储", "storage engine", "object storage", "对象存储", "search engine", "elasticsearch",
             "向量引擎", "time-series", "时序", "kubernetes", "容器", "service mesh", "api gateway", "网关"],
 "devtools": [" cli", "command line", "command-line", "terminal", "shell", "zsh", "git", "ide", "editor", "vscode",
              "neovim", "vim ", "emacs", "devops", "ci/cd", "github actions", "compiler", "编译器", "debugger",
              "调试", "static analysis", "lint", "formatter", "code review", "regex", "正则", "json viewer",
              "api tool", "api client", "http client", "postman", "insomnia", "抓包", "packet capture", "wireshark",
              "docker image", "dotfiles", "system monitor", "性能", "profiler", "benchmark", "域名", "self-signed",
              "developer", "程序员", "开发", "programming language", "编程语言", "runtime", "跨平台"],
 "tools": ["windows", "macos", "linux tool", "productivity", "效率", "launcher", "clipboard", "剪贴板",
           "screenshot", "截图", "ocr", "pdf", "文件管理", "file manager", "compress", "压缩", "解压", "archive",
           "downloader tool", "hotkey", "快捷键", "输入法", "ime ", "workflow automation", "自动化", "auto hotkey",
           "文件同步", "backup", "备份", "清理", "cleaner", "uninstall", "wallpaper", "壁纸", "天气", "weather",
           "calendar", "日历", "todo", "待办", "password generator", "二维码", "qr code", "translate tool",
           "翻译", "词典", "dictionary", "文本", "text processing", "ffmpeg gui", "local tool", "桌面"],
}

OVERRIDES = {
    "ohmyzsh/ohmyzsh": "devtools", "torvalds/linux": "devtools", "Genymobile/scrcpy": "tools",
    "nilbuild/developer-roadmap": "learn", "kamranahmedse/developer-roadmap": "learn",
    "sherlock-project/sherlock": "security", "bitcoin/bitcoin": "web3", "public-apis/public-apis": "data",
    "freeCodeCamp/freeCodeCamp": "learn", "microsoft/PowerToys": "tools", "996icu/996.ICU": "learn",
    "donnemartin/system-design-primer": "learn", "ossu/computer-science": "learn",
    "EbookFoundation/free-programming-books": "learn", "jwasham/computer-science-flash-cards": "learn",
    "microsoft/playwright": "devtools", "moby/moby": "devtools", "kubernetes/kubernetes": "backend",
    "gohugoio/hugo": "web", "mrdoob/three.js": "game", "spring-projects/spring-framework": "backend",
    "rails/rails": "backend", "jquery/jquery": "web", "reduxjs/redux": "web", "angular/angular.js": "web",
    "odoo/odoo": "backend", "gorhill/uBlock": "security", "LadybirdBrowser/ladybird": "tools",
    "astral-sh/uv": "devtools", "tonsky/FiraCode": "tools", "commaai/openpilot": "llm-infra",
    "twitter/the-algorithm": "data", "ruanyf/weekly": "learn", "opencv/opencv": "llm-infra",
    "python/cpython": "devtools", "golang/go": "devtools", "rust-lang/rust": "devtools",
    "vinta/awesome-python": "learn", "grafana/grafana": "devtools", "Developer-Y/cs-video-courses": "learn",
    "TheAlgorithms/Python": "learn", "TheAlgorithms/Java": "learn", "f/prompts.chat": "llm-infra",
    "awesome-selfhosted/awesome-selfhosted": "selfhost", "trekhleb/javascript-algorithms": "learn",
    "unionlabs/union": "web3", "DigitalPlatDev/FreeDomain": "tools",
}

def classify(name, desc, topics):
    if name in OVERRIDES:
        return OVERRIDES[name]
    text = (name.replace("/", " ") + " " + (desc or "") + " " + " ".join(topics or [])).lower()
    for cid, _, _, _ in CATS:
        for kw in RULES.get(cid, []):
            if kw in text:
                return cid
    return "other"

CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")

def has_cjk(s, ratio=0.25):
    if not s: return False
    return len(CJK.findall(s)) / max(len(s), 1) > ratio

def fmt_stars(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)

# ---------------- 生成 ----------------
def load_items():
    if os.path.exists(SNAP) and "--source" not in sys.argv:
        pass
    src = "snapshot" if ("snapshot" in sys.argv) else "jsonl"
    if src == "snapshot":
        data = json.load(open(SNAP, encoding="utf-8"))
        return data["repos"]
    items = []
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            items.append({
                "n": r["full_name"], "s": r["stargazers_count"], "l": r.get("language") or "-",
                "d": (r.get("description") or "").strip()[:300],
                "u": r["html_url"], "cr": r["created_at"][:10], "up": r["updated_at"][:10],
                "t": r.get("topics") or [], "z": "",
            })
    for it in items:
        it["c"] = classify(it["n"], it["d"], it["t"])
    return items

def save_snapshot(items):
    slim = [{k: it.get(k, "") for k in ("n", "s", "l", "d", "u", "cr", "up", "z", "c")} for it in items]
    json.dump({"date": SNAPSHOT_DATE, "repos": slim}, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False)
    print("snapshot saved:", SNAP)

# ---------------- 翻译（仅 Actions/本地网络可用时） ----------------
def gtx(text):
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": text})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    return "".join(seg[0] for seg in d[0])

def translate_missing(items):
    """Threaded translation with checkpoint saves (8 workers, 3 retries each)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    todo = [it for it in items if not it.get("z") and it["d"] and not has_cjk(it["d"])]
    print(f"to translate: {len(todo)}", flush=True)
    if not todo:
        return items

    def work(it):
        for attempt in range(3):
            try:
                return gtx(it["d"][:400])[:200]
            except Exception:
                time.sleep(2 + attempt * 3)
        return ""

    done = 0
    deadline = time.time() + 90 * 60  # time budget: stop and commit partial results
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(work, it): it for it in todo}
        for fut in as_completed(futs):
            it = futs[fut]
            try:
                z = fut.result()
            except Exception:
                z = ""
            if z:
                it["z"] = z
            done += 1
            if done % 100 == 0:
                print(f"translated {done}/{len(todo)}", flush=True)
            if done % 500 == 0:  # checkpoint: save partial translations
                save_snapshot(items)
                print("checkpoint saved", flush=True)
            if time.time() > deadline:
                print("time budget reached, stopping translation (partial results saved)", flush=True)
                for f in futs:
                    f.cancel()
                break
    ok = sum(1 for it in items if it.get("z"))
    print(f"translation finished: {ok}/{len(items)} have zh", flush=True)
    return items

# ---------------- README ----------------
def gen_readme(items):
    by_cat = {cid: [] for cid, _, _, _ in CATS}
    for it in items:
        by_cat[it["c"]].append(it)
    for cid in by_cat:
        by_cat[cid].sort(key=lambda x: -x["s"])

    L = []
    def A(s): L.append(s)
    A("# 🌌 GitHub 万星仓库全景图：全站 10k+ Stars 一网打尽")
    A("")
    A(f"> **全站扫描**：GitHub 上所有星标超过 10,000 的公开仓库，共 **{len(items)}** 个，一个不漏。")
    A(f"> 按应用场景自动分类成 **{len(CATS)} 大领域**，每个领域按星标数从高到低排列。数据快照：**{SNAPSHOT_DATE}**。")
    A("")
    A("🤖 英文简介均附**中文翻译**（由 GitHub Actions 自动翻译提交）")
    A("")
    A("**🚀 [打开可搜索导航页（GitHub Pages）](https://tongtong2011.github.io/awesome-github-star/all-10000-star/)** —— 5600+ 仓库全量收录，支持关键词搜索、分类筛选")
    A("")
    A("**⬅️ 返回 [星标淘金图鉴（我亲自在用的 88+ 仓库）](../../#readme)**")
    A("")
    A("## 🤔 这个清单和别的 awesome 有什么不同")
    A("")
    A("- **全量**：不是人工挑选的几百个，而是全站 10k+ 星的**每一个**仓库，用 GitHub Search API 按星标区间抓取，无遗漏")
    A("- **按场景分类**：不看技术标签看用途——做图、做视频、搞量化、做自媒体、搭自托管……按你真正想做的事归档")
    A("- **双语简介**：英文说明自动附中文翻译，扫一眼就知道这个仓库是干嘛的")
    A("- **可搜索**：全量数据配有在线导航页，比在 GitHub 里翻快 10 倍")
    A("")
    A("## 📊 全景统计")
    A("")
    A("| 领域 | 数量 | 该领域星标之王 |")
    A("|------|-----:|----------------|")
    for cid, icon, name, desc in CATS:
        lst = by_cat[cid]
        if not lst: continue
        top = lst[0]
        A(f"| {icon} {name} | {len(lst)} | [{top['n']}]({top['u']})（⭐ {fmt_stars(top['s'])}） |")
    A("")
    A("---")
    A("")

    for i, (cid, icon, name, desc) in enumerate(CATS, 1):
        lst = by_cat[cid]
        if not lst: continue
        A(f"## {i}. {icon} {name}（{len(lst)} 个）")
        A("")
        A(f"> {desc}")
        A("")
        A("| 仓库 | Stars | 语言 | 简介 |")
        A("|------|------:|------|------|")
        for it in lst:
            d = it["d"].replace("|", "/").replace("\n", " ")
            z = it.get("z", "")
            if z:
                d = f"{d}<br>*{z}*"
            A(f"| [{it['n']}]({it['u']}) | ⭐ {fmt_stars(it['s'])} | {it['l']} | {d} |")
        A("")
    A("---")
    A("")
    A(f"**数据来源**：GitHub Search API（`stars:>10000`），快照日期 {SNAPSHOT_DATE}。分类由关键词规则引擎自动完成，个别仓库可能归类不完美，欢迎 [提 Issue](https://github.com/tongtong2011/awesome-github-star/issues) 纠正。")
    A("")
    A("## 🔄 数据更新")
    A("")
    A("- 本目录数据为快照，由 GitHub Actions 工作流 `update-all10k` 按需更新（可手动触发）")
    A("- 工作流会重新抓取全站 10k+ 仓库、补齐中文翻译并重新生成本 README 与导航页数据")
    return "\n".join(L)

# ---------------- data.js ----------------
def gen_data_js(items):
    repos = sorted(items, key=lambda x: -x["s"])
    arr = [[r["c"], r["n"], r["s"], r["l"], r["d"][:160], r.get("z", "")[:160]] for r in repos]
    cats = [{"id": cid, "icon": icon, "name": name, "desc": desc} for cid, icon, name, desc in CATS]
    js = "window.ALL10K=" + json.dumps({"updated": SNAPSHOT_DATE, "cats": cats, "repos": arr},
                                       ensure_ascii=False, separators=(",", ":")) + ";"
    open(os.path.join(SUB, "data.js"), "w", encoding="utf-8").write(js)
    print("data.js size:", len(js) // 1024, "KB")

def apply_overrides(items):
    """Hand-translated (skill-quality) zh descriptions always win over machine ones."""
    path = os.path.join(HERE, "zh_overrides.json")
    if not os.path.exists(path):
        return items
    ov = json.load(open(path, encoding="utf-8"))
    n = 0
    for it in items:
        if it["n"] in ov:
            it["z"] = ov[it["n"]]
            n += 1
    print(f"applied {n} hand-translation overrides", flush=True)
    return items

def main():
    items = load_items()
    print("items:", len(items))
    items = apply_overrides(items)
    if os.environ.get("TRANSLATE") == "1":
        items = translate_missing(items)
    save_snapshot(items)
    gen_data_js(items)
    open(os.path.join(SUB, "README.md"), "w", encoding="utf-8").write(gen_readme(items))
    print("README done")
    # stats
    from collections import Counter
    c = Counter(it["c"] for it in items)
    for cid, icon, name, _ in CATS:
        print(f"  {icon} {name}: {c[cid]}")

if __name__ == "__main__":
    main()
