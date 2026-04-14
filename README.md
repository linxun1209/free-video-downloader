# SaveAny 深度项目说明

> 一个基于 `Vue 3 + FastAPI + yt-dlp + DeepSeek + SQLite + Stripe` 的在线视频下载与 AI 总结工具。
>
> 这份 README 不再以课程宣传为主，而是基于当前仓库代码，对项目的实际实现、模块职责、请求链路、数据结构和运行方式做一次完整拆解，方便你读代码、二开、排障和继续演进。

## 1. 项目是什么

SaveAny 是一个前后端分离的在线视频工具，核心目标有两件事：

1. 让用户输入一个视频链接后，统一解析并下载不同平台的视频。
2. 在“下载”之外，进一步利用字幕和大模型，给视频生成摘要、思维导图和问答能力。

从当前代码来看，它已经不是一个单纯的 `yt-dlp` 前端壳，而是一个相对完整的小型产品原型，包含：

- 多平台视频解析与下载
- 抖音专用无 Cookie 解析
- B 站优先字幕提取
- AI 总结、字幕展示、思维导图、视频问答
- 用户注册/登录
- 免费额度与 VIP 权限
- Stripe 支付下单与 Webhook 回调
- SQLite 本地持久化

## 2. 当前代码实现了什么

### 2.1 面向用户的功能

- 输入视频链接，调用后端解析视频标题、封面、时长、作者、平台、可用格式。
- 选择清晰度后由服务端完成下载，并将文件返回给浏览器。
- 解析完成后前端会自动触发 AI 总结流程。
- 总结面板分为 4 个标签页：
  - 总结摘要
  - 字幕文本
  - 思维导图
  - AI 问答
- 支持字幕导出为 `SRT / VTT / TXT`。
- 支持思维导图导出为 `PNG / SVG`。
- 支持邮箱注册登录。
- 免费用户每日可使用 3 次 AI 总结，VIP 不限次。
- 支持 Stripe 创建月度会员支付链接，支付成功后通过 Webhook 激活 VIP。

### 2.2 已实现但前端没有完整用上的能力

- 后端提供了 `/api/direct-url`，可以返回视频直链。
- 但当前前端实际下载流程默认走的是 `/api/download` 服务端下载模式，并没有自动优先走直链模式。

这意味着：

- “获取直链”是后端能力。
- “自动选择直链还是代理下载”在当前 UI 中还没有真正打通。

## 3. 技术栈与选型思路

### 3.1 前端

- `Vue 3`
- `Vite`
- `Tailwind CSS v4`
- `axios`
- `marked`
- `markmap-lib`
- `markmap-view`

前端的重点不是复杂状态管理，而是一个“单页工作台”：

- 上半部分负责链接输入和视频解析。
- 中间部分是视频信息与 AI 面板的双栏布局。
- 下半部分是营销与 SEO 型静态区块。

### 3.2 后端

- `FastAPI`
- `uvicorn`
- `yt-dlp`
- `httpx`
- `openai` SDK
- `bcrypt`
- `PyJWT`
- `stripe`
- `sqlite3`
- `python-dateutil`

后端把职责拆成了几块：

- `main.py` 负责应用启动和基础路由
- `downloader.py` 负责通用视频解析/下载
- `douyin.py` 负责抖音专用链路
- `summarizer.py` 负责字幕提取和 DeepSeek 调用
- `api_auth.py` / `api_summarize.py` / `api_payment.py` 分别挂认证、AI、支付接口
- `database.py` 负责 SQLite 表结构与业务读写

### 3.3 为什么这样选

- `yt-dlp` 解决“支持多平台下载”的底层能力。
- `FastAPI` 解决 HTTP API 和 SSE 流式输出。
- `openai` SDK + `DeepSeek` 解决大模型接入，同时保持 OpenAI 兼容接口风格。
- `SQLite` 让项目本地可直接启动，不依赖 MySQL/Redis。
- `Stripe` 让项目具备真实的会员变现能力，而不是只停留在 Demo 层。

## 4. 仓库结构总览

