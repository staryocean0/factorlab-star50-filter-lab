#!/usr/bin/env python3
"""Repository lifecycle, generated entry points and isolated contract-test runner.

No market-data parsing, model fitting, outcome scoring or BlackBox access.
Historical files are preserved by Git blob identity, including archived paths.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import posixpath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "5544fc093b8660b8eab4e7d0ceda2cbdb95f3b40"
ARCHIVE = "docs/archive/repository_consistency_20260912"
STATE = "docs/governance/REPOSITORY_STATE.json"
CATALOG = "docs/governance/COMPONENT_LIFECYCLE.json"
LATEST = "research/cross_index_residual_dislocation_utility_v1"
RECEPTION = "research/prospective_reception_recorder_v1"
D5 = "research/state_degree_consumer_d5"
DECISION = "CROSS_INDEX_RESIDUAL_DISLOCATION_INCREMENTAL_UTILITY_NOT_SUPPORTED"
PROGRAM = "HOLD_CURRENT_AUTHORITY"
WORKFLOWS = (".github/workflows/ci.yml", ".github/workflows/legacy-data-integrity.yml")
ENTRYPOINTS = ("README.md", "CURRENT_RESEARCH.md", "CONTINUE_HERE.md", "ai-readme.md", "LOCAL_TAKEOVER.md", "docs/INDEX.md", "AGENTS.md")
VALIDATORS = (
    "scripts/validate_data_usage_policy.py",
    "scripts/validate_research_backlog_closeout.py",
    "scripts/validate_degree_trajectory_utility_v1.py",
    "scripts/validate_historical_shock_burden_utility_v1.py",
    "scripts/validate_signed_risk_asymmetry_utility_v1.py",
    "scripts/validate_intrabar_temporal_reversal_utility_v1.py",
    "scripts/validate_cross_index_residual_dislocation_utility_v1.py",
)
FROZEN_DEPS = {
    "frozen_v19.py": "ee2fce299d5ee21abf1ab2c2c5183bac101ae822",
    "frozen_v9.py": "ae2a7e095df58692ef9df0dfee5856cac727ca44",
    "frozen_v18.py": "62c207badff1c3e37cbb1a8e17ef89feeea611d8",
    "frozen_v17.py": "397d80037806ba11cadf7f77717d36d55fbafc91",
    "frozen_v16_surface.json": "1f88966cf5dd3fb102f0d75746d5d00434555647",
}

def read_json(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))


def write(root: Path, name: str, text: str) -> None:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def dump(root: Path, name: str, value) -> None:
    write(root, name, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def tracked(root: Path) -> list[str]:
    return sorted(x.decode() for x in subprocess.check_output(["git", "ls-files", "-z"], cwd=root).split(b"\0") if x)


def tree(root: Path, ref: str) -> dict[str, str]:
    out = {}
    for row in subprocess.check_output(["git", "ls-tree", "-rz", ref], cwd=root).split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            out[path.decode()] = meta.decode().split()[2]
    return out


def scientific_sources(root: Path) -> list[dict]:
    out = []
    for p in sorted((root / "research").glob("*/PROGRAM_STATE.json")):
        s = json.loads(p.read_text())
        out.append({"path": p.relative_to(root).as_posix(), "snapshot_state": s.get("state", s.get("decision", s.get("status", s.get("current_stage", "see_original_snapshot")))), "git_blob": blob(p.read_bytes())})
    return out


def role(path: str) -> str:
    if path.startswith("docs/archive/"): return "archived_historical_no_execution_authority"
    if path.startswith("data/"): return "retained_input_identity_only_not_a_fit_permission"
    if path.startswith("artifacts/"): return "sealed_historical_artifact_not_current_promotion"
    if path.startswith("research/"):
        if path.startswith(tuple("research/" + x + "/" for x in ("causal_state_delivery_v1", "causal_state_delivery_d2", "state_degree_consumer_d5", "prospective_reception_recorder_v1"))):
            return "bounded_reference_and_frozen_acceptance_not_production"
        return "frozen_research_evidence_or_dependency_not_a_new_run"
    if path.startswith("docs/research/"): return "historical_research_or_closeout_snapshot"
    if path.startswith("docs/handoff/"): return "dated_handoff_snapshot_not_live_installation"
    if path.startswith("research_materials/"): return "reference_material_not_research_authority"
    if path.startswith("src/"): return "legacy_library_compatibility_not_trading_authority"
    if path.startswith("tests/"): return "synthetic_or_explicit_integration_regression"
    if path in VALIDATORS or path.startswith("docs/governance/"): return "governance_or_frozen_authority_check"
    if path.startswith("scripts/"): return "legacy_replay_or_export_tool_not_default_execution"
    return "retained_context_or_configuration"


def render_documents(root: Path, state: dict) -> dict[str, str]:
    latest = read_json(root, LATEST + "/PROGRAM_STATE.json")
    recv = read_json(root, RECEPTION + "/PROGRAM_STATE.json")
    d5 = read_json(root, D5 + "/PROGRAM_STATE.json")
    decl = read_json(root, "docs/governance/data_usage_declaration.json")
    status = (f"研究程序：**`{state['program_state']}`**。\n\n"
              f"最新科学决定：**`{latest['state']}`**。\n\n"
              f"接收工程：`{recv['state']}`。D5：`{d5['state']}`。\n\n"
              "`production_authority=false`; `research_hold=true`; `d6_started=false`; `v20_started=false`。\n")
    targets = (("状态与边界", STATE), ("当前白皮书", "docs/WHITEPAPER.md"), ("组件与生命周期", "docs/REPOSITORY_CATALOG.md"), ("整理记录", "docs/maintenance/REPOSITORY_CLEANUP_20260912.md"), ("最新正式结果", LATEST + "/RESULTS.md"), ("V2 数据政策", "docs/governance/DATA_USAGE_POLICY_V2.md"))
    def nav(path):
        folder = posixpath.dirname(path) or "."
        return " · ".join(f"[{label}]({posixpath.relpath(dest, folder)})" for label, dest in targets)
    note = "<!-- Generated by scripts/repository_consistency.py render; edit canonical state/sources, then regenerate. -->\n\n"
    docs = {}
    for path, title, intro in (
        ("README.md", "科创50 / 中证1000：因果 K 线风险属性模块", "本仓交付当时可知的风险状态、连续风险程度、时间和缺失语义。不是交易策略、方向信号、仓位管理或生产服务。"),
        ("CURRENT_RESEARCH.md", "当前研究：冻结结论，维护一致性", "HOLD 是当前研究程序的决定，不是宣称未来不存在新机制，也不是废除 V2 的 Validation 重复使用政策。本次整理不创建候选、不重开已关闭规格。"),
        ("CONTINUE_HERE.md", "接续入口", "从下方状态文件和白皮书接续。不要把历史目录中的 next_action 或旧 workflow_dispatch 当作现在的执行指令。维护任务可以继续，科学实验须另行明确协议。"),
        ("ai-readme.md", "AI 接续：当前状态与历史隔离", "先读 AGENTS.md 与机器状态。研究源码保留不代表该实验仍开放；原始结果和有限支持边界不得在清理中改写。"),
        ("LOCAL_TAKEOVER.md", "本地接续：工程边界", "D5 的仓内验收不等于外部消费者接收；接收适配器的云端验收不等于本地安装或采到真实逐条 received_at。不得以文件时间、批次时间、observation_time 伪造 received_at。"),
        ("docs/INDEX.md", "文档索引", "当前说明只从这里和白皮书进入。旧白皮书、旧报告及其原协议保留为历史证据，不与当前状态并列成为执行入口。"),
    ):
        docs[path] = note + f"# {title}\n\n{intro}\n\n" + status + "\n" + nav(path) + "\n\n## 检查\n\n```bash\npython scripts/repository_consistency.py check\npython scripts/repository_consistency.py tests --out /tmp/star50-contract-tests\n```\n\n"
    summary = "## 冻结研究链\n\n| 研究目录 | 原始快照状态（历史 next_action 不生效） |\n|---|---|\n"
    for source in state["scientific_sources"]:
        summary += f"| `{source['path'].split('/')[1]}` | `{source['snapshot_state']}` |\n"
    docs["CURRENT_RESEARCH.md"] += summary + "\nD4 仅支持指定 endpoint；D5 不新增 residual、signed-asymmetry 或 temporal-order 字段。旧 backlog 已关闭，程序没有自动授权的新实验。\n"
    protocol_path = root / ARCHIVE / "entrypoints/AGENTS.md"
    protocol_text = protocol_path.read_text(encoding="utf-8")
    marker = "## 云端—本地交接协议（默认不生效）"
    protocol = marker + protocol_text.split(marker, 1)[1]
    docs["AGENTS.md"] = note + "# STAR50 / CSI1000 repository instructions\n\n" + status + "\n" + nav("AGENTS.md") + "\n\nRead REPOSITORY_STATE.json and the current whitepaper first. Preserve original protocols, source bytes, evidence and scientific verdicts. Archived strategy skills are not active instructions. Do not run retired research workflows, new fitting, new validation scoring, BlackBox queries or market PnL for a maintenance task. Synthetic numerical regression is not a market backtest.\n\nV2 governs future data roles. Development is 2021–2023; reusable Validation is 2024-01-01 through 2026-08-21, not fresh OOS. The recent studies used the narrower 2024–2025 subset; the current D5 consumer is bounded to 2021–2025. These three boundaries must not be conflated. Post-2026-08-21 BlackBox detail stays closed. The directory name data/development is a legacy storage name, not fitting permission.\n\nGenerate entry points with `python scripts/repository_consistency.py render`; run `check` and the isolated `tests` command before publishing. Retain every test or record its explicit integration/dependency classification. Ordinary CI must not fetch mutable research branches or use write credentials.\n\n" + protocol
    docs["docs/WHITEPAPER.md"] = note + "# 因果 K 线风险属性模块：当前白皮书\n\n" + status + "\n" + nav("docs/WHITEPAPER.md") + "\n\n" + '''## 1. 使命、对象与可用范围

对象为 `000688.SH` 与 `000852.SH`。交付的是风险描述和适用性约束，不是收益承诺、买卖方向、仓位或订单。`src/star50_filter` 中早期策略/账户计算保留为历史兼容库，其存在与合成测试通过都不构成交易授权。

## 2. 模块链与信息时钟

| 层 | 实现 / 证据 | 当前含义 |
|---|---|---|
| V19 | `research/highvol_risk_episode_state_machine_v19/` 及 `_validation/` | 冻结的 NORMAL / UNSAFE / RECOVERING 状态机 |
| D1 / D2 | `research/causal_state_delivery_v1/adapter.py`、`research/causal_state_delivery_d2/engine.py` | 当时可知事件与双时钟、前缀一致性 |
| D3 | `research/causal_state_utility_d3/RESULTS.md` | 离散状态的实用预测增量未获支持 |
| D4 | `research/continuous_risk_utility_d4/RESULTS.md` | 连续 I/V 的有限 endpoint 支持 |
| D5 | `research/state_degree_consumer_d5/consumer.py` | 有界只读 research consumer，无外部接收或生产许可 |
| Reception | `research/prospective_reception_recorder_v1/` | recorder / adapter 工程通过，真实接收证据仍待取得 |

E15 是 5 分钟 K 线收盘前 15 秒；CLOSE 为完成后的确认事件。不得把当前完整收盘价注入 E15，不得回填或重写已经发布的事件。查询同时尊重 `decision_time`、`published_at`、`valid_until`；缺失/过期不是 NORMAL。`observation_time`、历史检索 `available_at` 与真实本机 `received_at` 不等价。当前历史证据不支持真实 feed latency 或 live 安装完成的说法。

D5 输出 schema 为 `state_degree_research_consumer_d5_v1`，D2 来源 schema 为 `causal_kline_delivery_d2_v1`。字段集合以 consumer.py 的 EVENT_FIELDS / ATTRIBUTE_FIELDS / EXTRA_FIELDS 为准；数值包含 intensity、volatility ratio 及其 lag/delta，并带可用性、来源与时钟语义。delta 和 numeric_bucket 只作描述/诊断，不获得独立预测或交易含义。冻结源码身份由 SOURCE_IDENTITY.json 与生命周期检查共同保护。

## 3. 证据边界

D4 的联合支持为 6 个 endpoint×horizon 中 4 个：future RMS 的 15/30/60 分钟，以及 future tail 的 30 分钟。15/60 分钟 tail 不得宣称支持；这是风险评分证据，不是交易收益。D3 与随后 M3、other-current degree、shock burden、one-step trajectory、signed asymmetry、intrabar ordering、cross-index residual 的固定规格不获得新的实用增量晋升。各阶段保留自己的原始报告与门槛，不拿最新状态回写历史统计。

最新 residual 规格的 B/R/Q 为 99/107/107 列，R/Q 等复杂度、同样本；12 项正式比较均未获支持。部分正向点估计与 30 分钟 RMS 的弱统计提示必须如实保留，但不能越过冻结的 1% 相对门、tail 0.0005 绝对门及稳健性门。最终结果以冻结 RESULTS.md / VALIDATION_RESULTS.json 为准。

## 4. 数据政策与当前实现不是一回事

''' + f"V2 Development：{decl['roles']['development']['date_start']} 至 {decl['roles']['development']['date_end']}。V2 reusable Validation：{decl['roles']['validation']['date_start']} 至 {decl['roles']['validation']['date_end']}。BlackBox-V1 为 2026-08-21 之后首 60 个完整交易日的固定快照，状态 `{decl['roles']['blackbox_v1']['status']}`。\n\n" + '''最近实验只评价 2024–2025；当前 D5 代码接收范围为 2021–2025。不得由 V2 允许未来研究复用 Validation，推断当前 D5 已验收 2026；也不得把最近实验未读 2026 改写成 V2 永久禁止所有 2026。旧 `data/development/` 文件实际上覆盖到 2026-08-21，目录名不授予训练权。维护检查不解析市场行；原始数据完整性复核是单独明确授权的手动集成任务。

## 5. 测试与运行方式

默认 CI 运行生命周期/入口一致性、7 项现存治理与冻结 authority 校验、根目录合成兼容测试，以及 25 个研究测试文件。研究测试逐文件独立进程执行，避免同名 run_study / run_validation / adapter 导入污染。V19 Validation 的 5 个临时依赖改为仓内精确 blob 固定副本，没有改状态机。

原始市场文件测试迁入 tests/integration，只有手动 legacy-data-integrity 工作流运行；根目录默认测试不读取历史市场行。依赖外部本地 FactorLab 的测试保留明确 skip，不能报告为外部系统验收通过。CI 的 JUnit / 退出码 / 环境版本作为实际执行记录。

## 6. 生命周期与保存

活动工作流只保留统一 CI 与有确认词的手动旧数据完整性检查。旧研究/导入/拟合工作流按原字节归档，不再挂在 Actions 自动入口。旧策略 skill 退出 .codex。重复历史文档合并到已存在的相同 blob 归档副本。其他原始研究源码、协议、结论、数据、产物保留身份；历史文档的 next_action、旧日期角色与旧路径不是当前指令。

全文件清单为 COMPONENT_LIFECYCLE.json；每个原始文件都有目标路径和原 blob。历史原文中的失效链接不伪装成有效链接，而在 HISTORICAL_LINKS.json 中列出 archive 重定位、现存候选路径或不可恢复状态；当前生成文档的所有 Markdown 文件链接必须有效。

## 7. 未完成的外部条件

真实 received_at 证据未取得；live recorder 未确认安装；external consumer 尚未接受；历史 feed latency 未验证。旧 v0.6.17 身份无法恢复的结论不变。文档清理、依赖补齐、绿色 CI 都不能自动消除这些条件，也不启动 D6/V20。

## 8. 变更规则

先改正式状态/协议或实现，再更新生命周期登记并运行 render、check、tests；不能只改一份入口。冻结研究字节有变必须作为新的、明确授权的规格或勘误处理，不得重写原证据。HOLD 下维护可以执行，但旧负结果不得通过换窗口、删控制组、选指数或放宽门槛自动救援。
'''
    docs["docs/REPOSITORY_CATALOG.md"] = note + "# 组件生命周期与执行目录\n\n" + status + "\n" + nav("docs/REPOSITORY_CATALOG.md") + "\n\n" + '''机器清单记录所有原始文件的 blob、当前位置与角色。保留文件不是批准执行；历史快照中的状态与下一步由当时协议解释，只有 REPOSITORY_STATE.json 代表当前程序。

| 组件 | 生命周期 / 执行方式 |
|---|---|
| 根入口、docs/INDEX、当前白皮书 | 从一个机器状态与冻结原始状态生成；CI 防止单文件漂移 |
| D1/D2/D5/recorder/adapter | bounded reference；运行合成契约测试，不宣称实盘 |
| 其他 research 与 docs/research | 冻结证据 / 历史依赖；LIFECYCLE.md 明示边界 |
| src/star50_filter | 旧库兼容回归；不是当前策略部署入口 |
| scripts 中 7 个登记校验器 | 当前 CI 只读校验；其他旧 run/fit/export/seal 脚本退役于默认执行 |
| data / artifacts | 身份不变的输入与历史产物；自动检查 Git 对象身份，不解析市场行 |
| research_materials | 参考文献；不是当前项目 authority |
| docs/handoff / ops | 日期化交接；实际安装、反馈、接收是否完成须看正式回执 |
| docs/archive | 历史原文 / 原工作流 / 原 agent skill；无运行授权 |

## 活动工作流

- `.github/workflows/ci.yml`：main / PR 的一致性与测试；只读权限、超时、并发取消。
- `.github/workflows/legacy-data-integrity.yml`：手动且必须明确确认；只做旧数据完整性，不拟合或评分，不查 BlackBox。

33 个旧工作流退出 Actions，ci.yml 更新前原文也保存，共 34 份工作流原文归档。临时整理工作流不进入最终主分支。

## 研究目录与原始状态

''' + summary + "\n## 自动检查命令\n\n```bash\npython -m pip install -e '.[maintenance]'\npython scripts/repository_consistency.py check\npython -m pytest -q -rs --junitxml=/tmp/star50-root.xml\npython scripts/repository_consistency.py tests --out /tmp/star50-contract-tests\n```\n\n所有结果以实际 CI 输出为准。手动集成测试与外部依赖 skip 不在自动通过范围内。\n"
    docs["docs/maintenance/REPOSITORY_CLEANUP_20260912.md"] = note + "# 仓库一致性整理记录 — 2026-09-12\n\n" + status + "\n" + nav("docs/maintenance/REPOSITORY_CLEANUP_20260912.md") + "\n\n" + f"基线：`{BASE}`，原始文件 5,187 个。清理不改变研究结论或生产权限。\n\n" + '''## 已处理的问题

README、CONTINUE_HERE、ai-readme、docs/INDEX 的最新状态落后于 CURRENT_RESEARCH；AGENTS 同时保留过期下一阶段指令；旧策略白皮书有 13 个字节相同的重复副本；34 个工作流未按当前 HOLD 整理；25 个研究测试文件未进入默认 tests/ 收集；V19 Validation 有两个测试依赖运行时下载文件；最近两轮完整证据只依赖有到期时间的 Actions artifact；旧 data/development 的命名容易误导数据池角色。

入口统一生成，新增当前白皮书、全文件生命周期与历史链接登记。归档 34 份原工作流，退役其中 33 个活动入口；旧 .codex 策略技能 4 个文件归档；13 个重复文档路径合并至原有同 blob 归档。原有根入口、配置和被整理的测试保存清理前原文。所有原始文件均由保留/迁移映射检查身份，没有把负结果或旧数据删除。

补齐 V19 Validation 五个精确冻结依赖；intrabar 与 residual 的完整 artifact 文件按校验清单持久化。既有证据文件如发现不一致立即失败，不覆盖。统一 CI 保留既有治理/authority 校验，补跑逐进程研究契约测试，并输出 JUnit、环境和退出码。

## 不夸大的验收边界

这是文件身份、代码/测试契约、入口语义和执行边界整理，不是把每项历史实验重新计算。原始数据只核对 Git 对象身份；旧行级完整性测试保留在手动 integration 流程。历史文档失效链接登记而不偷偷重写冻结原文。旧脚本若依赖原目录或旧下载，精确历史重放必须使用基线提交/归档原工作流，不能当作当前维护命令。

外部本地 FactorLab 依赖、真实接收证据、外部 D5 消费者接收仍是独立条件。最终通过数、skip 与 commit 以 PR/main CI 产物为准；本文不预写尚未完成的绿色结果。
'''
    return docs


def planned_paths(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts}


def initialize(root: Path, evidence_dir: Path) -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    if branch != "maintenance/repository-consistency-20260912" or (root / CATALOG).exists():
        raise RuntimeError("one-time initialization only on the reviewed maintenance branch")
    baseline = tree(root, BASE)
    if len(baseline) != 5187:
        raise RuntimeError(f"unexpected baseline file count {len(baseline)}")
    destinations = {}
    changed = (*ENTRYPOINTS, "pyproject.toml", "tests/test_package.py")
    for path in changed:
        dest = ARCHIVE + "/entrypoints/" + path
        data = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=root)
        (root / dest).parent.mkdir(parents=True, exist_ok=True)
        (root / dest).write_bytes(data)
        destinations[path] = dest
    for path in baseline:
        if path.startswith(".github/workflows/"):
            destinations[path] = ARCHIVE + "/workflows/" + path.rsplit("/", 1)[1]
        if path.startswith(".codex/"):
            destinations[path] = ARCHIVE + "/agent-skills/" + path[len(".codex/"):]
    duplicate_count = 0
    for path, sha in baseline.items():
        if path.startswith("docs/research/"):
            dest = path.replace("docs/research/", "docs/archive/mis_scoped_strategy_research_20260909/", 1)
            if baseline.get(dest) == sha:
                destinations[path] = dest
                (root / path).unlink()
                duplicate_count += 1
    if duplicate_count != 13:
        raise RuntimeError("duplicate inventory drift")
    evidence_receipts = []
    for folder, study in (("intrabar", "intrabar_temporal_reversal_utility_v1"), ("residual", "cross_index_residual_dislocation_utility_v1")):
        src = evidence_dir / folder
        dest = root / "research" / study / "evidence"
        manifest = src / "SHA256SUMS.txt"
        checked = []
        for line in manifest.read_text().splitlines():
            expected, filename = line.split(None, 1)
            filename = filename.strip().removeprefix("./")
            if Path(filename).name != filename:
                raise RuntimeError("artifact path must be a single filename")
            data = (src / filename).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError(f"artifact hash drift: {filename}")
            out = dest / filename
            if out.exists() and out.read_bytes() != data:
                raise RuntimeError(f"refuse to replace frozen evidence: {out}")
            out.write_bytes(data)
            checked.append({"file": filename, "sha256": expected})
        if (dest / "ARTIFACT_SHA256SUMS.txt").read_bytes() != manifest.read_bytes():
            raise RuntimeError("registered artifact manifest differs")
        evidence_receipts.append({"study": study, "files_verified": checked, "recomputed": False})
    p = root / "tests/test_package.py"
    original = p.read_text()
    start = original.index("def test_only_star50_and_roles():")
    stop = original.index("def test_lowpass_is_causal():")
    integration = original[start:stop]
    write(root, "tests/integration/test_legacy_market_integrity.py", "from pathlib import Path\nimport json\nimport pandas as pd\nROOT = Path(__file__).resolve().parents[2]\n\n" + integration)
    write(root, "tests/test_package.py", original[:start] + original[stop:])
    p = root / "pyproject.toml"
    text = p.read_text().replace('description = "Bounded FactorLab STAR50 causal filter timing research theme"', 'description = "Causal STAR50 / CSI1000 risk attributes and frozen research evidence; not a trading service"')
    text = text.replace('[tool.hatch.build.targets.wheel]', '[project.optional-dependencies]\nmaintenance = ["PyYAML>=6,<7"]\n\n[tool.hatch.build.targets.wheel]')
    text += '\naddopts = "--ignore=tests/integration"\n'
    write(root, "pyproject.toml", text)
    folders = sorted({path.rsplit("/", 1)[0] for path in baseline if path.startswith(("research/", "docs/research/")) and path.endswith(("/PROGRAM_STATE.json", "/PROTOCOL.md", "/whitepaper.md", "/preregistration.json"))})
    folders += ["research", "scripts", "src", "tests", "docs/handoff", "docs/ops", "docs/archive", "research_materials", "data", "artifacts", "docs/research/drawdown_conditions", "docs/research/execution_counterexamples"]
    for folder in sorted(set(folders)):
        rel = posixpath.relpath(STATE, folder)
        write(root, folder + "/LIFECYCLE.md", f"# 生命周期覆盖说明\n\n当前程序状态以 [REPOSITORY_STATE]({rel}) 为准。\n\n此目录的旧报告、原始代码、数据和 next_action 属于各自冻结协议/日期快照，不是启动新研究或生产执行的指令。原始字节保留；路径合并见全文件清单。未在当前 CI 登记的 run/fit/export/seal 工作流不自动执行。D1/D2/D5 与 recorder/adapter 只保留 bounded reference 含义。\n\n维护只校验身份和合成契约；重放历史实验使用精确历史提交及原工作流，须另行确定数据和研究授权。\n")
    sources = scientific_sources(root)
    state = {"schema": "star50_repository_state_v1", "as_of": "2026-09-12", "baseline_commit": BASE, "program_state": PROGRAM, "latest_scientific_state_path": LATEST + "/PROGRAM_STATE.json", "latest_scientific_decision": DECISION, "research_hold": True, "production_authority": False, "d6_started": False, "v20_started": False, "new_research_authorized": False, "blackbox_query_authorized": False, "raw_market_rows_read_by_maintenance": False, "d5_external_consumer_accepted": False, "true_reception_evidence_pending": True, "d5_supported_years": [2021, 2022, 2023, 2024, 2025], "latest_study_validation_years": [2024, 2025], "data_policy": "docs/governance/DATA_USAGE_POLICY_V2.md", "data_declaration": "docs/governance/data_usage_declaration.json", "scientific_sources": sources, "authority_validators": list(VALIDATORS), "active_workflows": list(WORKFLOWS), "active_workflow_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in WORKFLOWS}, "historical_executable_backlog": 0}
    dump(root, STATE, state)
    for path, text in render_documents(root, state).items(): write(root, path, text)
    suites = sorted(p.relative_to(root).as_posix() for p in root.glob("research/*/test*.py")) + sorted(p.relative_to(root).as_posix() for p in root.glob("docs/research/*/test*.py"))
    if len(suites) != 25: raise RuntimeError("unexpected frozen suite roster")
    dump(root, "docs/governance/TEST_REGISTRY.json", {"schema": "star50_test_registry_v1", "root_suites": sorted(p.relative_to(root).as_posix() for p in root.glob("tests/test*.py")), "research_suites": suites, "manual_integration": ["tests/integration/test_legacy_market_integrity.py"], "external_dependency_skip": "tests/test_three_proposals.py::test_exact_l3_prefix_and_scoped_module_restoration", "legacy_visual_tool": "tests/check_slope_union_v2_charts.cjs", "authority_validators": list(VALIDATORS)})
    dump(root, "docs/maintenance/EVIDENCE_PERSISTENCE.json", evidence_receipts)
    existing = set(baseline) | planned_paths(root)
    links = []
    for path in sorted(baseline):
        if not path.endswith(".md") or path.startswith(("data/", "artifacts/")): continue
        dest = destinations.get(path, path)
        p = root / dest
        if not p.is_file(): continue
        content = p.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", content):
            if re.match(r"[a-z]+:", target) or target.startswith("#"): continue
            target = target.split("#", 1)[0]
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if resolved in destinations:
                links.append({"source": dest, "original_source": path, "link": target, "status": "relocated", "replacement": destinations[resolved]})
            elif resolved not in existing and not any(x.startswith(resolved.rstrip('/') + '/') for x in existing):
                candidates = [x for x in baseline if x.endswith('/' + Path(resolved).name)]
                links.append({"source": dest, "original_source": path, "link": target, "status": "historical_unresolved_not_current_entry", "candidate_paths_not_asserted_equivalent": candidates[:8]})
    dump(root, "docs/maintenance/HISTORICAL_LINKS.json", links)
    preserved = [{"original": path, "path": destinations.get(path, path), "git_blob": sha, "role": role(destinations.get(path, path))} for path, sha in sorted(baseline.items())]
    allowed = (set(tracked(root)) | planned_paths(root) | set(WORKFLOWS) | {CATALOG})
    allowed -= {p for p in baseline if p in destinations and p not in changed and p != ".github/workflows/ci.yml"}
    allowed -= {".github/workflows/maintenance-bootstrap-once.yml", ".github/workflows/maintenance-inventory-once.yml"}
    allowed |= {r["path"] for r in preserved}
    catalog = {"schema": "star50_component_lifecycle_v1", "baseline_commit": BASE, "baseline_file_count": len(baseline), "preserved": preserved, "approved_tracked_paths": sorted(allowed), "disposition_counts": {"retired_research_workflow_entries": 33, "archived_original_workflows_including_ci": 34, "archived_strategy_skill_files": 4, "duplicate_document_paths_consolidated": duplicate_count}, "validation_scope": "Git blob identity for all baseline files; materialized non-market files also checked; no market row audit"}
    dump(root, CATALOG, catalog)
    print(json.dumps({"initialized": True, "baseline_files": len(baseline), "approved_paths": len(allowed), "research_suites": len(suites), "duplicate_paths_removed": duplicate_count, "outcomes_recomputed": False}))


def validate_semantics(root: Path, state: dict) -> list[str]:
    errors = []
    latest = read_json(root, state["latest_scientific_state_path"])
    recv = read_json(root, RECEPTION + "/PROGRAM_STATE.json")
    d5 = read_json(root, D5 + "/PROGRAM_STATE.json")
    if state["program_state"] != PROGRAM or state["latest_scientific_decision"] != latest["state"] or latest["state"] != DECISION: errors.append("current scientific/program state mismatch")
    for key in ("production_authority", "d6_started", "v20_started"):
        if any(x.get(key) is not False for x in (state, latest, recv, d5)): errors.append("authority escalation: " + key)
    for key in ("blackbox_query_authorized", "new_research_authorized", "raw_market_rows_read_by_maintenance", "d5_external_consumer_accepted"):
        if state.get(key) is not False: errors.append("unexpected authorization: " + key)
    if state.get("research_hold") is not True or latest.get("research_hold") is not True: errors.append("HOLD mismatch")
    if recv.get("true_reception_rows_collected") is not False or recv.get("live_recorder_installed") is not False or d5.get("external_consumer_accepted") is not False: errors.append("external evidence status changed without reconciliation")
    if state["scientific_sources"] != scientific_sources(root): errors.append("frozen scientific source roster/identity mismatch")
    return errors


def check(root: Path) -> None:
    import yaml
    state, catalog = read_json(root, STATE), read_json(root, CATALOG)
    errors = validate_semantics(root, state)
    names = set(tracked(root))
    if names != set(catalog["approved_tracked_paths"]): errors.append("tracked lifecycle coverage mismatch: " + repr({"unclassified": sorted(names - set(catalog["approved_tracked_paths"])), "missing": sorted(set(catalog["approved_tracked_paths"]) - names)}))
    identities = tree(root, "HEAD")
    for row in catalog["preserved"]:
        path, expected = row["path"], row["git_blob"]
        if identities.get(path) != expected: errors.append("preserved Git identity drift: " + path)
        p = root / path
        if not path.startswith(("data/", "artifacts/", "research_materials/")) and p.is_file() and blob(p.read_bytes()) != expected:
            errors.append("preserved worktree identity drift: " + path)
    if len(catalog["preserved"]) != 5187 or len({x["original"] for x in catalog["preserved"]}) != 5187: errors.append("incomplete baseline inventory")
    for path, text in render_documents(root, state).items():
        if (root / path).read_text(encoding="utf-8") != text: errors.append("generated entry drift: " + path)
        for link in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            if re.match(r"[a-z]+:", link) or link.startswith("#"): continue
            dest = posixpath.normpath(posixpath.join(posixpath.dirname(path), link.split("#", 1)[0]))
            if dest not in names and not any(x.startswith(dest.rstrip('/') + '/') for x in names): errors.append(f"broken current link: {path} -> {link}")
    workflows = sorted(p for p in names if p.startswith(".github/workflows/") and p.endswith((".yaml", ".yml")))
    if workflows != sorted(WORKFLOWS): errors.append("unexpected active workflow set")
    for path in workflows:
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != state["active_workflow_sha256"].get(path): errors.append("active workflow identity drift: " + path)
        w = yaml.load((root / path).read_text(), Loader=yaml.BaseLoader)
        if w.get("permissions") != {"contents": "read"}: errors.append("workflow permissions must be read-only: " + path)
        if not w.get("concurrency"): errors.append("workflow lacks concurrency: " + path)
        for job in w.get("jobs", {}).values():
            if job.get("permissions", {"contents": "read"}) != {"contents": "read"}: errors.append("job permission escalation: " + path)
            if not job.get("timeout-minutes"): errors.append("workflow lacks timeout: " + path)
        events = set(w.get("on", {}))
        allowed = {"push", "pull_request"} if path.endswith("/ci.yml") else {"workflow_dispatch"}
        if events != allowed: errors.append("unexpected workflow triggers: " + path)
        if "curl " in (root / path).read_text() or "contents: write" in (root / path).read_text(): errors.append("unexpected network/write execution in maintained workflow: " + path)
    for name, sha in FROZEN_DEPS.items():
        p = root / "research/highvol_risk_episode_state_machine_v19_validation" / name
        if blob(p.read_bytes()) != sha: errors.append("V19 frozen dependency drift: " + name)
    for receipt in read_json(root, "docs/maintenance/EVIDENCE_PERSISTENCE.json"):
        for f in receipt["files_verified"]:
            p = root / "research" / receipt["study"] / "evidence" / f["file"]
            if hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]: errors.append("persisted artifact drift: " + str(p))
    registry = read_json(root, "docs/governance/TEST_REGISTRY.json")
    actual = sorted(p.relative_to(root).as_posix() for p in root.glob("research/*/test*.py")) + sorted(p.relative_to(root).as_posix() for p in root.glob("docs/research/*/test*.py"))
    if actual != registry["research_suites"] or len(actual) != 25: errors.append("research test roster drift")
    if sorted(p.relative_to(root).as_posix() for p in root.glob("tests/test*.py")) != registry["root_suites"]: errors.append("root test roster drift")
    for path in names:
        p = root / path
        if p.suffix == ".py" and p.is_file() and not path.startswith("docs/archive/"):
            try: ast.parse(p.read_text(encoding="utf-8"), filename=path)
            except (SyntaxError, UnicodeError) as e: errors.append(str(e))
    if errors: raise RuntimeError("\n".join(errors))
    print(json.dumps({"repository_consistency": "PASS", "baseline_files_preserved": 5187, "tracked_components": len(names), "active_workflows": len(workflows), "research_test_files_registered": len(actual), "current_links_valid": True, "raw_market_rows_read": False, "historical_outcomes_recomputed": False}))


def run_tests(root: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    registry = read_json(root, "docs/governance/TEST_REGISTRY.json")
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONPATH=str(root / "src"))
    results = []
    for i, path in enumerate(registry["research_suites"]):
        report = out / f"suite-{i:02d}.xml"
        cmd = [sys.executable, "-m", "pytest", "-q", "-rs", "--junitxml=" + str(report), str(root / path)]
        try:
            r = subprocess.run(cmd, cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            output, code = r.stdout, r.returncode
        except subprocess.TimeoutExpired as e:
            output, code = str(e), 124
        (out / f"suite-{i:02d}.log").write_text(output)
        counts = {}
        if report.exists():
            suites = ET.parse(report).getroot().iter("testsuite")
            for suite in suites:
                for key in ("tests", "errors", "failures", "skipped"):
                    counts[key] = counts.get(key, 0) + int(suite.get(key, "0"))
        results.append({"path": path, "returncode": code, "junit": report.name, "counts": counts})
        print(path, code, counts, flush=True)
        dump(out, "RESULT.json", {"python": sys.version, "isolated_processes": True, "raw_market_rows_read": False, "results": results})
    if any(x["returncode"] for x in results): raise RuntimeError("contract suite failure; see RESULT.json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("initialize", "render", "check", "tests"))
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--evidence-dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("/tmp/star50-contract-tests"))
    a = ap.parse_args()
    root = a.repo_root.resolve()
    if a.command == "initialize":
        if a.evidence_dir is None: ap.error("initialize requires --evidence-dir")
        initialize(root, a.evidence_dir.resolve())
    elif a.command == "render":
        for name, content in render_documents(root, read_json(root, STATE)).items(): write(root, name, content)
    elif a.command == "check": check(root)
    else: run_tests(root, a.out.resolve())


if __name__ == "__main__":
    main()
