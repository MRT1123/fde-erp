# FDE + ERP 智能采购风控系统 · 数据库设计文档

> 版本：v1.0 ｜ 日期：2026-10-01 ｜ 数据库：PostgreSQL 16
> 技术栈：SQLAlchemy 2.0（异步）+ Alembic 迁移
> 关联方案：`FDE_ERP_项目方案.html`

---

## 1. 设计原则

1. **业务主数据与流程数据分离**：部门/员工/物料/供应商为主数据，采购申请/审批/库存流水为流程数据。
2. **审计优先**：所有审批动作落 `approval_actions`，所有关键操作落 `audit_logs`，Agent 决策单独落表，满足合规与面试亮点。
3. **快照字段**：采购明细保存物料名称快照，审批保存风险评分快照，避免历史被后续修改污染。
4. **风险链路可追溯**：`purchase_requests` → `risk_assessments` → `supplier_due_diligence` → `agent_decisions` → `approvals`，一条采购单可完整回溯 AI 决策与人工审批全过程。
5. **金额用整数（分）**：本设计金额字段采用数值型（元），实际生产建议改为 `NUMERIC(12,2)` 或存储分为单位的整数，避免浮点误差。当前骨架用 `Integer` 简化，正式迁移前需调整为 `Numeric`。

---

## 2. ER 概览（表清单）

| # | 表名 | 模块 | 说明 |
|---|------|------|------|
| 1 | `departments` | 基础数据 | 部门（审批路由、预算控制） |
| 2 | `employees` | 基础数据 | 员工/用户（角色：申请人/部门审批人/高级审批人/管理员） |
| 3 | `materials` | 基础数据 | 物料主数据 |
| 4 | `suppliers` | 供应商 | 供应商主数据 |
| 5 | `supplier_ratings` | 供应商 | 供应商评级记录 |
| 6 | `purchase_requests` | 采购 | 采购申请（审批链路核心） |
| 7 | `purchase_items` | 采购 | 采购明细行 |
| 8 | `approvals` | 审批 | 审批实例 |
| 9 | `approval_actions` | 审批 | 审批操作流水 |
| 10 | `inventories` | 库存 | 库存快照 |
| 11 | `stock_movements` | 库存 | 库存变动流水 |
| 12 | `audit_logs` | 审计 | 统一审计日志 |
| 13 | `risk_assessments` | FDE Agent | 风险分析输出 |
| 14 | `supplier_due_diligence` | FDE Agent | 供应商尽调报告 |
| 15 | `agent_decisions` | FDE Agent | 审批建议输出 |
| 16 | `anomaly_alerts` | FDE Agent | 异常检测告警 |
| 17 | `agent_runs` | FDE Agent | Agent 工作流运行记录 |
| 18 | `risk_configs` | FDE Agent | 风险规则配置 |

---

## 3. 表结构明细

### 3.1 基础数据

#### departments（部门）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | autoincrement | |
| name | VARCHAR(100) | NOT NULL | 部门名称 |
| code | VARCHAR(50) | UNIQUE NOT NULL | 部门编码 |
| parent_id | BIGINT FK→departments.id | NULL | 上级部门 |
| manager_id | BIGINT FK→employees.id | NULL | 部门负责人 |
| budget_limit | INT | NULL | 年度预算上限（元） |
| description | VARCHAR(255) | NULL | |
| created_at / updated_at | TIMESTAMPTZ | NOT NULL | |

#### employees（员工/用户）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| employee_no | VARCHAR(50) | UNIQUE NOT NULL | 工号 |
| name | VARCHAR(100) | NOT NULL | 姓名 |
| email | VARCHAR(120) | UNIQUE | |
| phone | VARCHAR(30) | | |
| department_id | BIGINT FK→departments.id | | 所属部门 |
| role | VARCHAR(30) | default `applicant` | `applicant` / `department_approver` / `senior_approver` / `admin` |
| approval_limit | INT | NULL | 审批额度上限（元） |
| feishu_user_id | VARCHAR(100) | | 飞书用户 ID |
| status | VARCHAR(20) | default `active` | `active` / `disabled` / `leave` |
| password_hash | VARCHAR(255) | | |

#### materials（物料）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| code | VARCHAR(50) | UNIQUE NOT NULL | 物料编码 |
| name | VARCHAR(150) | NOT NULL | 物料名称 |
| category | VARCHAR(50) | NOT NULL | 品类：办公/IT/生产/服务 |
| spec | VARCHAR(255) | | 规格型号 |
| unit | VARCHAR(20) | default `件` | 计量单位 |
| default_price | INT | | 参考单价 |
| status | VARCHAR(20) | default `active` | |

### 3.2 供应商