```text
free-video-downloader/
├── README.md
├── docs/
│   ├── 保姆级本地运行指南.md
│   ├── 方案设计.md
│   └── 需求分析.md
├── backend/
│   ├── main.py
│   ├── downloader.py
│   ├── douyin.py
│   ├── summarizer.py
│   ├── auth.py
│   ├── database.py
│   ├── api_auth.py
│   ├── api_payment.py
│   ├── api_summarize.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/
│   └── downloads/
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── main.js
    │   ├── App.vue
    │   ├── style.css
    │   ├── api/
    │   │   ├── auth.js
    │   │   ├── payment.js
    │   │   ├── summarize.js
    │   │   └── video.js
    │   └── components/
    │       ├── AppHeader.vue
    │       ├── AppFooter.vue
    │       ├── AuthModal.vue
    │       ├── HeroSection.vue
    │       ├── VideoResult.vue
    │       ├── VideoSummary.vue
    │       ├── FeatureSection.vue
    │       ├── HowToSection.vue
    │       ├── ComparisonSection.vue
    │       ├── PricingSection.vue
    │       └── PlatformSection.vue
```

## 5. 系统架构

```text
浏览器
  │
  ├─ Vue 页面
  │   ├─ 解析视频
  │   ├─ 选择格式并下载
  │   ├─ 自动触发 AI 总结
  │   ├─ 展示字幕 / 思维导图 / 问答
  │   └─ 登录 / 支付
  │
  └─ HTTP / SSE
      │
      ▼
FastAPI
  ├─ /api/parse
  ├─ /api/download
  ├─ /api/direct-url
  ├─ /api/proxy/thumbnail
  ├─ /api/summarize
  ├─ /api/chat
  ├─ /api/auth/*
  └─ /api/payment/*
      │
      ├─ yt-dlp 通用解析下载
      ├─ 抖音专用解析器
      ├─ 字幕提取器
      ├─ DeepSeek 总结 / 问答
      ├─ JWT 鉴权
      ├─ SQLite 用户与订单
      └─ Stripe 支付
```

## 6. 本地运行

### 6.1 环境要求

- Python `>= 3.10`
- Node.js `>= 18`
- `ffmpeg`，建议安装
- 一个可用的 `DeepSeek API Key`
- 如果要体验支付，需要 Stripe 测试环境配置

### 6.2 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

后端默认监听：

```text
http://localhost:8000
```

### 6.3 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端默认监听：

```text
http://localhost:5173
```

### 6.4 开发联调方式

`frontend/vite.config.js` 中配置了代理：

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

这意味着开发时前端请求 `/api/...` 会自动转发给本地 FastAPI 服务。

## 7. 环境变量说明

后端通过 `python-dotenv` 加载 `backend/.env`。

### 7.1 必填变量

| 变量名 | 用途 |
| --- | --- |
| `DEEPSEEK_API_KEY` | AI 总结、思维导图、问答 |
| `JWT_SECRET` | 用户登录 Token 签名 |

### 7.2 选填变量

| 变量名 | 用途 |
| --- | --- |
| `STRIPE_SECRET_KEY` | Stripe 服务端密钥 |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook 验签 |
| `STRIPE_PRICE_ID_MONTHLY` | 月度会员价格 ID |
| `FRONTEND_URL` | 支付成功/取消后的跳转地址 |

