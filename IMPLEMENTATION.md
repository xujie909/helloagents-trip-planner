# 代码功能实现文档

## 1. 文档目的

本文档面向开发、维护、演示与交接，重点说明这个项目“功能是怎么实现的”，而不是只罗列页面名称。

项目当前已经不是单一的旅行规划 Demo，而是一个围绕中国旅行场景构建的多模块平台，包含：

- FastAPI 后端 API
- Vue 3 前端单页应用
- 独立的 Remotion 视频生成子项目
- 多类 AI 能力：旅行规划、旅行顾问、视觉问答、数字人引导、知识库导入与景点介绍

---

## 2. 总体架构

### 2.1 目录级结构

```text
helloagents-trip-planner/
├── backend/                 # FastAPI 后端
├── frontend/                # Vue 3 用户端
├── video-generator/         # Remotion 视频生成子项目
├── README.md                # 项目说明与快速启动
└── IMPLEMENTATION.md        # 本文档
```

### 2.2 三个主子系统的职责

#### backend
负责：

- 提供认证、旅行规划、聊天、数据广场、管理员、视频任务等 API
- 统一读取配置与第三方密钥
- 调用 HelloAgents / LLM / Qwen-VL / 高德 / 本地 JSON 数据
- 管理持久化数据与运行时缓存

#### frontend
负责：

- 登录与路由守卫
- Dashboard 单壳多视图切换
- 聊天、行程规划、历史记录、广场、视频生成等页面交互
- 通过 `frontend/src/services/api.ts` 统一调用后端 API
- 挂载全局数字人引导组件

#### video-generator
负责：

- 使用 React + Remotion 将后端准备好的脚本、图片、音频、字幕等素材渲染为视频
- 作为独立渲染工程存在，不直接混入 Vue 前端

---

## 3. 后端实现

## 3.1 后端入口与启动

### 入口文件

- `backend/run.py`
- `backend/app/api/main.py`

### 启动流程

1. `backend/run.py` 读取配置并启动 Uvicorn。
2. `backend/app/api/main.py` 创建 FastAPI 应用。
3. 注册 CORS。
4. 注册各业务路由：
   - `auth`
   - `chat`
   - `plaza`
   - `admin`
   - `trip`
   - `poi`
   - `video`
5. 在 `startup` 事件中打印配置并执行 `validate_config()`。

### 已确认的关键行为

- 高德 Key 缺失会在启动校验时直接报错。
- 主 LLM Key 缺失会给出警告，但不一定阻断服务启动。

---

## 3.2 配置管理

### 核心文件

- `backend/app/config.py`

### 主要职责

- 通过 `BaseSettings` 统一读取环境变量
- 提供全局 `settings`
- 校验必要配置
- 输出脱敏后的配置摘要

### 当前重点配置

- `AMAP_API_KEY`
- `OPENAI_API_KEY` / `LLM_API_KEY`（主文本 LLM）
- `QWEN_API_KEY`
- `QWEN_BASE_URL`
- `QWEN_MODEL_ID`
- `HOST`
- `PORT`
- `CORS_ORIGINS`
- `SCENIC_INSIGHTS_EXCEL_PATH`（数据广场洞察的可选本地 Excel 数据源）

### 配置策略

- 高德相关能力高度依赖 `AMAP_API_KEY`
- 文本 LLM 由 HelloAgentsLLM 自动读取主模型环境变量
- 多模态视觉模型单独走 Qwen 配置
- 数据广场洞察的 Excel 文件路径通过 `config.py` 统一管理；未配置时仅影响 `/api/plaza/insights`，不会阻断后端启动
- 前端 `VITE_*` 变量会进入浏览器构建产物，只能存放可公开配置，不能放服务端私密密钥

---

## 3.3 数据模型

### 核心文件

- `backend/app/models/schemas.py`

### 作用

定义后端接口间共享的请求/响应模型，包括：

- 旅行规划请求 `TripRequest`
- 旅行计划结构 `TripPlan`
- 单日计划 `DayPlan`
- 景点、餐饮、酒店、天气、预算等结构
- 自然语言解析请求/响应
- 视频生成请求与任务状态

### 设计特点

- 使用 Pydantic 建模，接口语义比较明确
- 行程相关结构是后端与前端展示层的核心契约
- 视频模块也复用了统一的响应模型 `VideoTaskStatus`

---

## 3.4 认证模块

