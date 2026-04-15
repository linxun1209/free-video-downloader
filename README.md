# SaveAny

一个基于 `Vue 3 + FastAPI + yt-dlp + DeepSeek + SQLite + Stripe` 的在线视频下载与 AI 总结工具。

当前仓库已经覆盖这几类能力：

- 多平台视频解析与下载
- 抖音专用无 Cookie 解析链路
- B 站优先字幕提取
- AI 总结、字幕展示、思维导图、视频问答
- 邮箱注册登录、JWT 鉴权
- 用户资料编辑
- 免费额度与 VIP 权限控制
- Stripe 支付与 Webhook 回调

这份 README 以“快速上手和继续开发”为目标，内容基于当前仓库代码，而不是项目宣传文案。

## 功能概览

### 面向用户

- 输入视频链接后解析标题、封面、时长、作者、平台、可用格式
- 选择清晰度后由服务端下载并返回文件
- 解析完成后自动触发 AI 总结流程
- 总结面板支持：
  - 摘要
  - 字幕
  - 思维导图
  - AI 问答
- 支持字幕导出为 `SRT / VTT / TXT`
- 支持思维导图导出为 `PNG / SVG`
- 支持邮箱注册、登录、退出
- 支持用户资料查看与编辑：昵称、手机号、个人简介
- 免费用户每天可使用 3 次 AI 总结，VIP 不限次
- 支持月度会员支付和支付成功后的 VIP 激活

### 当前实现上的注意点

- 后端既提供 `/api/download`，也提供 `/api/direct-url`
- 当前前端默认使用的是服务端下载模式，没有把“优先直链下载”完整接进主流程
- AI 总结要求用户登录；未登录用户会被拒绝
- AI 总结依赖平台可用字幕，没有字幕的视频无法生成总结

## 技术栈

### 前端

- Vue 3
- Vite
- Tailwind CSS v4
- axios
- marked
- markmap-lib / markmap-view

### 后端

- FastAPI
- uvicorn
- yt-dlp
- httpx
- OpenAI Python SDK（以 OpenAI 兼容方式调用 DeepSeek）
- bcrypt
- PyJWT
- stripe
- sqlite3
- python-dateutil

## 仓库结构

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
│   ├── downloads/
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── public/
    └── src/
```

## 系统架构

```text
浏览器
  │
  ├─ Vue 页面
  │   ├─ 解析视频
  │   ├─ 下载视频
  │   ├─ 自动触发 AI 总结
  │   ├─ 展示字幕 / 思维导图 / 问答
  │   └─ 登录 / 支付 / 用户资料
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

## 快速开始

### 环境要求

- Python `>= 3.10`
- Node.js `>= 18`
- `ffmpeg`，推荐安装
- 可用的 `DeepSeek API Key`
- 如需支付联调，需要 Stripe 测试环境配置

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端默认地址：

```text
http://localhost:8000
```

也可以直接运行：

```bash
python main.py
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

### 3. 开发联调

前端开发服务器已经配置代理，请求 `/api/...` 时会自动转发到本地 FastAPI：

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

## 环境变量

后端通过 `python-dotenv` 读取 `backend/.env`。

### 必填

| 变量名 | 说明 |
| --- | --- |
| `DEEPSEEK_API_KEY` | AI 总结、思维导图、问答 |
| `JWT_SECRET` | JWT 签名密钥 |

### 支付相关

| 变量名 | 说明 |
| --- | --- |
| `STRIPE_SECRET_KEY` | Stripe 服务端密钥 |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook 验签密钥 |
| `STRIPE_PRICE_ID_MONTHLY` | 月度会员价格 ID |
| `FRONTEND_URL` | 支付成功/取消后的跳转地址 |

示例：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
JWT_SECRET=your-jwt-secret-change-in-production
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
STRIPE_PRICE_ID_MONTHLY=price_your_monthly_price_id
FRONTEND_URL=http://localhost:5173
```

## 核心接口

### 基础视频接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/parse` | 解析视频信息 |
| `POST` | `/api/download` | 服务端下载并返回文件 |
| `POST` | `/api/direct-url` | 获取视频直链 |
| `GET` | `/api/proxy/thumbnail` | 代理缩略图 |

### AI 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/summarize` | SSE 流式视频总结 |
| `POST` | `/api/chat` | SSE 流式视频问答 |

`/api/summarize` 会按事件流返回这些事件类型：

- `subtitle`
- `summary`
- `mindmap`
- `quota`
- `done`
- `error`

### 认证接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/register` | 注册 |
| `POST` | `/api/auth/login` | 登录 |
| `GET` | `/api/auth/me` | 获取当前登录用户 |
| `GET` | `/api/auth/profile` | 获取用户资料 |
| `PUT` | `/api/auth/profile` | 更新用户资料 |

资料字段包括：

- `nickname`
- `phone`
- `bio`

其中长度限制为：

- `nickname <= 30`
- `phone <= 20`
- `bio <= 200`

### 支付接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/payment/create-checkout` | 创建 Stripe 支付会话 |
| `POST` | `/api/payment/webhook` | Stripe Webhook 回调 |
| `GET` | `/api/payment/orders` | 查询当前用户订单 |

## 数据存储

项目默认使用 SQLite，数据库文件位于：

```text
backend/data/app.db
```

当前主要数据表：

- `users`
  - 邮箱、密码哈希
  - 用户资料
  - VIP 状态
  - 每日 AI 总结次数
- `orders`
  - 订单号
  - 套餐类型
  - Stripe 会话 ID
  - 支付状态
  - 支付时间

`init_db()` 会自动建表，并兼容旧库补齐用户资料字段：

- `nickname`
- `phone`
- `bio`

## 测试

当前仓库已包含用户资料相关测试，位于：

```text
backend/tests/
```

可在后端目录执行：

```bash
pytest tests -q
```

如果本地没有安装 `pytest`，需要先自行安装开发测试依赖。

## 实现说明

### 下载链路

- 普通平台主要通过 `yt-dlp` 完成解析与下载
- 抖音走 `backend/douyin.py` 的专用解析器
- 如果系统中找不到 `ffmpeg`，部分“视频音频合并”格式会自动降级到 `best`

### 字幕与 AI

- B 站优先走专用字幕提取逻辑
- 其他平台通过 `yt-dlp` 下载字幕后再统一解析
- 优先人工字幕，其次自动字幕
- AI 总结与问答依赖可用字幕文本

### 登录与权限

- 登录态通过 Bearer Token 传递
- 免费用户每日 AI 总结额度为 3 次
- VIP 用户不限次

## 已知限制

- 当前文档中的支付流程是基于 Stripe Checkout 实现的单次支付会话，不是完整订阅系统
- `/api/direct-url` 已实现，但前端默认下载流程仍走服务端下载
- 当前 CORS 配置为全开放，便于本地开发，生产环境需要收紧
- 下载目录会在应用关闭时清理，不是按请求即时清理
- 某些平台是否能解析、能否拿到直链、能否提取字幕，仍取决于平台侧限制和 `yt-dlp` 支持情况

## 相关文档

- `docs/保姆级本地运行指南.md`
- `docs/方案设计.md`
- `docs/需求分析.md`

如果你准备继续二开，建议先读 `backend/main.py`、`backend/downloader.py`、`backend/summarizer.py` 和 `frontend/src/App.vue`，这几个文件基本覆盖了主链路。