`.env.example` 示例：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
JWT_SECRET=your-jwt-secret-change-in-production
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
STRIPE_PRICE_ID_MONTHLY=price_your_monthly_price_id
FRONTEND_URL=http://localhost:5173
```

## 8. 后端深度讲解

### 8.1 `main.py` 做了什么

这是后端的总入口，负责 5 件事：

1. 加载环境变量。
2. 创建 `FastAPI` 实例。
3. 初始化数据库。
4. 挂载基础路由和功能路由。
5. 在应用关闭时清理下载目录。

### 基础路由

- `GET /api/health`
  - 健康检查
- `POST /api/parse`
  - 解析视频信息
- `POST /api/download`
  - 服务端下载视频并回传文件
- `POST /api/direct-url`
  - 获取视频直链
- `GET /api/proxy/thumbnail`
  - 代理缩略图，绕过部分平台防盗链

### 生命周期处理

应用启动时：

- 调用 `init_db()` 初始化表结构。

应用关闭时：

- 遍历 `backend/downloads/`
- 尝试删除目录内文件

注意这里的行为是：

- 只在应用关闭时清理下载目录。
- 不是“每次请求后删除”。
- 也不是“定时任务清理”。

### CORS 配置

当前配置是：

- `allow_origins=["*"]`
- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

这对本地开发很方便，但生产环境通常需要收紧来源。

### 8.2 `downloader.py`：通用下载器

`VideoDownloader` 是对 `yt-dlp` 的一层封装，解决三个问题：

1. 不下载时的视频解析
2. 实际视频下载
3. 视频直链提取

### 核心设计

- `DOWNLOAD_DIR` 固定在 `backend/downloads`
- 初始化时自动创建目录
- 自动探测 `ffmpeg`
  - 先查系统 PATH
  - 再尝试 `static_ffmpeg`

### `parse_video(url)`

使用 `yt_dlp.YoutubeDL(...).extract_info(url, download=False)` 获取元数据，然后做二次整理，输出统一结构：

- `id`
- `title`
- `thumbnail`
- `duration`
- `duration_string`
- `uploader`
- `platform`
- `view_count`
- `upload_date`
- `description`
- `formats`
- `subtitles`
- `automatic_captions`

### `_extract_formats(info)`

这是下载器里比较关键的一段逻辑，主要做了：

- 遍历 `yt-dlp` 返回的原始格式列表
- 过滤掉纯音频流
- 只保留含视频的格式
- 用 `(height, ext, av/v)` 去重
- 生成适合前端展示的 `label`
- 按分辨率从高到低排序
- 最多返回 15 项

还有一个很实用的处理：

- 如果所有可见格式都不带音频，则手动在首位插入一个 `bestvideo+bestaudio/best`
- 前端会把它展示成“最佳（视频+音频合并）”

### `download_video(url, format_id)`

真实下载逻辑：

- 如果没有 `ffmpeg` 且格式 ID 含 `+`，自动降级为 `best`
- 使用 `yt-dlp` 下载到 `downloads/`
- 如果标准路径找不到文件，再尝试：
  - `ydl.prepare_filename(info)`
  - 在目录里按标题模糊查找

这部分解决的是：不同平台、不同后处理方式下，最终文件名不一定完全可预测。

### `get_direct_url(url, format_id)`

该接口只负责解析出媒体直链，不真正下载。

返回：

- `direct_url`
- `ext`
- `filesize`
- `title`

但要注意：

- 某些平台没有稳定直链。
- 某些平台返回的是分离流。
- 当前前端默认没有使用这个能力作为下载主路径。

### 8.3 `douyin.py`：抖音专用解析器

这是项目里最“针对平台定制”的模块。

作者没有完全依赖 `yt-dlp` 处理抖音，而是单独做了一个 `DouyinParser`，核心目标是：

- 尽量不依赖 Cookie
- 支持无水印链接
- 提高抖音场景可用性

### 整体流程

```text
输入文本
  → 提取链接
  → 解析短链跳转
  → 抽取 video_id
  → 优先调用公开 API
  → 如果失败则回退到分享页 HTML 解析
  → 拿到视频信息与无水印地址