### 核心文件

- `backend/app/api/routes/auth.py`
- `backend/app/services/auth_service.py`

### 提供的能力

- 注册
- 登录
- 获取当前用户信息
- 修改显示名
- 退出登录

### 当前认证方式

后端的标准身份入口是：

- `auth.py:get_current_user()`

它通过 `Authorization: Bearer <token>` 解析当前登录用户。

### 当前实现现状

- `auth.py` 已经明确以 Bearer token 为主
- 其他模块仍有部分接口保留了 `X-Username` 兼容逻辑
- 整体正在逐步向统一认证边界收敛

### 认证数据流

1. 用户调用登录接口。
2. 后端校验用户名密码。
3. 生成 token，并通过 `/api/auth/login` 返回。
4. 前端把 token 与用户名写入 `localStorage`。
5. 后续请求由 `api.ts` 自动注入认证头。
6. 后端通过 `get_current_user()` 或等价逻辑恢复当前用户。

---

## 3.5 行程规划模块

### 核心文件

- `backend/app/api/routes/trip.py`
- `backend/app/agents/trip_planner_agent.py`
- `backend/app/services/trip_store.py`
- `backend/app/services/llm_service.py`

### 主要接口

- `/api/trip/plan`
- `/api/trip/parse`
- `/api/trip/save`
- `/api/trip/history`
- `/api/trip/history/{trip_id}`
- `/api/trip/history/{trip_id}/tasks`
- `/api/trip/suggest`
- `/api/trip/stats`

### 子能力拆解

#### 1）自然语言解析
`/api/trip/parse`

作用：

- 将用户自然语言转成结构化字段
- 判断当前信息是否足够生成行程
- 生成下一轮追问或确认文案

实现方式：

- 组装 system prompt + current_fields + 用户消息
- 调用文本 LLM
- 从返回文本中提取 JSON
- 映射为 `ParseResponse`

#### 2）行程生成
`/api/trip/plan`

作用：

- 基于结构化参数生成完整行程

实现方式：

- 调用 `get_trip_planner_agent()` 获取多智能体规划器
- 由景点、天气、酒店、规划等智能体协作生成统一结果
- 最终返回 `TripPlanResponse`

#### 3）行程持久化
`/api/trip/save` 与 history 系列接口

作用：

- 保存某次旅行计划
- 查询历史记录
- 查询单条详情
- 更新任务清单与附加内容
- 删除历史

实现方式：

- 统一交由 `trip_store.py` 处理
- 以当前用户名为维度进行文件型隔离存储

#### 4）生活建议 / 旅行顾问建议
`/api/trip/suggest`

此接口承担两类功能：

- 普通生活建议
- 旅行顾问问答模式（`_chat`）

说明：

- 普通建议有基于城市、天气、温度的缓存逻辑
- 旅行顾问模式会把最近几轮上下文注入给 LLM

### 关键数据流：行程规划

1. 前端收集用户需求。
2. 用户输入先经 `/api/trip/parse` 提取字段。
3. 当前端认为信息完整后，调用 `/api/trip/plan`。
4. 后端多智能体生成完整行程。
5. 前端展示结果，并允许继续保存到历史记录。
6. 保存行为进入 `trip_store.py`，写入 JSON 文件。

---

## 3.6 聊天模块

### 核心文件

- `backend/app/api/routes/chat.py`
- `backend/app/services/llm_service.py`

### 主要能力

- 对话会话创建与读取
- SSE 流式聊天输出
- 页面上下文引导
- FAQ / 用户档案 / 地图信息注入
- 数字人会话与普通聊天会话分流
- 视觉问答（图片 + 文本）

### 当前架构现状

`chat.py` 是项目当前最重的路由之一，存在多职责耦合：

- 会话管理
- 提示词构建
- FAQ 与资料读取
- 高德数据注入
- SSE 输出
- 数字人角色逻辑
- 视觉问答入口

### SSE 流式输出

数字人与聊天模块并不是一次性返回整段文本，而是通过 SSE 进行增量输出。

典型流程：

1. 前端用 `EventSource` 请求 `/api/chat/conversations/{conv_id}/stream`
2. 后端逐段推送文本事件
3. 前端拼接流式内容并更新界面
4. 流结束后前端再做分段朗读或转入历史消息区

### 数字人模式约定

当会话 ID 以 `dh_` 开头时，后端会识别为数字人引导模式。

