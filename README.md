# HelloAgents Trip Planner / 知行旅行

一个围绕“中国旅行场景”构建的多模块智能旅行平台。它不只包含传统的 AI 行程规划，还整合了旅行顾问聊天、数字人页面引导、数据广场、管理员知识库、景区视频生成与多模态视觉问答能力。

## 项目概览

当前仓库由三个主要子系统组成：

- **backend**：FastAPI 后端，负责 API、认证、AI 能力编排、JSON 数据存储、视频任务调度
- **frontend**：Vue 3 + TypeScript 用户端，负责主交互界面与各业务页面
- **video-generator**：React + Remotion 视频渲染子项目，负责把后端准备好的素材渲染成景区介绍视频

如果你想快速理解代码实现而不是只看启动方式，请先阅读：

- [IMPLEMENTATION.md](IMPLEMENTATION.md)

---

## 主要能力

### 1. 智能行程规划

- 基于 HelloAgents 的多智能体旅行规划
- 支持自然语言解析与结构化字段提取
- 输出包含每日行程、景点、餐饮、住宿、天气、预算建议的旅行计划

### 2. 旅行顾问聊天

- 提供面向旅行问题的问答与建议
- 支持上下文对话
- 后端通过 SSE 提供流式回复

### 3. 数字人页面引导

- 全局悬浮数字人助手“红美玲”
- 可根据当前页面提供功能引导
- 支持文本聊天、语音识别、TTS 播报、情绪立绘切换

### 4. 行囊记录 / 历史管理

- 保存已生成的旅行计划
- 编辑任务清单、备注、附件
- 从历史记录同步内容到数据广场

### 5. 数据广场

- 展示城市、景点与旅行数据聚合
- 支持景点详情、广场同步与部分推荐/洞察能力

### 6. 管理员后台能力

- 用户管理
- 广场数据维护
- FAQ 管理
- 知识库导入、上传与删除

### 7. 景区视频生成

- 输入景区名后生成介绍视频任务
- 后端串联脚本、TTS、图片、Remotion 渲染
- 前端轮询任务状态并下载视频

### 8. 多模态视觉问答

- 基于 Qwen-VL 对用户上传图片做理解与回答
- 用于聊天场景下的图片问答

---

## 技术栈

### 后端

- FastAPI
- Uvicorn
- Pydantic / pydantic-settings
- HelloAgents / HelloAgentsLLM
- Qwen-VL（DashScope 兼容接口）
- JSON 文件存储

### 前端

- Vue 3
- TypeScript
- Vite
- Ant Design Vue
- Axios
- Web Speech API
- html2canvas + jsPDF

### 视频子项目

- React
- Remotion
- Zod

---

## 目录结构

```text
helloagents-trip-planner/
├── backend/
│   ├── run.py
│   ├── requirements.txt
│   └── app/
│       ├── config.py
│       ├── data/
│       ├── agents/
│       ├── api/
│       │   ├── main.py
│       │   └── routes/
│       │       ├── auth.py
│       │       ├── trip.py
│       │       ├── chat.py
│       │       ├── plaza.py
│       │       ├── admin.py
│       │       ├── poi.py
│       │       └── video.py
│       ├── models/
│       └── services/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── main.ts
│       ├── services/api.ts
│       ├── components/
│       └── views/
├── video-generator/
│   ├── package.json
│   └── src/
├── IMPLEMENTATION.md
└── README.md
```

---

## 关键模块说明

### 后端路由入口

后端在 [backend/app/api/main.py](backend/app/api/main.py) 中注册以下核心模块：

- `auth`：用户认证
- `chat`：聊天、SSE、数字人相关对话
- `plaza`：数据广场、景点详情、同步等
- `admin`：管理员能力与知识库处理
- `trip`：行程规划、解析、保存、历史、统计
- `poi`：POI 查询与地图相关能力
- `video`：视频任务创建、状态查询、下载

### 前端主壳

前端主壳位于 [frontend/src/views/Dashboard.vue](frontend/src/views/Dashboard.vue)，在一个应用壳中切换多个业务视图，包括：

- 首页
- 个人档案
- 旅行顾问
- 行程规划
- 行囊记录
- 旅行导览
- 数据广场
- 旅行视频
- 使用手记