```

### 关键点

- `_extract_url`
  - 允许用户输入一段包含链接的文本，不要求严格只传 URL
- `_resolve_redirect`
  - 处理抖音分享短链接跳转
- `_extract_video_id`
  - 从 query、path、多种 URL 结构中提取视频 ID
- `_fetch_via_api`
  - 调用 `https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/`
- `_fetch_via_share_page`
  - 如果公开 API 不可用，则抓分享页
- `_solve_waf_and_retry`
  - 尝试处理分享页的简单 WAF 验证
- `_get_media_url`
  - 对 `playwm` 做替换，拿无水印视频地址

### 为什么这个模块重要

因为很多平台通用解析器在抖音场景上容易遇到：

- 反爬
- 登录限制
- 带水印链接
- 分享短链结构变化

这个模块本质上是在给“抖音”做一条单独的容错通道。

### 8.4 `summarizer.py`：字幕提取 + AI 能力

这个文件拆成两部分：

- `SubtitleExtractor`
- `VideoSummarizer`

#### 8.4.1 `SubtitleExtractor`

职责是把“视频 URL”变成“结构化字幕”。

输出结构是：

```json
{
  "has_subtitle": true,
  "language": "zh",
  "subtitle_type": "manual",
  "segments": [
    { "start": 0.0, "end": 3.2, "text": "..." }
  ],
  "full_text": "..."
}
```

### 字幕提取策略

1. 如果是 B 站链接，先走 B 站专用逻辑。
2. 如果拿不到，再回退到 `yt-dlp` 通用逻辑。
3. 通用逻辑优先选择人工字幕，其次自动字幕。
4. 语言优先级：
   - `zh-Hans`
   - `zh`
   - `zh-CN`
   - `en`
   - `ja`
   - `ko`

### 为什么 B 站单独处理

`_extract_bilibili(url)` 会：

- 先从 URL 提取 `BV` 号
- 请求 B 站视频信息接口拿到 `aid / cid`
- 再请求弹幕/字幕接口拿字幕列表
- 下载字幕 JSON
- 转成统一的 `segments`

这样做的好处是：

- 能优先拿到 B 站原生 CC 字幕
- 对 B 站场景更稳定

### `yt-dlp` 字幕下载逻辑

通用逻辑并不是直接读取 `subtitles` 里的 URL，而是：

- 用 `yt-dlp` 在临时目录里下载字幕文件
- 指定格式为 `vtt`
- 再手动解析 VTT

这样做的优势是：

- 不同平台的字幕格式不统一
- 统一转成 VTT 再解析更稳定

### `_parse_vtt(filepath)`

负责把 VTT 解析成 `segments`：

- 提取时间区间
- 清洗 HTML 标签
- 去除纯重复文本
- 转成 `{start, end, text}`

#### 8.4.2 `VideoSummarizer`

这个类负责真正调用 DeepSeek。

初始化时：

- 读取 `DEEPSEEK_API_KEY`
- 用 `OpenAI` SDK 构造客户端
- 指定 `base_url="https://api.deepseek.com"`
- 默认模型写死为 `deepseek-chat`

### 三类 AI 能力

- `summarize_stream(subtitle_text, language)`
  - 流式总结
- `generate_mindmap(subtitle_text, language)`
  - 一次性生成思维导图 Markdown
- `chat_stream(subtitle_text, question)`
  - 流式问答

### Prompt 设计

代码里做了两个实际限制：

- 总结和思维导图只取字幕前 `15000` 个字符
- 问答只取字幕前 `12000` 个字符

这说明它目前是“长度截断策略”，不是“分块总结 + 汇总”策略。

优点：

- 实现简单
- 成本可控

缺点：

- 超长视频可能只总结前半部分

### 8.5 `api_summarize.py`：SSE 总线

这是 AI 侧的接口编排层。

### `POST /api/summarize`

这是一个 SSE 接口，按事件流返回：

- `subtitle`
- `summary`
- `mindmap`
- `quota`
- `done`
- `error`

完整流程：

1. 检查用户是否允许使用 AI 总结
2. 提取字幕
3. 把字幕数据先推给前端
4. 如果没有字幕，直接推送错误事件
5. 流式输出总结 token
6. 再生成一次性思维导图 Markdown
7. 返回额度信息
8. 返回完成事件

### 权限逻辑

`_check_summary_permission(user)` 的规则是：

- 未登录：拒绝
- 免费用户：走每日次数限制
- VIP：不限次数

### 一个很重要的实现细节

SSE 返回的流式文本不是裸文本，而是 `json.dumps()` 之后再发。

这样做的好处是：

- 避免换行和特殊字符把 SSE 帧切坏
- 前端可稳定 `JSON.parse()`

### `POST /api/chat`

也是 SSE 接口，事件主要有：

- `answer`
- `done`
- `error`

当前实现有一个值得注意的点：

- 这个接口虽然注入了 `get_optional_user`
- 但没有像总结接口那样做登录和次数校验

也就是说，按当前代码：

- AI 总结受登录和额度限制
- AI 问答接口本身没有额度限制

前端层面因为摘要页会先尝试总结，所以用户通常会先被登录门槛挡住；但从接口实现看，问答权限并没有被真正收紧。

### 8.6 `auth.py`：认证基础设施

认证层实现很直接：

- `bcrypt` 处理密码哈希
- `PyJWT` 处理 token
- `HTTPBearer` 读取请求头里的 Bearer Token

### 核心函数

- `hash_password`
- `verify_password`
- `create_token`
- `decode_token`
- `get_current_user`
- `get_optional_user`

### Token 特点

- 算法：`HS256`
- 过期时间：72 小时
- `sub` 存用户 ID
- 同时保存邮箱

### 密码校验

当前规则比较轻量：

- 最少 6 位
- 最多 50 位

没有额外要求：

- 不要求大小写
- 不要求数字
- 不要求特殊字符

### 8.7 `database.py`：SQLite 业务层

这个文件承担了本项目几乎全部持久化逻辑。

### 数据库位置

```text
backend/data/app.db
```

### 初始化表

启动时自动创建两张表：

#### `users`

- `id`
- `email`
- `password_hash`
- `is_vip`
- `vip_expire_at`
- `daily_summary_count`
- `last_summary_date`
- `created_at`
- `updated_at`

#### `orders`

- `id`
- `order_no`
- `user_id`
- `amount`
- `currency`
- `status`
- `plan_type`
- `stripe_session_id`
- `stripe_payment_intent_id`
- `paid_at`
- `created_at`
- `updated_at`

### 数据库访问方式

`get_db()` 用 context manager 包装：

- 开启连接
- 设置 `Row` 工厂
- 开启 `WAL`
- 开启外键
- 成功自动提交
- 异常自动回滚

### 免费额度逻辑

`check_and_increment_summary(user_id)` 是免费额度的核心：

- 每天按 UTC 日期计算
- 新的一天会重置计数为 1
- 免费额度上限是 `3`
- VIP 返回 `-1` 表示无限制

这里要注意时区语义：

- 代码按 `UTC` 天切换
- 不是按浏览器本地时间
- 也不是按中国时区自然日

### 支付完成后的会员激活

`complete_order(session_id, payment_intent_id)` 会：

- 找到状态为 `pending` 的订单
- 标记为 `paid`
- 计算新的 VIP 到期时间
- 如果当前还在 VIP 有效期内，则续费是“叠加”

当前实际配置的套餐只有：

- `monthly`

但是数据库代码对 `yearly` 也留了兼容逻辑。

### 8.8 `api_auth.py`：注册登录接口

提供三个接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### 注册流程

1. 校验邮箱格式
2. 校验密码长度
3. 检查邮箱是否重复
4. 哈希密码
5. 写入用户表
6. 直接签发 JWT
7. 返回 token 和用户信息

这意味着：

- 注册成功后无需再次登录
- 前端可直接把 token 存本地

### `GET /api/auth/me`

用途是：

- 页面刷新后恢复用户状态
- 支付成功后重新刷新会员状态

### 8.9 `api_payment.py`：支付链路

### 当前套餐

代码中 `PLANS` 当前只定义了一个套餐：

- `monthly`
- 名称：`SaveAny VIP 月度会员`
- 金额：`990`
- 货币：`cny`

也就是前端展示的 `¥9.9/月`。

### `POST /api/payment/create-checkout`

流程如下：

1. 校验用户已登录
2. 读取 Stripe 密钥、价格 ID、前端回跳地址
3. 创建本地订单号
4. 先在 SQLite 中写入待支付订单
5. 再调用 Stripe Checkout 创建会话
6. 把 `session.id` 回写订单
7. 返回 `checkout_url`

### 为什么先写本地订单

因为支付回调最终还是要以本地订单为准，先落库能保证：

- 有明确订单号
- 支付完成后可追踪
- 前端成功页可带 `order_no`

### `POST /api/payment/webhook`

用途是接收 Stripe 回调。

支持的事件：

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

核心点：

- 用 `STRIPE_WEBHOOK_SECRET` 验签
- 调 `complete_order(...)` 做幂等更新

### `GET /api/payment/orders`

返回当前用户订单列表，前端当前没有专门订单页，但接口已经具备。

## 9. 前端深度讲解

### 9.1 `src/main.js`

很简单，只做两件事：

- 引入全局样式
- 挂载 `App.vue`

### 9.2 `src/style.css`

项目把 Tailwind v4 的主题变量写在这里：

- 主色：`#1777FF`
- 主背景：白色
- 浅色区块背景：`#F8FAFC`
- 文本、边框、成功/警告/错误色