这是一个必须保留的兼容约定，因为前端数字人组件与后端分流逻辑依赖这个前缀。

---

## 3.7 数据广场模块

### 核心文件

- `backend/app/api/routes/plaza.py`

### 主要能力

- 广场数据展示
- 用户画像/档案相关逻辑
- 热门城市与景点聚合
- 景点详情补全
- 广场同步
- 推荐与洞察
- 知识库/RAG 风格景点介绍

### 当前实现特征

这是另一个职责较重的模块，集中承担了：

- 数据广场内容组织
- 用户行为结果汇总
- 景点知识读取
- 第三方地图查询
- 缓存与同步

### 当前待继续优化的问题

- 仍广泛依赖 `X-Username`
- 历史上的硬编码高德 key fallback 已纳入统一配置治理，后续新增能力也应继续通过 `config.py` 读取配置
- 景区洞察能力依赖可选 Excel 数据文件，现已改为配置项，不再绑定开发机绝对路径
- 模块边界较大，后续适合拆出 service/helper

### 典型数据流：历史同步到广场

1. 用户在历史页选择同步行程。
2. 前端调用 `/api/plaza/sync`。
3. 后端根据城市与景点列表更新广场聚合数据。
4. 广场页面重新读取后即可看到同步结果。

---

## 3.8 管理员模块

### 核心文件

- `backend/app/api/routes/admin.py`

### 主要能力

- 用户列表与用户状态管理
- 广场数据维护
- FAQ 管理
- 知识库导入、上传与删除
- 平台级数据编辑

### 管理员校验方式

- `_check_admin()` 允许 `X-Username` 或 Bearer token 的管理员身份识别
- 当前属于混合校验态，不是完全统一的认证方案

### 知识库导入逻辑

管理员模块不只是 CRUD，还承担一定 AI 处理能力：

- 导入景点资料
- 调用 LLM 做景点分类
- 更新知识库 JSON
- 同步刷新广场数据或缓存

这使它与 `plaza.py` 在数据层面存在较强耦合。

---

## 3.9 视频生成模块

### 核心文件

- `backend/app/api/routes/video.py`
- `backend/app/services/video_service.py`
- `backend/app/models/schemas.py`
- `video-generator/src/Root.tsx`
- `video-generator/src/ScenicVideo.tsx`

### 后端接口

- `/api/video/generate`
- `/api/video/status/{task_id}`
- `/api/video/download/{task_id}`

### 不是“简单下载接口”，而是完整编排链路

`video_service.py` 负责的是一个多步骤异步任务，而不是只调一次模型：

1. 生成景区介绍脚本
2. 生成 TTS 音频
3. 测量音频时长
4. 拉取景区图片
5. 确定城市信息
6. 组装 Remotion props
7. 触发视频渲染
8. 更新任务进度与最终下载路径

### 前后端交互方式

1. 前端发起 `/api/video/generate`
2. 后端返回任务 ID 与当前状态
3. 前端轮询 `/api/video/status/{task_id}`
4. 状态完成后拿到下载地址
5. 用户再请求 `/api/video/download/{task_id}`

### Remotion 子项目职责

#### `video-generator/src/Root.tsx`
- 注册 `ScenicVideo` Composition
- 根据 props 动态计算总帧数

#### `video-generator/src/ScenicVideo.tsx`
- 组合背景、数字人、字幕、音频序列
- 按每个 scene 的时长控制画面与音轨
- 输出最终视频画面

---

## 3.10 POI 与地图能力

### 相关文件

- `backend/app/api/routes/poi.py`
- `backend/app/config.py`
- 以及 `chat.py` / `plaza.py` 中调用高德的逻辑

### 用途

- POI 搜索
- 景点详情补充
- 路线与天气等旅行辅助能力
- 聊天与广场中的地图信息注入

### 当前注意点

地图能力所需配置已经统一收口到 `config.py`，新增地图相关逻辑时应继续复用该配置入口，避免重新引入硬编码 key、路由层直接读环境变量或机器相关路径。

---

## 3.11 LLM 与多模态能力

### 核心文件

- `backend/app/services/llm_service.py`

### 两类模型能力

#### 文本 LLM：`get_llm()`
- 用于自然语言解析
- 旅行建议
- 聊天与旅行顾问能力
- 管理员知识分类等文本任务