### 数字人组件

全局数字人组件位于 [frontend/src/components/DigitalHuman.vue](frontend/src/components/DigitalHuman.vue)。

它不是简单聊天框，而是页面引导助手；其会话 ID 使用 `dh_` 前缀，这是当前实现的重要兼容约定。

### 视频渲染子项目

视频模板与渲染入口位于：

- [video-generator/src/Root.tsx](video-generator/src/Root.tsx)
- [video-generator/src/ScenicVideo.tsx](video-generator/src/ScenicVideo.tsx)

它与 Vue 前端分离，由后端视频服务触发渲染。

---

## 快速开始

### 两种启动方式怎么选

- **本地开发模式**：适合日常调试前后端，入口脚本是 [start-local.sh](start-local.sh)
- **Docker 部署 / 演示模式**：适合交付、演示、减少环境差异，入口脚本是 [start.sh](start.sh)

两种模式都要求你先准备自己的 `backend/.env`。仓库不会提供可直接使用的本地 Key。

## 1. 环境要求

建议环境：

- Python 3.10+
- Node.js 18+
- npm

如果你要完整使用 AI / 地图 / 视频能力，还需要准备相应第三方服务密钥。

---

## 2. 后端配置

请先复制示例配置文件，再填写你自己的真实密钥：

> 注意：仓库不会提供可直接使用的本地 Key；无论是本地启动还是部署到服务器，都需要由使用者自行配置自己的第三方服务密钥。

```bash
cp backend/.env.example backend/.env
```

`backend/.env` 至少建议配置：

```bash
AMAP_API_KEY=你的高德Key
LLM_API_KEY=你的主文本模型Key
LLM_BASE_URL=你的主模型兼容地址
LLM_MODEL_ID=你的主模型ID

QWEN_API_KEY=你的Qwen Key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL_ID=qwen-vl-plus

UNSPLASH_ACCESS_KEY=你的Unsplash Access Key
UNSPLASH_SECRET_KEY=你的Unsplash Secret Key

# 可选：数据广场洞察使用的本地 Excel 数据文件
SCENIC_INSIGHTS_EXCEL_PATH=你的景区洞察Excel路径
```

### 配置说明

- `AMAP_API_KEY`：后端启动校验的重要必填项
- `LLM_API_KEY`：主文本 LLM 使用
- `QWEN_*`：视觉问答使用
- `UNSPLASH_*`：图片素材能力使用
- `SCENIC_INSIGHTS_EXCEL_PATH`：数据广场 `/api/plaza/insights` 的可选增强数据源；未配置时该接口会返回提示，但不会阻塞服务启动
- `backend/.env` 不应提交到仓库；如当前密钥曾被提交，请立即轮换

详细说明见：

- [backend/app/config.py](backend/app/config.py)

---

## 3. 前端配置

同样建议先复制前端示例配置：

```bash
cp frontend/.env.example frontend/.env
```

前端可用变量示例：

```bash
VITE_API_BASE_URL=
VITE_AMAP_WEB_KEY=你的可公开高德 Web Key
VITE_AMAP_WEB_JS_KEY=你的可公开高德 Web JS Key
```

注意：

- `VITE_*` 变量会进入浏览器端构建产物，只能填写可公开配置
- 不要把服务端私密密钥（如 `LLM_API_KEY`、`QWEN_API_KEY`、`UNSPLASH_SECRET_KEY`）写入前端 `.env`
- 首页天气、温度、湿度的主查询链路现在走后端 `/api/trip/homepage-weather`，真正必需的是服务端 `AMAP_API_KEY`
- `VITE_AMAP_WEB_KEY` / `VITE_AMAP_WEB_JS_KEY` 主要用于浏览器侧地图、定位补充能力与相关前端交互，不应用来承载服务端私密能力

---

## 4. 本地开发模式（推荐日常调试）

### 4.1 后端准备

**注意：当前项目统一使用 `backend/venv` 作为后端虚拟环境。**

如果你本地同时存在 `backend/.venv`，请不要再用它启动；之前的依赖缺失问题就是由误用 `.venv` 引起的。

推荐先执行环境检查脚本：

```bash
./backend/check_env.sh
```