#### suppliers（供应商）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| code | VARCHAR(50) | UNIQUE NOT NULL | 供应商编码 |
| name | VARCHAR(150) | NOT NULL | 供应商名称 |
| contact_person / phone / email / address | 文本 | | |
| tax_no | VARCHAR(50) | | 统一社会信用代码 |
| qualification_status | VARCHAR(20) | default `pending` | `pending`/`verified`/`rejected` |
| risk_level | VARCHAR(20) | default `low` | `low`/`medium`/`high` |
| credit_score | INT | | 信用评分 0-100 |
| first_cooperation | BOOL | default false | 是否首次合作 |
| status | VARCHAR(20) | default `active` | |

#### supplier_ratings（供应商评级）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| supplier_id | BIGINT FK→suppliers.id | INDEX | |
| rating_date | DATE | NOT NULL | 评级日期 |
| score | INT | NOT NULL | 0-100 |
| level | VARCHAR(20) | NOT NULL | A/B/C/D |
| comment | TEXT | | |
| rated_by | BIGINT FK→employees.id | | 评级人 |

### 3.3 采购

#### purchase_requests（采购申请）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| request_no | VARCHAR(40) | UNIQUE NOT NULL | 申请单号，如 PR20261001001 |
| title | VARCHAR(200) | NOT NULL | 采购标题 |
| applicant_id | BIGINT FK→employees.id | INDEX | 申请人 |
| department_id | BIGINT FK→departments.id | INDEX | 申请部门 |
| supplier_id | BIGINT FK→suppliers.id | | 拟选供应商 |
| total_amount | INT | NOT NULL | 总金额（元） |
| currency | VARCHAR(10) | default `CNY` | |
| purpose | TEXT | | 采购用途 |
| status | VARCHAR(30) | INDEX | 见状态机 |
| risk_score | INT | | Agent 综合风险评分 |
| risk_level | VARCHAR(20) | | low/medium/high |
| needs_human_review | BOOL | default false | 是否路由人工审批 |
| budget_status | VARCHAR(20) | | ok/over_budget/unknown |
| agent_summary | TEXT | | Agent 分析摘要 |
| feishu_instance_code | VARCHAR(100) | | 飞书审批实例 code |
| submitted_at | TIMESTAMPTZ | | 提交时间 |

**状态机**：`draft`（待提交）→ `analyzing`（Agent 分析中）→ `pending_approval`（待审批）→ `approving`（审批中）→ `approved`（已通过）/ `rejected`（已驳回）/ `withdrawn`（已撤回）/ `escalated`（超时升级）。异常态：`needs_manual_review`（Agent 分析失败转人工）、`callback_error`（飞书回调异常）。

#### purchase_items（采购明细）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| purchase_request_id | BIGINT FK→purchase_requests.id | INDEX | |
| material_id | BIGINT FK→materials.id | | 可空（手工填写物料） |
| material_name | VARCHAR(150) | NOT NULL | 名称快照 |
| spec | VARCHAR(255) | | |
| quantity | FLOAT | NOT NULL | 数量 |
| unit_price | INT | | 单价 |
| amount | INT | NOT NULL | 行金额 |
| remark | TEXT | | |

### 3.4 审批

#### approvals（审批实例）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| purchase_request_id | BIGINT FK→purchase_requests.id | INDEX | |
| approval_no | VARCHAR(40) | UNIQUE NOT NULL | 审批编号 |
| feishu_instance_code | VARCHAR(100) | | 飞书审批实例 code |
| approver_id | BIGINT FK→employees.id | | 当前审批人 |
| status | VARCHAR(30) | default `pending` | pending/approving/approved/rejected/escalated |
| decision | VARCHAR(20) | | approved/rejected |
| comment | TEXT | | 审批意见 |
| risk_score_snapshot | INT | | 审批时风险快照 |
| started_at / finished_at | TIMESTAMPTZ | | |
| timeout_at | TIMESTAMPTZ | | 预计超时时间 |
| escalated_to | BIGINT FK→employees.id | | 超时升级目标 |
| escalated_at | TIMESTAMPTZ | | |

#### approval_actions（审批操作流水）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| approval_id | BIGINT FK→approvals.id | INDEX | |
| action | VARCHAR(30) | NOT NULL | submit/accept/approve/reject/withdraw/escalate/transfer |
| operator_id | BIGINT FK→employees.id | | |
| comment | TEXT | | |
| from_status / to_status | VARCHAR(30) | | 状态转移前后 |

### 3.5 库存

#### inventories（库存快照）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| material_id | BIGINT FK→materials.id | INDEX | |
| warehouse | VARCHAR(50) | default `default` | |
| quantity | FLOAT | default 0 | 可用库存 |
| reserved_quantity | FLOAT | default 0 | 预留库存 |
| safety_stock | FLOAT | | 安全库存（预警线） |
| updated_at | TIMESTAMPTZ | NOT NULL | |