#### Qwen-VL：`get_qwen_llm()` / `chat_with_vision()`
- 用于图片理解与视觉问答
- 使用独立 Qwen 配置

### 本轮已完成的重要优化

Qwen 初始化已经从“依赖全局环境变量覆盖”的方式，改成了显式传参初始化：

- `model=settings.qwen_model_id`
- `api_key=settings.qwen_api_key`
- `base_url=settings.qwen_base_url`
- `provider="qwen"`

这能减少：

- 进程级环境污染
- 多模型并发串配置风险
- 调试时主模型/视觉模型相互影响的问题

---

## 4. 前端实现

## 4.1 前端入口与路由

### 核心文件

- `frontend/src/main.ts`

### 路由结构

当前前端使用 `createWebHistory()`，主要路由包括：

- `/login`
- `/dashboard`
- `/admin`
- `/datascreen`
- `/result`

### 路由守卫

- 通过 `isLoggedIn()` 判断本地 token 是否存在
- 未登录访问受保护页面时跳转 `/login`
- 已登录访问 `/login` 时跳回 `/dashboard`

---

## 4.2 API 调用层

### 核心文件

- `frontend/src/services/api.ts`

### 作用

这是前端网络请求的统一入口，负责：

- 创建 axios 实例
- 注入认证头
- 统一处理 401
- 封装 auth / trip / plaza / video 等 API 方法

### 当前认证头策略

`getAuthHeaders()` 目前仍同时返回：

- `Authorization`
- `X-Username`

这说明前后端还处于认证统一的过渡阶段。

### 本轮已完成的重要前端收口

已经把部分分散请求从页面内回收到 `api.ts`，例如：

- `getTripSuggestion`
- `syncTripToPlaza`
- `getAttractionDetail`

401 处理也已改为与 `createWebHistory()` 兼容的跳转方式：

- `window.location.assign('/login')`

---

## 4.3 Dashboard 单壳多视图结构

### 核心文件

- `frontend/src/views/Dashboard.vue`

### 作用

Dashboard 不是单一页面，而是系统主壳。它通过左侧导航切换不同功能视图，包含：

- 首页 `home`
- 个人档案 `profile`
- 旅行顾问 `chat`
- 行程规划 `plan`
- 行囊记录 `history`
- 旅行导览 `guide`
- 数据广场 `plaza`
- 旅行视频 `video`
- 使用手记 `manual`

### 结构特点

- 左侧是统一导航
- 中间是视图切换区域
- 全局数字人组件始终挂载在主壳外层

这意味着 README 和功能文档必须把 Dashboard 理解为“应用容器”，而不是普通首页。

---

## 4.4 聊天页 / 旅行顾问页

### 核心文件

- `frontend/src/views/Home.vue`

### 职责

该页面承担了较多交互：

- 会话创建
- 消息展示
- SSE 对话
- 视觉问答
- 上传图片
- 语音能力
- 与后端聊天接口对接

### 当前现状

`Home.vue` 仍然比较重，且保留了较多直接 `fetch()` 调用，是前端下一轮收口和拆分的重点文件。

后续适合拆出的方向：

- 会话列表状态
- SSE 流处理
- 图片上传与视觉问答
- 语音输入输出
- 页面内工具区组件

---

## 4.5 历史记录页

### 核心文件

- `frontend/src/views/History.vue`

### 能力

- 历史行程列表
- 单条行程详情
- 任务清单编辑
- 笔记/附件更新
- 景点详情查看
- 同步到广场
- 旅行建议展示

### 本轮已完成的重要优化

页面内部分分散请求已回收到 `api.ts`：

- 同步广场
- 景点详情
- 旅行建议

同时也移除了页面中直接硬编码第三方 key 的天气请求写法。

---

## 4.6 数字人组件

### 核心文件

- `frontend/src/components/DigitalHuman.vue`

### 角色定位

数字人不是普通聊天框皮肤，而是一个“页面引导型智能助手”。

它会：

- 根据当前页面名称生成上下文
- 以全局浮窗形式存在
- 支持展开/收起、拖拽、语音输入、语音播报
- 通过 SSE 与后端流式通信

### 关键约定

会话 ID 生成方式：

- `dh_ + username`

这是后端识别数字人模式的重要协议，不能轻易改动。

### 页面上下文注入

组件会把当前页面编码为：

- 首页
- 个人档案
- 旅行顾问
- 行程规划
- 行囊记录
- 旅行导览
- 数据广场
- 使用手记