这意味着前端视觉风格主要依赖：

- Tailwind 原子类
- 少量主题变量
- 少量组件内 scoped style

### 9.3 `App.vue`：前端总编排器

这是前端最核心的文件，负责把各个 UI 组件和业务状态串起来。

### 管理的核心状态

- 用户状态
- 登录弹窗
- 支付结果提示
- 当前解析中的 URL
- 视频解析结果
- 下载中状态
- 总结中状态
- AI 面板刷新键 `summaryKey`
- 一个隐藏的 `demoMode`

### 页面结构

从上到下是：

1. `AppHeader`
2. `HeroSection`
3. 解析成功后的视频区
   - 左边 `VideoResult`
   - 右边 `VideoSummary`
4. `FeatureSection`
5. `HowToSection`
6. `ComparisonSection`
7. `PricingSection`
8. `PlatformSection`
9. `AppFooter`
10. `AuthModal`

### 关键交互

#### 解析视频

- `HeroSection` 提交 URL
- `App.vue` 调 `parseVideo`
- 成功后写入 `videoData`
- 同时自增 `summaryKey`
- `VideoSummary` 因为 `key` 变化重新挂载
- `onMounted()` 自动触发总结

这就是“解析成功后自动开始 AI 总结”的实现方式。

#### 下载视频