#### stock_movements（库存流水）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| material_id | BIGINT FK→materials.id | INDEX | |
| movement_type | VARCHAR(20) | NOT NULL | in/out/adjust |
| quantity | FLOAT | NOT NULL | 变动数量 |
| reference_type / reference_id | | | 来源追溯 |
| operator_id | BIGINT FK→employees.id | | |
| remark | TEXT | | |

### 3.6 审计

#### audit_logs（审计日志）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| user_id | BIGINT | | 操作人 |
| actor_type | VARCHAR(20) | default `user` | user/agent/system |
| action | VARCHAR(50) | NOT NULL | |
| entity_type | VARCHAR(50) | INDEX | |
| entity_id | BIGINT | INDEX | |
| detail | JSON | | 变更详情 |
| ip | VARCHAR(45) | | |

### 3.7 FDE Agent 数据

#### risk_assessments（风险分析）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| purchase_request_id | BIGINT FK | INDEX | |
| risk_score | FLOAT | NOT NULL | 综合评分 0-100 |
| risk_level | VARCHAR(20) | NOT NULL | |
| dimensions | JSON | | 各维度得分 |
| analysis | TEXT | | 风险点说明 |
| model_used | VARCHAR(100) | | |
| created_at | TIMESTAMPTZ | NOT NULL | |

#### supplier_due_diligence（供应商尽调）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| supplier_id | BIGINT FK | INDEX | |
| report_date | TIMESTAMPTZ | NOT NULL | |
| business_info | JSON | | 工商信息 |
| news | JSON | | 舆情列表 |
| risk_flags | JSON | | 风险信号 |
| risk_level | VARCHAR(20) | | |
| report_content | TEXT | | 报告文本 |

#### agent_decisions（审批建议）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| purchase_request_id | BIGINT FK | INDEX | |
| decision | VARCHAR(30) | NOT NULL | approve/reject/supplement/human |
| confidence | FLOAT | | 置信度 |
| reasons | JSON | | 决策理由 |

#### anomaly_alerts（异常告警）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| alert_type | VARCHAR(30) | NOT NULL | split_order/supplier_churn/amount_spike |
| target_type | VARCHAR(30) | NOT NULL | |
| target_id | BIGINT | | |
| description | TEXT | NOT NULL | |
| severity | VARCHAR(20) | default `info` | |
| status | VARCHAR(20) | default `open` | open/acknowledged/resolved |

#### agent_runs（工作流运行记录）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| purchase_request_id | BIGINT FK | INDEX | |
| workflow_name | VARCHAR(50) | default `procurement_review` | |
| status | VARCHAR(20) | default `running` | running/succeeded/failed/human_waiting |
| current_node | VARCHAR(50) | | |
| state_snapshot | JSON | | LangGraph 状态快照 |
| started_at / finished_at | TIMESTAMPTZ | | |

#### risk_configs（风险规则配置）
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT PK | | |
| dimension | VARCHAR(30) | UNIQUE NOT NULL | amount/new_supplier/category/supplier_risk/frequency/budget |
| weight | FLOAT | default 0 | 风险权重 |
| threshold | FLOAT | | 触发阈值 |
| condition | VARCHAR(255) | | 触发条件 |
| description | VARCHAR(255) | | |
| enabled | BOOL | default true | |

---

## 4. 关键关系

```text
departments 1 ── n employees
employees  1 ── n purchase_requests (申请人)
departments 1 ── n purchase_requests (申请部门)
suppliers  1 ── n purchase_requests
purchase_requests 1 ── n purchase_items
purchase_requests 1 ── 1 risk_assessments
purchase_requests 1 ── 1 agent_decisions
suppliers  1 ── n supplier_due_diligence
purchase_requests 1 ── n approvals
approvals  1 ── n approval_actions
materials  1 ── n inventories
materials  1 ── n stock_movements
```

---

## 5. 索引建议

- `purchase_requests(status)`、`purchase_requests(applicant_id)`、`purchase_requests(department_id)`
- `approvals(purchase_request_id)`、`approval_actions(approval_id)`
- `risk_assessments(purchase_request_id)`、`agent_decisions(purchase_request_id)`
- `audit_logs(entity_type, entity_id)`
- 分页/统计可加组合索引：`purchase_requests(status, created_at)`

---

## 6. 迁移计划

- 使用 Alembic 管理迁移：`alembic revision --autogenerate` 生成，`alembic upgrade head` 应用。
- 种子数据脚本：`scripts/seed_data.py` 提供部门/员工/物料/供应商演示数据，便于本地开发与演示。