后端据此更容易返回页面引导式回答。

---

## 4.7 视频生成页

### 核心文件

- `frontend/src/views/VideoGenerate.vue`

### 作用

- 发起景区视频生成任务
- 轮询任务状态
- 展示进度与结果
- 提供下载入口

### 当前实现特点

- 页面已经主要通过 `api.ts` 调用后端视频接口
- 采用定时轮询，而不是 SSE
- 后续优化重点更偏向轮询逻辑复用，而不是接口收口

---

## 5. JSON 文件存储体系

## 5.1 存储位置

- `backend/app/data/`

## 5.2 当前用途

项目当前没有引入数据库，而是通过 JSON 文件实现轻量持久化。它承载了：

- 用户信息
- token/登录信息
- 历史行程
- 对话记录
- 用户画像/档案
- 广场聚合数据
- FAQ / 知识库 / 景点缓存
- 建议缓存

## 5.3 当前策略

本轮优化不替换为数据库，原因是：

- 用户已有数据结构已建立
- API 行为依赖这些文件格式
- 当前目标是低风险结构优化，而不是基础设施迁移

### 维护约束

后续改造时应尽量保证：

- 旧 JSON 文件仍能被读取
- 用户隔离方式不被破坏
- `trip_store.py` 等底层存储接口优先保持兼容

---

## 6. 关键功能数据流

## 6.1 登录与鉴权流

1. 前端登录页调用 `/api/auth/login`
2. 后端返回 token、用户信息、管理员标记
3. 前端保存：
   - token
   - username
   - display_name / user_name
   - is_admin
4. 之后 axios 拦截器自动注入认证头
5. 后端通过 Bearer token 或兼容逻辑恢复用户

---

## 6.2 行程规划流

1. 用户在规划页或对话场景中输入旅行需求
2. 前端调用 `/api/trip/parse`
3. 后端用 LLM 提取结构化字段
4. 当前端判定信息完整后，调用 `/api/trip/plan`
5. 多智能体生成完整行程 JSON
6. 前端展示结果
7. 用户可调用 `/api/trip/save` 持久化到历史

---

## 6.3 普通聊天 / 旅行顾问流

1. 前端创建或进入会话
2. 前端通过 SSE 打开 stream 接口
3. 后端按角色与上下文生成流式文本
4. 前端实时拼接内容
5. 页面把消息加入聊天历史

---

## 6.4 数字人引导流

1. Dashboard 始终挂载 `DigitalHuman.vue`
2. 用户点击浮窗进入引导模式
3. 组件根据当前页面构造上下文
4. 使用 `dh_` 前缀会话访问聊天流接口
5. 后端按数字人角色生成页面引导式回答
6. 前端再分段播放 TTS，并切换数字人表情

---

## 6.5 视觉问答流

1. 用户在聊天页上传图片并输入问题
2. 前端把表单数据发给视觉问答接口
3. 后端读取图片，转 base64
4. `llm_service.py` 调用 Qwen 兼容接口
5. 返回图片理解结果
6. 若多模态失败，回退到文本 LLM 的兜底回答

---

## 6.6 历史记录与广场同步流

1. 用户保存或打开历史行程
2. 前端读取 `/api/trip/history*` 接口
3. 用户在历史详情中选择同步到广场
4. 前端调用 `/api/plaza/sync`
5. 后端更新广场聚合文件与相关统计

---

## 6.7 视频生成流

1. 用户在视频页面输入景区名
2. 前端调用 `/api/video/generate`
3. 后端创建异步任务
4. `video_service.py` 执行脚本、音频、图片、渲染流水线
5. 前端轮询状态
6. 完成后获得下载地址并下载 mp4

---

## 7. 当前的重要实现约定

以下约定在后续优化中应优先保持：

### 7.1 `dh_` 会话前缀
用于区分数字人会话与普通聊天会话，不能随意修改。

### 7.2 `api.ts` 是前端 API 主入口
新增前端接口时，优先先放进 `frontend/src/services/api.ts`，避免继续把 `fetch()` 分散写回页面。

### 7.3 文件型存储仍是当前基础设施
本轮不替换为数据库。

### 7.4 路由兼容优先
后端优化时尽量不改变已有 API 路径与返回结构，减少前端联动成本。