- `VideoResult` 把 `format_id` 抛给父组件
- `App.vue` 调 `downloadViaServer`
- 把后端返回的 `blob` 转成浏览器下载

#### 恢复登录状态

- 首先从 `localStorage` 读缓存用户
- 再调用 `/api/auth/me` 做一次服务端校验

### 隐藏功能：`demoMode`

`App.vue` 里埋了一个小彩蛋：

- 当用户不在输入框里时
- 连续快速按 3 次 `Enter`
- 会切换 `demoMode`

它的影响主要是：

- 控制首页 slogan 的显示逻辑

这不是核心业务，但说明页面做过演示场景兼容。

### 9.4 `src/api/*.js`：前端接口层

#### `video.js`

负责：

- `parseVideo`
- `getDirectUrl`
- `downloadViaServer`

其中：

- `getDirectUrl` 已封装
- 但当前主流程没有用

#### `auth.js`

负责：

- token 存取
- 用户对象存取
- 注册登录
- 获取当前用户
- 退出登录

本地存储键：

- `saveany_token`
- `saveany_user`

#### `payment.js`

负责：

- 创建支付链接
- 拉取订单列表

#### `summarize.js`

这是前端接口层里最值得看的一个文件。

因为 SSE 这里没有用浏览器原生 `EventSource`，而是自己用：

- `fetch`
- `ReadableStream`
- 手动解析 SSE 帧

这么做的原因很实际：

- `EventSource` 不方便发送 `POST`
- `EventSource` 不方便带认证头
- 这里的总结和问答都需要 POST Body

所以作者自己实现了一个 `handleSSEStream(response, callbacks)`。

### 9.5 `HeroSection.vue`

职责很单纯：

- 展示标题、说明文案和 URL 输入框
- 维护当前输入内容
- 提供几个演示链接按钮
- 提交时对 B 站链接做一个 `www.bilibili.com` 规范化

这个组件不直接发请求，只通过事件把 URL 抛给父组件。

### 9.6 `VideoResult.vue`

这个组件对应左侧视频信息卡片。

它负责：

- 显示视频封面、标题、作者、平台、播放量
- 展示格式列表
- 选择当前 `format_id`
- 触发下载
- 触发“重新总结”

### 一个细节

封面图不是直接使用原始 `thumbnail`，而是走：

```text
/api/proxy/thumbnail?url=...
```

这是为了绕过一些平台的防盗链和跨域问题。

### 9.7 `VideoSummary.vue`

这是前端最复杂的组件，也是整个项目的 AI 中心。

### 4 个标签页

- 总结摘要
- 字幕文本
- 思维导图
- AI 问答

### 进入页面时会自动做什么

组件 `onMounted()` 会直接调用 `startSummarize()`。

这意味着：

- 只要 `VideoSummary` 被挂载
- 就会自动开始请求 `/api/summarize`

### 总结摘要

- 实时拼接 `summary` 事件
- 使用 `marked` 渲染 Markdown
- 配合 `@tailwindcss/typography` 和 scoped style 做排版美化

### 字幕文本

- 使用 `subtitle` 事件里的 `segments`
- 带时间戳展示
- 支持展开/收起
- 支持下载为：
  - `SRT`
  - `VTT`
  - `TXT`

### 思维导图

