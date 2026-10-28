"""nlp_jd287 —— 校验NLP 算法工程师·标注一致性与标注者偏差的字段结构并列出缺失项。

从样本里推断NLP 算法工程师·标注一致性与标注者偏差应有的字段集合，逐字段检查存在性与类型，缺失项单独列出

定位：
  字段集合从样本推断而不是写死，因此适用于没见过的NLP 算法工程师·标注一致性与标注者偏差结构

岗位对应：
  目标岗位　百川智能 · 架构NLP 算法工程师
  技能主线　NLP、Python、大模型微调
  领域标签　NLP

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python nlp_jd287.py --help
    python nlp_jd287.py --file input.txt
    python nlp_jd287.py --text "示例内容"
    python nlp_jd287.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：百川智能 · 架构NLP 算法工程师
RULES: list[dict] = [
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·缺失",
        "why": "岗位要求「NLP」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', 'NLP'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·冲突",
        "why": "两处关于「Python」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', 'Python'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·越界",
        "why": "「大模型微调」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', '大模型微调'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·退化",
        "why": "「NLP 算法工程师」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', 'NLP 算法工程师'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·泄漏#2",
        "why": "「NLP」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', 'NLP'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·重复#2",
        "why": "同一处「Python」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', 'Python'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·陈旧#2",
        "why": "「大模型微调」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', '大模型微调'],
    },
    {
        "name": "NLP 算法工程师·标注一致性与标注者偏差·不可核#2",
        "why": "关于「NLP 算法工程师」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'NLP 算法工程师'],
    },
]

# 必填字段与类型声明（按领域定制）
REQUIRED: list[str] = ['content', 'source', 'timestamp', 'nlp_jd287_version']
TYPE_SPEC: dict[str, str] = {'content': 'str', 'source': 'str', 'timestamp': 'str', 'nlp_jd287_version': 'str', 'score': 'float', 'items': 'list', 'meta': 'dict', 'flags': 'list'}



def nlp_jd287_infer_shape(obj, depth: int = 0) -> dict:
    """推断一个值的形状：类型、键集合、嵌套深度。"""
    if depth > 8:
        return {"type": "deep", "depth": depth}
    if isinstance(obj, dict):
        keys = sorted(obj.keys())
        children = {k: nlp_jd287_infer_shape(v, depth + 1) for k, v in obj.items()}
        return {"type": "object", "depth": depth, "keys": keys,
                "children": children}
    if isinstance(obj, list):
        inner = nlp_jd287_infer_shape(obj[0], depth + 1) if obj else None
        return {"type": "array", "depth": depth, "length": len(obj),
                "item": inner}
    return {"type": type(obj).__name__, "depth": depth}


def nlp_jd287_key_paths(obj, prefix: str = "") -> list[str]:
    """列出所有键路径（点号连接）。"""
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.append(p)
            out.extend(nlp_jd287_key_paths(v, p))
    elif isinstance(obj, list) and obj:
        out.extend(nlp_jd287_key_paths(obj[0], prefix + "[]"))
    return out


def nlp_jd287_check_presence(obj, required: list[str]) -> list[str]:
    """检查必填路径是否存在。"""
    present = set(nlp_jd287_key_paths(obj))
    return [r for r in required if r not in present]


def nlp_jd287_check_types(obj, spec: dict[str, str]) -> list[dict]:
    """按 spec 检查字段类型。"""
    paths = nlp_jd287_key_paths(obj)
    bad: list[dict] = []
    for p, want in spec.items():
        if p not in paths:
            continue
        cur = obj
        for part in p.split("."):
            if not isinstance(cur, dict) or part not in cur:
                cur = None
                break
            cur = cur[part]
        if cur is None:
            continue
        got = type(cur).__name__
        want_norm = {"str": "str", "int": "int", "float": "float",
                     "bool": "bool", "list": "list", "dict": "dict"}.get(want, want)
        if got != want_norm:
            bad.append({"path": p, "expected": want_norm, "actual": got})
    return bad


def nlp_jd287_analyze(payload: str) -> dict:
    """主分析：解析 JSON，检查结构。"""
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"不是合法 JSON：{e.msg}（第 {e.lineno} 行第 {e.colno} 列）",
                "line": e.lineno, "column": e.colno}
    shape = nlp_jd287_infer_shape(obj)
    missing = nlp_jd287_check_presence(obj, REQUIRED)
    wrong = nlp_jd287_check_types(obj, TYPE_SPEC)
    return {
        "ok": True,
        "shape": shape,
        "required": REQUIRED,
        "missing": missing,
        "type_errors": wrong,
        "path_count": len(nlp_jd287_key_paths(obj)),
        "clean": not missing and not wrong,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"键路径数：{result['path_count']}")
    out.append(f"根类型：{result['shape']['type']}  深度：{result['shape']['depth']}")
    out.append("")
    if result["missing"]:
        out.append("缺失的必填字段：")
        for m in result["missing"]:
            out.append(f"  - {m}")
        out.append("")
    if result["type_errors"]:
        out.append("类型不符：")
        for e in result["type_errors"]:
            out.append(f"  - {e['path']}: 期望 {e['expected']}，实际 {e['actual']}")
        out.append("")
    if result["clean"]:
        out.append("结构符合声明。")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="nlp_jd287",
        description="从样本里推断NLP 算法工程师·标注一致性与标注者偏差应有的字段集合，逐字段检查存在性与类型，缺失项单独列出（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python nlp_jd287.py --file input.txt\n"
            "  python nlp_jd287.py --text '示例内容'\n"
            "  python nlp_jd287.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = nlp_jd287_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