首次安装后端环境：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.2 前端准备

```bash
cd frontend
npm install
```

前端入口与路由守卫见：

- [frontend/src/main.ts](frontend/src/main.ts)

### 4.3 一键启动本地开发主链路

根目录 [start-local.sh](start-local.sh) 会统一拉起：

- `backend`：复用 [backend/start.sh](backend/start.sh)
- `frontend`：复用 `frontend` 下的 `npm run dev`

执行方式：

```bash
cp backend/.env.example backend/.env
./start-local.sh
```

它会先检查：

- `backend/.env` 是否存在
- 必填配置是否为空，或是否仍保留示例占位值
- `backend/venv/bin/python` 是否存在
- `frontend/node_modules` 是否已安装
- `PORT`（默认 `8000`）和 `FRONTEND_PORT`（默认 `5173`）是否可用

启动后默认访问地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- Swagger：`http://localhost:8000/docs`

如端口冲突，可直接改端口启动：

```bash
PORT=8001 FRONTEND_PORT=5174 ./start-local.sh
```

### 4.4 本地视频模板调试（可选）

如果你还需要一起启动 Remotion 开发服务，可以先安装视频子项目依赖：

```bash
cd video-generator
npm install
```

然后回到仓库根目录执行：

```bash
./start-local.sh --with-video
```

如果你只想单独调试视频模板，也可以直接执行：

```bash
cd video-generator
npm run dev
```

也可以使用：

```bash
npm run build
```

或：

```bash
npm run render
```

具体脚本见：

- [video-generator/package.json](video-generator/package.json)

### 4.5 本地开发验收清单

建议第一次在本地跑通时至少检查：

1. **配置检查**
   - 已执行 `cp backend/.env.example backend/.env`
   - 已把 `AMAP_API_KEY`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL_ID` 改成自己的真实配置
   - 确认没有继续保留“请填写你的...”这类示例占位值

2. **依赖检查**
   - `backend/venv` 已创建并安装依赖
   - `frontend/node_modules` 已安装
   - 如需视频模板调试，`video-generator/node_modules` 已安装

3. **服务检查**
   - 执行 `./start-local.sh` 后前端能在 `http://localhost:5173` 打开
   - `http://localhost:8000/docs` 能看到 FastAPI Swagger 文档
   - 首页天气、温度、湿度可正常加载（前提是自己的高德服务 Key 有效）

4. **排障检查**
   - 如前端未安装依赖：`cd frontend && npm install`
   - 如后端虚拟环境缺失：`cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
   - 如本地端口冲突：`PORT=8001 FRONTEND_PORT=5174 ./start-local.sh`
   - 如需视频模板调试：`./start-local.sh --with-video`

---

## 5. Docker Compose 一键部署（推荐交付 / 演示）

如果你希望保留当前**前端 + 后端 + 视频生成**全部功能，同时尽量控制交付体积，推荐直接使用仓库根目录的 Compose 方案：

```bash
cp backend/.env.example backend/.env
./start.sh
```

根目录 [start.sh](start.sh) 现在会先检查：

- `docker` 命令是否存在
- `docker compose` 插件是否可用
- `backend/.env` 是否已准备完成
- 必填配置是否为空，或是否仍保留示例占位值

当前部署结构包含三个服务：

- `frontend`：提供 Vue 构建后的静态站点
- `backend`：提供 FastAPI API、聊天、行程规划、数字人、视频任务入口
- `video-generator`：提供 Remotion 运行时占位容器，并与后端共享视频媒体卷

### Compose 运行要点

- Linux 环境建议安装 Docker Engine 并确认 `docker compose` 可用；Mac / Windows 可使用 Docker Desktop
- 仓库不会附带可直接使用的本地密钥，启动前必须先把 `backend/.env` 中的示例占位值改成你自己的真实配置
- 浏览器访问：`http://localhost`
- 后端文档：`http://localhost:8000/docs`
- 视频生成素材与成品不再默认堆在源码目录，而是写入 Compose 卷 `video_media`
- 首次构建通常较慢，因为会同时构建前端、后端和视频渲染依赖
- 如需彻底清理视频成品、临时音频和图片，可执行：

```bash
docker compose down -v
```

### 体积控制建议（很重要）

