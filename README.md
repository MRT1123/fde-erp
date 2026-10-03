# FDE + ERP 智能采购风控系统

> Forward Deployed Engineering 面试项目：把 AI Agent 嵌入企业采购审批流程，实现「风险自动识别 + 高风险人工审批 + 飞书联动 + 预算管控 + 采购订单与收货入库」的完整业务闭环。

## 项目简介

本项目由四个子系统组成：

| 子系统 | 目录 | 技术栈 | 职责 |
|--------|------|--------|------|
| **ERP 智能采购管理系统（后端）** | `erp-backend/` | FastAPI · SQLAlchemy 2.0 · SQLite（开发）/ PostgreSQL（生产） | 采购申请、供应商、物料、库存、审批、预算、采购订单、审计 |
| **ERP 管理前端** | `erp-web/` | Vue 3 · Element Plus · ECharts · TypeScript | 数据看板、采购申请、审批工作台、供应商/物料/库存、预算管控、采购订单、风控分析 |
| **FDE 智能风控 Agent 系统** | `fde-agents/` | LangGraph · LLM（OpenAI 兼容，可降级规则引擎） | 风险分析、供应商尽调、审批建议、异常检测 |
| **FDE 前端** | `fde-web/` | Vue 3 | Agent 运行观测 |

**核心流程（完整业务闭环）：**

```
用户提交采购申请
    ↓
[风险分析 Agent] → 综合风险评分（0-100）
    ↓
[供应商尽调 Agent] → 背景报告（联网搜索）
    ↓
[审批建议 Agent] → 通过/驳回/补充材料/转人工
    ↓
[预算校验] → budget_status 落库（ok / over_budget / unknown），超预算计入风险维度
    ↓
    ├─ 风险 < 40 → 自动通过
    └─ 风险 ≥ 40 → 人工审批（≥ 70 强制）→ 飞书审批流 → Webhook 回调
    ↓
审批通过 → 生成采购订单（PurchaseOrder）
    ↓
收货入库 → 更新库存 + 库存流水（reference_type=purchase_order）
```

## 目录结构

```
.
├── erp-backend/              # ERP 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/          # REST API（采购/审批/供应商/物料/库存/预算/采购订单/看板/Webhook）
│   │   ├── core/            # 配置、数据库、安全、日志
│   │   ├── models/          # SQLAlchemy ORM 模型（20 张表）
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 业务逻辑（审批流、风险路由、预算、采购订单、飞书、Agent 客户端）
│   └── Dockerfile
├── erp-web/                  # ERP 前端（Vue 3 + Element Plus）
│   └── src/
│       ├── api/             # axios 封装 + 类型定义 + API 函数
│       ├── layout/          # 侧边导航布局
│       ├── router/          # 路由（含 预算管控 / 采购订单）
│       └── views/           # 页面（Dashboard/PurchaseRequests/Approvals/Suppliers/Materials/Inventory/Budget/PurchaseOrders/FdeRisk）
├── fde-agents/              # FDE Agent 服务（LangGraph）
│   ├── app/
│   │   ├── graph/          # LangGraph 工作流（Supervisor 多 Agent 编排）
│   │   ├── agents/         # 4 个 Agent（风险分析/尽调/审批建议/异常检测）
│   │   └── services/       # LLM、规则引擎（risk_rules）、搜索
│   ├── evaluation/         # Agent 效果评测（评测集 + 跑批脚本 + 报告）
│   │   ├── dataset.json    # 25 条标注评测集
│   │   ├── run_evaluation.py
│   │   ├── report_local.json / report_api.json
│   │   └── ...
│   └── Dockerfile
├── fde-web/                 # FDE Agent 观测前端
├── docs/
│   ├── database.md         # 数据库设计文档
│   └── evaluation.md       # Agent 效果评测报告（指标定义、结果、结论）
├── scripts/
│   └── seed_data.py        # 演示数据种子脚本
├── docker-compose.yml      # 一键容器化部署
├── start-all.cmd           # Windows 一键启动（后端×2 + 前端×2）
├── stop-all.cmd            # Windows 一键停止
├── .env.example            # 环境变量模板
└── .github/workflows/      # GitHub Actions CI
```

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
cp .env.example .env          # 按需填写飞书/LLM 配置
docker compose up --build
```

启动后：
- ERP API：http://localhost:8000 （Swagger: /docs）
- Agent 服务：http://localhost:8001 （Swagger: /docs）
- ERP 前端：http://localhost:5173
- 健康检查：`curl http://localhost:8000/health`