### 7.5 配置统一从 `config.py` 读取
避免在业务代码中继续引入新的硬编码 key 或路径。

---

## 8. 当前已完成的优化

本轮已经完成的低风险优化包括：

1. **后端认证统一第一步**
   - `trip.py` 多个受保护接口改为通过 Bearer token 获取用户身份
   - `auth.py` 中更新显示名接口不再允许伪身份 fallback

2. **前端 API 集中化第一步**
   - 在 `api.ts` 中新增：
     - `getTripSuggestion`
     - `syncTripToPlaza`
     - `getAttractionDetail`
   - `History.vue` 已改用这些 API 方法

3. **前端 401 跳转与 history 路由兼容**
   - 统一使用 `window.location.assign('/login')`

4. **去除前端部分硬编码第三方 key 使用**
   - `History.vue` 中已移除直接硬编码高德 key 的请求方式

5. **Qwen 初始化卫生修复**
   - `llm_service.py` 改为显式传参初始化，去掉环境变量污染式实现

---

## 9. 当前仍需继续优化的热点

### 后端

#### `backend/app/api/routes/chat.py`
- 职责混杂
- `X-Username` 依赖仍多
- 与 plaza 内部实现耦合
- 地图/FAQ/SSE/角色分流混在同一文件

#### `backend/app/api/routes/plaza.py`
- 职责过重
- 仍有硬编码风险点
- Excel 绝对路径影响部署
- 适合拆 service

#### `backend/app/api/routes/video.py`
- 视频生成入口仍主要依赖 `X-Username`

#### `backend/app/api/routes/admin.py`
- 仍是混合认证模型

### 前端

#### `frontend/src/views/Home.vue`
- 仍有较多直接 `fetch()`
- 状态与副作用过于集中

#### `frontend/src/components/DigitalHuman.vue`
- 功能完整，但组件本身偏重
- 后续适合拆出 SSE / TTS / 语音识别逻辑

### 文档与验证

- README 需要与当前真实模块重新对齐
- 需要补跑针对性的启动或构建验证

---

## 10. 推荐阅读顺序

如果是新接手这个项目，建议按下面顺序阅读：

### 后端阅读顺序
1. `backend/app/api/main.py`
2. `backend/app/config.py`
3. `backend/app/models/schemas.py`
4. `backend/app/api/routes/auth.py`
5. `backend/app/api/routes/trip.py`
6. `backend/app/services/llm_service.py`
7. `backend/app/api/routes/chat.py`
8. `backend/app/api/routes/plaza.py`
9. `backend/app/api/routes/video.py`
10. `backend/app/services/video_service.py`

### 前端阅读顺序
1. `frontend/src/main.ts`
2. `frontend/src/services/api.ts`
3. `frontend/src/views/Dashboard.vue`
4. `frontend/src/views/Home.vue`
5. `frontend/src/views/History.vue`
6. `frontend/src/components/DigitalHuman.vue`
7. `frontend/src/views/VideoGenerate.vue`

### 视频子项目阅读顺序
1. `video-generator/package.json`
2. `video-generator/src/Root.tsx`
3. `video-generator/src/ScenicVideo.tsx`
4. `backend/app/services/video_service.py`

---

## 11. 后续维护建议

1. **先继续统一认证边界**
   - 优先减少 `X-Username` 的新扩散
   - 新接口尽量直接走 Bearer token

2. **优先拆 `chat.py` 与 `plaza.py`**
   - 先抽 helper/service，再缩薄 route

3. **继续收口前端原始请求**
   - 重点是 `Home.vue`

4. **继续清理配置硬编码**
   - 包括 key fallback 和绝对路径依赖

5. **保持 README 与本文档分层**
   - README 负责项目介绍、快速启动、模块索引
   - IMPLEMENTATION.md 负责功能实现与调用关系

---

## 12. 总结

这个项目当前的核心价值，不只是“自动生成旅行计划”，而是围绕旅行场景形成了一个多模块平台：

- 旅行规划
- 对话顾问
- 数字人引导
- 数据广场
- 管理后台
- 视频生成
- 多模态问答

理解它的正确方式，是把它看成：

> 一个以 FastAPI 为后端中枢、以 Vue Dashboard 为交互壳、以 JSON 文件为轻量存储、以多类 LLM / 地图 / 视频能力为扩展模块的旅行平台。

后续优化应继续遵循“低风险、高收益、保兼容”的原则推进。