如果你要把项目发给别人或上传到服务器，请**不要**把下面这些内容一起打包：

- `backend/venv`
- `backend/.venv`
- `frontend/node_modules`
- `frontend/dist`
- `video-generator/node_modules`
- `video-generator/output`
- `video-generator/public/audio`
- `video-generator/public/images`

这些目录已经通过根目录和子目录下的 `.dockerignore` 规则尽量排除在构建上下文之外；真正需要上线的主要是源码、Dockerfile、Compose 配置和后端 `.env`。

### 视频生成相关环境变量

视频功能现在支持通过 `backend/.env` 覆盖运行时目录与渲染参数，默认值已经写在 [backend/.env.example](backend/.env.example) 中：

- `VIDEO_GENERATOR_DIR`
- `VIDEO_MEDIA_ROOT`
- `VIDEO_OUTPUT_SUBDIR`
- `VIDEO_AUDIO_SUBDIR`
- `VIDEO_IMAGE_SUBDIR`
- `VIDEO_OUTPUT_KEEP_COUNT`
- `VIDEO_TEMP_KEEP_DAYS`
- `EDGE_TTS_BIN`
- `REMOTION_CONCURRENCY`
- `PUPPETEER_EXECUTABLE_PATH`

默认策略会：

- 把最终 mp4 保留最近若干个（默认 5 个）
- 把旧的音频、图片、Remotion staging 目录按天数清理（默认 2 天）
- 保证视频功能保留的同时，不让媒体文件无限增长

### 部署验收清单

建议别人第一次拿到项目时，至少按下面顺序验收一遍：

1. **配置检查**
   - 已执行 `cp backend/.env.example backend/.env`
   - 已把 `AMAP_API_KEY`、`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL_ID` 改成自己的真实配置
   - 如需视觉问答，已配置自己的 `QWEN_API_KEY`
   - 确认没有继续保留“请填写你的...”这类示例占位值

2. **启动检查**
   - 已安装 Docker
   - `docker compose version` 可正常输出
   - 执行 `./start.sh` 时没有出现缺少配置或占位值报错

3. **服务检查**
   - 打开 `http://localhost` 能进入前端首页
   - 打开 `http://localhost:8000/docs` 能看到 FastAPI Swagger 文档
   - `docker compose ps` 能看到 `frontend`、`backend`、`video-generator` 三个服务处于运行状态

4. **关键功能检查**
   - 登录 / 注册可正常使用
   - 首页城市、天气、温度、湿度可正常加载（前提是自己的高德服务 Key 有效）
   - 行程规划可以正常生成结果
   - 视频生成功能至少能成功发起任务；如依赖完整，再进一步验证视频可生成并下载

5. **排障检查**
   - 查看全部日志：`docker compose logs -f`
   - 查看视频相关日志：`docker compose logs -f backend video-generator`
   - 如需彻底清理环境后重试：`docker compose down -v`

---

## 常用 API 分类

详细接口请直接查看 Swagger，但从功能上可以先这样理解：