- `mindmap` 事件返回的是 Markdown，不是图
- 前端用 `markmap-lib` 把 Markdown 转成树
- 再用 `markmap-view` 渲染成 SVG

### 导图导出的难点

组件里为导图导出做了不少工程性处理：

- 通过 `getBBox()` 计算完整内容边界
- 纠正异常 `transform`
- 把 `foreignObject` 替换成纯 SVG `text`
- 内联 markmap 样式
- 通过 `canvas` 导出高分辨率 PNG

这说明作者不只是“能显示图”，而是考虑了“导出文件可用性”。

### AI 问答

- 把用户问题追加到对话列表
- 新建一个占位的 AI 消息对象
- 通过 SSE 实时把 `answer` token 拼进去
- 回答内容同样支持 Markdown 渲染

### 一个优化点

问答时优先使用已有的 `subtitleData.full_text`，避免重复提取字幕。

### 9.8 其他展示组件

这些组件主要负责 Landing Page 的静态区块：

- `AppHeader.vue`
- `FeatureSection.vue`
- `HowToSection.vue`
- `ComparisonSection.vue`
- `PricingSection.vue`
- `PlatformSection.vue`
- `AppFooter.vue`
- `AuthModal.vue`

它们本身逻辑不重，但承担了产品化层面的职责：

- 登录注册入口
- VIP 转化入口
- SEO 关键词分布
- 对工具能力的解释和对比

## 10. 关键业务链路

### 10.1 视频解析链路

```text
用户输入 URL
  → 前端调用 /api/parse
  → main.py 判断是否抖音
    → 是：走 DouyinParser
    → 否：走 VideoDownloader.parse_video
  → 后端返回统一结构的视频信息
  → 前端展示格式列表和视频信息
  → 同时触发 AI 总结组件重挂载
```

### 10.2 视频下载链路

```text
用户在前端选择格式
  → 调用 /api/download
  → 后端用 yt-dlp 或抖音专用逻辑下载到 backend/downloads
  → FastAPI 返回 FileResponse
  → 浏览器收到 blob
  → 前端创建临时链接并触发下载
```

### 10.3 AI 总结链路

```text
VideoSummary 挂载
  → 调用 /api/summarize
  → 后端校验登录和额度
  → 字幕提取器抽取字幕
  → SSE 推送 subtitle
  → DeepSeek 流式生成 summary
  → SSE 推送 summary token
  → DeepSeek 再生成 mindmap Markdown
  → SSE 推送 mindmap
  → SSE 推送 quota
  → SSE 推送 done
```

### 10.4 AI 问答链路

```text
用户输入问题
  → 调用 /api/chat
  → 优先使用已有字幕全文
  → 若没有则服务端重新提取字幕
  → DeepSeek 流式回答
  → SSE 推送 answer token
  → 前端对话框实时更新
```

### 10.5 注册登录链路

```text
注册
  → /api/auth/register
  → 校验邮箱与密码
  → bcrypt 哈希
  → SQLite 写用户
  → 返回 JWT
  → 前端存 localStorage

登录
  → /api/auth/login
  → 验证密码
  → 返回 JWT
  → 前端存 localStorage
```

### 10.6 支付开通 VIP 链路

```text
用户点击开通 VIP
  → /api/payment/create-checkout
  → 本地创建 pending 订单
  → Stripe 创建 Checkout Session
  → 前端跳到 Stripe 支付页
  → Stripe 回调 /api/payment/webhook
  → 后端验签并 complete_order
  → 订单改 paid，用户 VIP 生效
  → 前端支付成功页再次调用 /api/auth/me 刷新状态
```

## 11. API 总览

### 11.1 基础能力

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/parse` | 解析视频信息 |
| `POST` | `/api/download` | 服务端下载并回传文件 |
| `POST` | `/api/direct-url` | 获取视频直链 |
| `GET` | `/api/proxy/thumbnail` | 代理缩略图 |

### 11.2 AI 能力

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/summarize` | SSE 视频总结 |
| `POST` | `/api/chat` | SSE 视频问答 |

### 11.3 认证能力

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/register` | 注册 |
| `POST` | `/api/auth/login` | 登录 |
| `GET` | `/api/auth/me` | 获取当前用户 |

### 11.4 支付能力

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/payment/create-checkout` | 创建支付会话 |
| `POST` | `/api/payment/webhook` | Stripe Webhook |
| `GET` | `/api/payment/orders` | 查询当前用户订单 |

