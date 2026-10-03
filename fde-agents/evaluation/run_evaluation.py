"""FDE 智能风控 Agent 效果评测脚本。

用法：
    python run_evaluation.py --mode local   # 直接调用规则引擎（不依赖服务，默认）
    python run_evaluation.py --mode api     # 调用 fde-agents /analyze HTTP 接口（需 8001 运行）

输出：
    report.json（结构化结果）+ 控制台汇总
指标：
    分级命中率、评分命中率、审批决策一致率、综合准确率、误杀率（预期低风险被判中/高）
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # fde-agents/
sys.path.insert(0, str(ROOT))

DATASET = Path(__file__).resolve().parent / "dataset.json"

# 决策规则（与 approval_advisor 规则兜底一致：<40 approve，>=40 human）
RISK_MEDIUM_THRESHOLD = 40
RISK_HIGH_THRESHOLD = 70


def _rule_decision(score: float) -> str:
    if score >= RISK_MEDIUM_THRESHOLD:
        return "human"
    return "approve"


def _rule_predict(purchase_request: dict) -> dict:
    """本地模式：规则引擎 + 审批建议兜底。"""
    from app.services.risk_rules import compute_rule_score
    result = compute_rule_score(purchase_request)
    return {
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "approval_decision": _rule_decision(result["risk_score"]),
        "summary": result["summary"],
    }


async def _api_predict(purchase_request: dict, base_url: str) -> dict:
    """API 模式：调用 fde-agents /analyze 全链路（失败重试 2 次）。"""
    import urllib.request
    payload = json.dumps({
        "request_id": "eval",
        "purchase_request": purchase_request,
    }).encode("utf-8")
    last_exc = None
    for _attempt in range(2):
        try:
            req = urllib.request.Request(
                f"{base_url}/analyze",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(1.5)
    else:
        data = {"final_result": {}, "summary": f"request failed: {last_exc}"}
    fr = data.get("final_result") or {}
    score = fr.get("risk_score")
    level = fr.get("risk_level")
    raw_decision = fr.get("approval_decision") or data.get("approval_decision")
    if raw_decision in ("human", "reject", "supplement"):
        decision = "human"
    elif raw_decision == "approve":
        decision = "approve"
    else:
        decision = _rule_decision(score)
    return {
        "risk_score": float(score) if score is not None else -1,
        "risk_level": level or "unknown",
        "approval_decision": decision,
        "summary": fr.get("summary") or data.get("summary") or "",
    }


def _hit_range(score: float, rng) -> bool:
    lo, hi = rng
    return lo <= score <= hi


async def main() -> None:
    parser = argparse.ArgumentParser(description="FDE Agent 效果评测")
    parser.add_argument("--mode", choices=["local", "api"], default="local")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    args = parser.parse_args()

    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    print(f"载入评测集：{len(cases)} 条（mode={args.mode}）\n")

    rows = []
    stats = {
        "total": len(cases),
        "level_hits": 0, "score_hits": 0, "decision_hits": 0, "all_hits": 0,
        "low_cases": 0, "killed_low": 0,  # 误杀：预期 low 被判 medium/high
        "level_dist": {"low": 0, "medium": 0, "high": 0},
        "pred_dist": {"low": 0, "medium": 0, "high": 0},
    }

    for i, case in enumerate(cases, start=1):
        pr = case["purchase_request"]
        exp = case["expected"]
        if args.mode == "local":
            pred = _rule_predict(pr)
        else:
            try:
                pred = await _api_predict(pr, args.base_url)
            except Exception as exc:
                pred = {"risk_score": -1, "risk_level": "error", "approval_decision": "error", "summary": str(exc)}

        level_hit = pred["risk_level"] == exp["risk_level"]
        score_hit = pred["risk_score"] >= 0 and _hit_range(pred["risk_score"], exp["risk_score_range"])
        decision_hit = pred["approval_decision"] == exp["approval_decision"]
        all_hit = level_hit and score_hit and decision_hit

        stats["level_hits"] += int(level_hit)
        stats["score_hits"] += int(score_hit)
        stats["decision_hits"] += int(decision_hit)
        stats["all_hits"] += int(all_hit)
        stats["level_dist"][exp["risk_level"]] = stats["level_dist"].get(exp["risk_level"], 0) + 1
        if pred["risk_level"] in stats["pred_dist"]:
            stats["pred_dist"][pred["risk_level"]] += 1
        if exp["risk_level"] == "low":
            stats["low_cases"] += 1
            if pred["risk_level"] in ("medium", "high"):
                stats["killed_low"] += 1

        rows.append({
            "id": case["id"], "name": case["name"],
            "expected_level": exp["risk_level"], "pred_level": pred["risk_level"],
            "expected_score": exp["risk_score_range"], "pred_score": pred["risk_score"],
            "expected_decision": exp["approval_decision"], "pred_decision": pred["approval_decision"],
            "level_hit": level_hit, "score_hit": score_hit, "decision_hit": decision_hit, "all_hit": all_hit,
        })

    n = stats["total"]
    summary = {
        "mode": args.mode,
        "dataset": str(DATASET),
        "total": n,
        "risk_level_accuracy": round(stats["level_hits"] / n * 100, 2),
        "risk_score_accuracy": round(stats["score_hits"] / n * 100, 2),
        "decision_consistency": round(stats["decision_hits"] / n * 100, 2),
        "overall_accuracy": round(stats["all_hits"] / n * 100, 2),
        "false_kill_rate": round(stats["killed_low"] / stats["low_cases"] * 100, 2) if stats["low_cases"] else 0.0,
        "level_distribution": stats["level_dist"],
        "prediction_distribution": stats["pred_dist"],
        "details": rows,
    }

    # 控制台输出
    print(f"{'ID':<4}{'名称':<26}{'预期':<10}{'预测':<10}{'分预期':<8}{'分实际':<8}{'决策':<10}{'结果'}")
    for r in rows:
        mark = "OK" if r["all_hit"] else "FAIL"
        print(f"{r['id']:<4}{r['name']:<26}{r['expected_level']:<10}{r['pred_level']:<10}{str(r['expected_score']):<8}{r['pred_score']:<8}{r['expected_decision'] + '->' + r['pred_decision']:<12}{mark}")
    print("\n===== 汇总指标 =====")
    for k in ("risk_level_accuracy", "risk_score_accuracy", "decision_consistency", "overall_accuracy", "false_kill_rate"):
        print(f"{k}: {summary[k]}")
    print(f"样本分布(预期): {summary['level_distribution']}")
    print(f"样本分布(预测): {summary['prediction_distribution']}")

    OUT_JSON = Path(__file__).resolve().parent / f"report_{args.mode}.json"
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: {OUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