### 方式二：Windows 一键启动（本地测试推荐）

```cmd
start-all.cmd     # 一键启动：自动按端口停旧，拉起 后端×2 + 前端×2 独立窗口
stop-all.cmd      # 一键停止：按端口 8000/8001/5173/5174 全部停止
```

- 默认使用 SQLite（`erp_dev.db`），**零外部依赖**，无需安装 Postgres/Redis，双击即用；
- 启动后同上：ERP API :8000、Agent 服务 :8001、ERP 前端 http://localhost:5173、FDE 前端 http://localhost:5174。

### 方式三：手动本地开发

需要 Python 3.12+ 与 Node.js 18+。

```bash
# ERP 后端
cd erp-backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# FDE Agent（另开终端）
cd fde-agents
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# ERP 前端（另开终端）
cd erp-web
npm install
npm run dev            # http://localhost:5173
```

初始化数据库：

```bash
cd erp-backend
python ../scripts/seed_data.py  # 写入演示数据（含部门预算上限）
```

> 注：当前开发环境使用 SQLite（`erp_dev.db`），新模型表可通过 `Base.metadata.create_all` 自动补齐；生产环境使用 PostgreSQL + Alembic 迁移。

## 核心设计

### 风险评分与人工审批路由

- 综合风险评分 = 各维度权重之和（金额阶梯/新供应商/品类异常/供应商风险/频率异常/超预算）
- **金额阶梯**：≥ 5万 +30 ｜ ≥ 20万 +45 ｜ ≥ 50万 +60
- **其他维度**：新供应商 +25 ｜ 品类异常 +20 ｜ 供应商风险 +25 ｜ 采购频率 +15 ｜ 超预算 +20
- **≥ 70 分**：高风险 → 强制人工审批（不可跳过），路由到飞书审批流并附带 AI 分析报告
- **40-69 分**：中风险 → 默认人工审批
- **< 40 分**：低风险 → 自动通过

规则引擎在 `erp-backend/app/services/risk_service.py`（ERP 降级兜底）与 `fde-agents/app/services/risk_rules.py`（FDE 端）保持双端一致。

### 预算管控模块（新增）

**预算口径**（`erp-backend/app/services/budget_service.py`）：

| 指标 | 定义 |
|------|------|
| 预算上限 | 部门年度 `budget_limit`（元） |
| used（已用） | `status=approved` 采购单金额合计 |
| pending（在途） | `status in (analyzing, pending_approval, approving)` 金额合计 |
| available（可用） | `limit - used - pending` |
| utilization（使用率） | `(used + pending) / limit × 100%` |
| budget_status | `ok`（扣减后 ≥0）／ `over_budget`（扣减后 <0）／ `unknown`（部门未设上限） |

**生效链路：**
1. 采购申请提交后，Agent 分析阶段调用 `check_budget_for_request`（排除本单自身），把 `budget_status` 落库（`apply_agent_result`）；
2. `over_budget` 作为独立维度传入 FDE 风险分析（`agent_flow._build_payload`），超预算采购自动 +20 风险分；
3. 部门预算总览页实时展示各部门上限/已用/在途/可用/使用率/状态。

**API：**
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/budget/departments` | 部门预算总览列表 |
| GET | `/api/v1/budget/departments/{id}` | 单部门明细 + 采购单预算明细 |
| PUT | `/api/v1/budget/departments/{id}/limit` | 设置/更新部门预算上限 |

**前端**：`erp-web/src/views/Budget.vue`（侧边导航「预算管控」），含使用率进度条、超预算标红、设置上限对话框、明细抽屉。

### 采购订单 + 收货入库模块（新增）

**模型**（`erp-backend/app/models/purchase_order.py`）：
- `PurchaseOrder`：订单号（PO+日期+3位序号，按最大序号递增、兼容删除空洞）、关联采购申请（唯一，防重复下单）、供应商/部门、总额、状态机
- `PurchaseOrderItem`：物料、规格、数量、单价、金额、累计收货量 `received_quantity`

**状态机**：`confirmed（待收货）→ partial_received（部分收货）→ received（已收货）`，未完全收货前可 `cancelled`。

**生效链路：**
1. 采购申请审批通过（`status=approved`）后，可在前端「采购订单」页一键生成订单（仅 approved 且未下单的申请可下单，重复下单返回 409）；
2. 收货时逐行校验不超过剩余可收量，更新 `received_quantity`；
3. 库存联动：`Inventory.quantity` 增加 + 写入 `StockMovement(movement_type=in, reference_type="purchase_order", reference_id=订单ID)`——库存预留字段 `reference_type=purchase_order` 正式启用；
4. 全部收齐自动置 `received`，部分收货置 `partial_received`；未关联物料的明细拒绝入库（防呆）。

**API：**
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/purchase-orders` | 订单列表（含供应商/部门/申请单号） |
| GET | `/api/v1/purchase-orders/eligible` | 可下单的已审批采购申请 |
| GET | `/api/v1/purchase-orders/{id}` | 订单详情（含明细与收货量） |
| POST | `/api/v1/purchase-orders/from-request/{request_id}` | 由审批通过的申请生成订单 |
| POST | `/api/v1/purchase-orders/{id}/receive` | 收货入库（明细收货量 + 库存 + 流水） |
| POST | `/api/v1/purchase-orders/{id}/cancel` | 取消订单 |