### 认证

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/auth/update-name`
- `POST /api/auth/logout`

### 行程规划

- `POST /api/trip/parse`
- `POST /api/trip/plan`
- `POST /api/trip/save`
- `GET /api/trip/history`
- `GET /api/trip/history/{id}`
- `PUT /api/trip/history/{id}`
- `PUT /api/trip/history/{id}/tasks`
- `DELETE /api/trip/history/{id}`
- `POST /api/trip/suggest`
- `POST /api/trip/homepage-weather`
- `GET /api/trip/stats`

### 聊天 / 数字人

- `/api/chat/*`
  - 会话创建
  - 会话读取
  - SSE 流式回复
  - 视觉问答

### 数据广场

- `/api/plaza/*`
  - 广场数据
  - 景点详情
  - 同步
  - 推荐 / 洞察相关能力

### 视频

- `POST /api/video/generate`
- `GET /api/video/status/{task_id}`
- `GET /api/video/download/{task_id}`

### 管理员

- `/api/admin/*`
  - 用户管理
  - FAQ 管理
  - 知识库导入 / 上传 / 删除
  - 广场数据维护

---

## 重要实现约定

在继续开发前，建议先了解这些约定：

### 1. 数字人会话前缀必须保留

数字人使用 `dh_` 前缀会话 ID；后端会据此区分数字人引导模式与普通聊天模式。

### 2. 前端 API 调用优先走 `api.ts`

统一 API 入口在：

- [frontend/src/services/api.ts](frontend/src/services/api.ts)

新增前端接口时，优先在这里收口，而不是继续在页面里散写 `fetch()`。
首页天气能力已经按这个约定收口到 [frontend/src/services/api.ts](frontend/src/services/api.ts) 的 `getHomepageWeather()`。

### 3. 当前存储仍是 JSON 文件体系

数据主要位于：

- `backend/app/data/`

本项目当前没有数据库，后续修改时请注意兼容已有 JSON 结构。

### 4. 后端优化以兼容现有路由为优先

当前很多前端页面已经依赖现有 API 路径，后端重构时优先“路由不变、逻辑下沉”。

### 5. 服务端配置统一从 `backend/app/config.py` 读取

新增或修改后端第三方配置时，优先通过统一配置层读取，不要在路由或前端中继续散落读取环境变量、硬编码 Key 或机器相关绝对路径。

---

## 建议阅读顺序

如果你第一次接手这个项目，建议按下面顺序进入：

### 先看说明

1. [README.md](README.md)
2. [IMPLEMENTATION.md](IMPLEMENTATION.md)

### 后端

1. [backend/app/api/main.py](backend/app/api/main.py)
2. [backend/app/config.py](backend/app/config.py)
3. [backend/app/models/schemas.py](backend/app/models/schemas.py)
4. [backend/app/api/routes/auth.py](backend/app/api/routes/auth.py)
5. [backend/app/api/routes/trip.py](backend/app/api/routes/trip.py)
6. [backend/app/api/routes/chat.py](backend/app/api/routes/chat.py)
7. [backend/app/api/routes/plaza.py](backend/app/api/routes/plaza.py)
8. [backend/app/api/routes/video.py](backend/app/api/routes/video.py)

### 前端

1. [frontend/src/main.ts](frontend/src/main.ts)
2. [frontend/src/services/api.ts](frontend/src/services/api.ts)
3. [frontend/src/views/Dashboard.vue](frontend/src/views/Dashboard.vue)
4. [frontend/src/views/Home.vue](frontend/src/views/Home.vue)
5. [frontend/src/views/History.vue](frontend/src/views/History.vue)
6. [frontend/src/components/DigitalHuman.vue](frontend/src/components/DigitalHuman.vue)

### 视频

1. [video-generator/package.json](video-generator/package.json)
2. [video-generator/src/Root.tsx](video-generator/src/Root.tsx)
3. [video-generator/src/ScenicVideo.tsx](video-generator/src/ScenicVideo.tsx)
4. `backend/app/services/video_service.py`

---

## 当前已知的优化方向

本仓库已经做过一轮低风险优化，但还有一些热点值得继续处理：

### 后端热点

- `backend/app/api/routes/chat.py`：职责混杂
- `backend/app/api/routes/plaza.py`：职责较重，仍有配置/路径卫生问题
- `backend/app/api/routes/video.py`：认证方式仍待进一步统一
- `backend/app/api/routes/admin.py`：管理员认证仍处于混合态

### 前端热点

- `frontend/src/views/Home.vue`：仍有较多直接 `fetch()` 与大组件问题
- `frontend/src/components/DigitalHuman.vue`：适合继续拆分逻辑层

### 文档与验证

- 建议在继续迭代时同步维护 `IMPLEMENTATION.md`
- 重要修改后应补做前后端启动、构建与关键流程验证

---

## 开发建议

如果你准备继续优化这个项目，推荐顺序是：

1. 先统一认证边界，逐步减少 `X-Username` 扩散
2. 再拆 `chat.py` / `plaza.py` 的重逻辑
3. 收口 `Home.vue` 的原始请求到 `api.ts`
4. 最后补做验证与文档同步

---

## 补充说明

- 本项目当前更适合被理解为“旅行平台”而不是“单页行程生成 Demo”
- README 负责快速上手与模块索引
- 详细实现请阅读 [IMPLEMENTATION.md](IMPLEMENTATION.md)