## 12. 数据结构与业务规则

### 12.1 用户规则

- 邮箱唯一
- 密码最少 6 位
- 登录态使用 JWT
- 免费用户每日 3 次 AI 总结
- VIP 用户无限次 AI 总结

### 12.2 订单规则

- 创建支付会话前先生成本地订单
- Webhook 才是正式的支付成功依据
- 订单完成后会同步更新用户 VIP 时间
- 续费时如果当前 VIP 未过期，会在原有效期基础上顺延

### 12.3 文件规则

- 下载文件暂存在 `backend/downloads/`
- 应用关闭时尝试清理
- 没有单独的历史下载记录表

## 13. 这个项目值得学习的点

如果你是从工程角度看这个仓库，比较值得学的不是“页面好不好看”，而是下面这些组合能力：

- 如何把 `yt-dlp` 封装成统一 API。
- 如何对特定平台做专门适配，而不是把所有平台都塞进一个通用逻辑里。
- 如何把字幕提取、LLM 调用、SSE 推流串成可交互体验。
- 如何在前端自己解析 SSE，而不是只会用最简单的 `axios.get()`。
- 如何在一个轻量项目里加上真正可运行的认证、额度和支付闭环。
- 如何用 SQLite 在本地快速完成产品原型，而不引入过重基础设施。

## 14. 当前实现的边界与注意事项

这部分很重要，因为它决定了你二开时优先改什么。

### 14.1 文档与代码存在漂移

仓库里的部分旧文档已经落后于当前实现，例如：

- 旧设计稿里写“无数据库”
- 但当前代码实际上已经引入 SQLite、用户表、订单表和会员体系

所以判断项目现状时，应优先以代码为准。

### 14.2 下载链路还没有真正利用直链模式

后端已有 `/api/direct-url`，但前端默认只走服务端下载。

这意味着仍有优化空间：

- 优先走浏览器直链下载，降低服务器带宽压力
- 不可直连时再回退到代理下载

### 14.3 AI 总结是截断式，不是长文分块式

长字幕只截前 `15000` 或 `12000` 字符，这会影响超长视频质量。

### 14.4 问答接口权限校验偏松

`/api/chat` 当前没有像 `/api/summarize` 一样做严格登录和额度控制。

### 14.5 没有自动化测试

当前仓库里没有测试文件，至少当前工作区下未发现：

- 单元测试
- 接口测试
- 前端组件测试

这意味着后续迭代更依赖人工验证。

### 14.6 生产级能力还不完整

例如：

- 没有任务队列
- 没有缓存层
- 没有对象存储
- 没有下载进度推送
- 没有审计日志
- 没有更细的权限与风控

它更适合：

- 学习
- 演示
- 小规模试运行

而不是直接无改造上线承载大流量。

## 15. 如果你要继续迭代，建议优先做什么

### 第一优先级

- 接通前端“直链优先，代理兜底”的下载策略
- 给 `/api/chat` 增加和总结一致的权限/额度控制
- 为超长视频加入“分块总结 + 汇总”

### 第二优先级

- 增加下载进度
- 增加失败重试与错误码分层
- 增加 Docker 部署方案
- 增加订单页和会员中心

### 第三优先级

- 增加 Whisper/ASR，覆盖无字幕视频
- 增加批量下载
- 增加字幕翻译
- 增加历史记录和收藏

## 16. 适合怎么读这个项目

如果你是第一次接触，建议按下面顺序读代码：

1. 先看 `backend/main.py`
2. 再看 `backend/downloader.py` 和 `backend/douyin.py`
3. 再看 `backend/summarizer.py`
4. 再看 `backend/api_summarize.py`
5. 再看 `backend/auth.py`、`backend/database.py`、`backend/api_payment.py`
6. 最后回到前端，从 `frontend/src/App.vue` 开始往下看

这样读会比较顺，因为它和真实请求路径一致。

## 17. 合规提醒

本项目适合作为技术学习、产品原型和工程练习材料。实际使用时应自行遵守：

- 视频平台服务条款
- 所在地区版权与数据合规要求
- 第三方模型与支付服务的使用规则

请勿将未授权内容下载、分发或用于侵权用途。