**前端**：`erp-web/src/views/PurchaseOrders.vue`（侧边导航「采购订单」），含生成订单对话框、订单详情抽屉、收货入库表单。

### Agent 效果评测（新增）

评测系统位于 `fde-agents/evaluation/`，用于量化 FDE 风险分析 Agent 的准确性、分级能力与决策一致性。

**评测集**：`dataset.json`，25 条人工标注样本，覆盖：
- 三档风险级别：低（<40）/ 中（40-69）/ 高（≥70）
- 金额边界：5万（+30）、20万（+45）、50万（+60）及临界值 4.9万/19.9万
- 维度组合：新供应商、品类异常、供应商风险、频率、超预算，及多维叠加
- 每条样本含输入字段（total_amount / first_cooperation / supplier_risk / category_mismatch / frequency_risk / over_budget / supplier_name）与预期（risk_level / risk_score / approval_decision）

**跑批脚本**：`run_evaluation.py`，支持两种模式：
```bash
# 本地规则引擎直调（稳定可复现，不依赖服务与 LLM）
python evaluation/run_evaluation.py --mode local
# HTTP 全链路（调 8001 /analyze，含尽调子图与 LLM）
python evaluation/run_evaluation.py --mode api
```

**指标定义**：
| 指标 | 定义 |
|------|------|
| 风险分级命中率 | 预测 risk_level 与标注一致的比例 |
| 风险分命中率 | 预测 risk_score 落在标注区间（±容差）的比例 |
| 审批决策一致率 | 预测 approval_decision 与标注一致的比例 |
| 综合准确率 | 级别+分数+决策三项全对的比例 |
| 误杀率 | 低风险样本被误判为中/高风险的比例 |

**评测结论（2026-10-03）**：
- 本地规则引擎：25/25 全中，全部指标 100%（规则实现与标注一致）
- HTTP 全链路：补充供应商上下文后 25/25 全中；未补充供应商信息时，尽调子图会把「未知供应商」作为风险信号强制转人工（保护性兜底，符合预期）

完整报告见 [`docs/evaluation.md`](docs/evaluation.md)。

### 状态机

```
draft → analyzing → pending_approval → approving → approved → 生成采购订单 → 收货入库
                                      → rejected
                                      → withdrawn
                                      → escalated（超时 48h 自动升级）
异常：needs_manual_review（Agent 失败）/ callback_error（Webhook 回调失败）
```

### 数据库

20 张表覆盖基础数据、采购、审批、预算、采购订单、库存、审计与 Agent 决策数据，完整设计见 [`docs/database.md`](docs/database.md)。

## 测试与 CI

```bash
# ERP 后端单测
cd erp-backend
pytest

# Agent 效果评测（详见上文「Agent 效果评测」）
cd fde-agents
python evaluation/run_evaluation.py --mode local
```

GitHub Actions 配置见 `.github/workflows/ci.yml`：提交自动执行 lint + 单测 + Docker 镜像构建。

## 面试亮点

1. **真实 FDE 场景**：AI 嵌入真实采购审批业务流程，覆盖「申请 → 风控 → 审批 → 预算 → 下单 → 收货入库」完整闭环，而非玩具 demo。
2. **人机协作**：LangGraph 状态机 + 高风险人工审批路由，体现「人在环上（Human-in-the-loop）」；低风险自动放行提升效率。
3. **Agent 可评测**：25 条标注评测集 + 跑批脚本 + 量化指标，AI 效果可度量、可回归。
4. **完整审计**：Agent 决策、审批动作、预算校验、收货流水全部落审计日志，可全链路回溯。
5. **工程化**：Docker 容器化、CI/CD、种子数据（含部门预算）、双端规则引擎一致，开箱即用。
