#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drp.py - deep-research-plus 工具链（单文件，零第三方硬依赖）。

子命令
  validate   校验技能包的 frontmatter / 悬空路径 / 文档版本 / 清单规则
  detect     探测依赖子技能，输出降级方案
  init       初始化调研工作区（outline.yaml / fields.yaml）
  gate       阶段闸门：outline / confirm / results / review / report
  report     从 outline + results + review 渲染 report.md
  bump       语义化版本递增，并同步 SKILL.md / 文档 / README / CHANGELOG
  package    校验 + 自动递增 + 构建 zip + SHA256 + release notes
  selfcheck  清单兜底：逐条规则复核 + 内置流水线回归
  version    输出当前版本

约定
  - PyYAML 存在时用它，缺失时回退内置 yamlmini（子集解析，测试保证等值）
  - 退出码：0 通过 / 1 存在违规 / 2 用法或环境错误
"""

from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
SOURCE_TYPES = ("official", "code", "secondary", "community", "journalism")
ITEM_KINDS = ("normal", "counter")
TIERS = ("light", "standard", "deep")
FIELD_TYPES = ("fact", "judgement")
TIER_MAX_ITEMS = {"light": 3, "standard": 8}
TIER_MIN_ITEMS = {"standard": 4, "deep": 9}

REQUIRED_REPORT_SECTIONS = (
    "核心结论",
    "对比总表",
    "逐项详析",
    "冲突与存疑",
    "未覆盖与限制",
    "来源清单",
)

# R2 反例黑名单：出现即返工（报告正文，不含技能自身的黑名单章节）
CLICHE_PATTERNS = (
    r"值得注意的是",
    r"总而言之",
    r"综上所述",
    r"众所周知",
    r"毋庸置疑",
    r"不难发现",
    r"在当今",
    r"随着[^。]{0,12}的不断发展",
    r"赋能",
    r"全方位",
    r"一站式",
    r"打造闭环",
)

URL_RE = re.compile(r"https?://[^\s<>()\"'，。；、]+")
BARE_DOMAIN_RE = re.compile(
    r"(?:来源|source)\s*[:：]\s*(?!https?://)[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.I
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_IN_TEXT_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


# --------------------------------------------------------------------------
# 输出与错误
# --------------------------------------------------------------------------
class DrpError(RuntimeError):
    """可预期的环境/用法错误（不打印 traceback）。"""


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def say(msg: str = "") -> None:
    print(msg)


def jprint(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False))


# --------------------------------------------------------------------------
# YAML：PyYAML 优先，内置子集解析兜底
# --------------------------------------------------------------------------
try:  # pragma: no cover - 环境相关
    import yaml as _pyyaml

    _HAS_PYYAML = True
except Exception:  # pragma: no cover
    _pyyaml = None
    _HAS_PYYAML = False


class YamlError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    out = []
    quote = None
    escaped = False
    for idx, ch in enumerate(line):
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (idx == 0 or line[idx - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_inline(text: str) -> list:
    parts, buf, depth, quote = [], [], 0, None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _scalar(token: str):
    s = token.strip()
    if s == "" or s in ("~", "null", "Null", "NULL"):
        return None
    if len(s) >= 2 and s[0] == s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if len(s) >= 2 and s[0] == s[-1] == '"':
        return s[1:-1].replace('\\"', '"')
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(x) for x in _split_inline(inner)] if inner else []
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out = {}
        for chunk in _split_inline(inner):
            k, _, v = chunk.partition(":")
            out[_scalar(k)] = _scalar(v)
        return out
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _yaml_lines(text: str):
    lines = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.lstrip(" ")
        if stripped.startswith("\t"):
            raise YamlError(f"line {lineno}: tab 缩进不被支持")
        body = _strip_comment(raw)
        if not body.strip():
            continue
        lines.append((len(body) - len(body.lstrip(" ")), body.strip(), lineno))
    return lines


def _parse_block_scalar(lines, idx, min_indent, style):
    buf = []
    while idx < len(lines) and lines[idx][0] >= min_indent:
        buf.append(lines[idx][1])
        idx += 1
    joiner = " " if style.startswith(">") else "\n"
    body = joiner.join(buf)
    if body and not style.endswith("-"):
        body += "\n"
    return body, idx


def _parse_seq(lines, idx, indent):
    out = []
    while idx < len(lines) and lines[idx][0] == indent and lines[idx][1].startswith("-"):
        content = lines[idx][1][1:].strip()
        if content == "":
            idx += 1
            if idx < len(lines) and lines[idx][0] > indent:
                value, idx = _parse_block(lines, idx, lines[idx][0])
            else:
                value = None
            out.append(value)
            continue
        if ":" in content and not content.startswith(("'", '"', "[", "{")):
            key, _, rest = content.partition(":")
            key = key.strip()
            rest = rest.strip()
            idx += 1
            entry = {}
            if rest in ("|", ">", "|-", ">-", "|+", ">+"):
                entry[key], idx = _parse_block_scalar(lines, idx, indent + 2, rest)
            elif rest == "":
                if idx < len(lines) and lines[idx][0] > indent:
                    entry[key], idx = _parse_block(lines, idx, lines[idx][0])
                else:
                    entry[key] = None
            else:
                entry[key] = _scalar(rest)
            while idx < len(lines) and lines[idx][0] > indent and not lines[idx][1].startswith("-"):
                more, idx = _parse_map(lines, idx, lines[idx][0])
                entry.update(more)
            out.append(entry)
            continue
        out.append(_scalar(content))
        idx += 1
    return out, idx


def _parse_map(lines, idx, indent):
    out = {}
    while idx < len(lines) and lines[idx][0] == indent and not lines[idx][1].startswith("-"):
        content = lines[idx][1]
        if ":" not in content:
            raise YamlError(f"line {lines[idx][2]}: 缺少 ':' 的映射行：{content!r}")
        key, _, rest = content.partition(":")
        key = key.strip()
        if key[:1] in ("'", '"'):
            key = _scalar(key)
        rest = rest.strip()
        idx += 1
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            out[key], idx = _parse_block_scalar(lines, idx, indent + 2, rest)
        elif rest == "":
            if idx < len(lines) and lines[idx][0] > indent:
                out[key], idx = _parse_block(lines, idx, lines[idx][0])
            else:
                out[key] = None
        else:
            out[key] = _scalar(rest)
    return out, idx


def _parse_block(lines, idx, indent):
    if lines[idx][1].startswith("-"):
        return _parse_seq(lines, idx, indent)
    return _parse_map(lines, idx, indent)


def loads(text: str):
    """内置 YAML 子集解析。"""
    lines = _yaml_lines(text)
    if not lines:
        return None
    value, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise YamlError(f"line {lines[idx][2]}: 缩进不一致，无法解析剩余内容")
    return value


def load_yaml_text(text: str):
    if _HAS_PYYAML:
        class _Loader(_pyyaml.SafeLoader):  # type: ignore[misc]
            pass

        _Loader.add_constructor(
            "tag:yaml.org,2002:timestamp",
            lambda loader, node: loader.construct_scalar(node),
        )
        return _pyyaml.load(text, Loader=_Loader)
    return loads(text)


def read_yaml(path: Path):
    if not path.exists():
        raise DrpError(f"文件不存在：{path}")
    try:
        return load_yaml_text(path.read_text(encoding="utf-8")) or {}
    except YamlError as exc:
        raise DrpError(f"YAML 解析失败 {path}: {exc}") from exc


FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)


def parse_frontmatter(text: str):
    match = FM_RE.match(text)
    if not match:
        return {}, text, 0
    try:
        meta = load_yaml_text(match.group(1)) or {}
    except YamlError as exc:
        raise DrpError(f"frontmatter 解析失败：{exc}") from exc
    if not isinstance(meta, dict):
        raise DrpError("frontmatter 不是映射结构")
    return meta, text[match.end():], text[: match.end()].count("\n")


# --------------------------------------------------------------------------
# 通用小工具
# --------------------------------------------------------------------------
def today_iso() -> str:
    return _dt.date.today().isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def slugify(topic: str, fallback: str = "research") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return cleaned[:48] or fallback


def bump_semver(version: str, level: str) -> str:
    match = SEMVER_RE.match(version)
    if not match:
        raise DrpError(f"当前版本不是语义化版本：{version!r}")
    major, minor, patch = (int(x) for x in match.groups())
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise DrpError(f"未知递增级别：{level}")


def compare_semver(left: str, right: str) -> int:
    lp = [int(x) for x in SEMVER_RE.match(left).groups()]  # type: ignore[union-attr]
    rp = [int(x) for x in SEMVER_RE.match(right).groups()]  # type: ignore[union-attr]
    return (lp > rp) - (lp < rp)


class Issue:
    __slots__ = ("code", "severity", "location", "message", "hint")

    def __init__(self, code: str, severity: str, location: str, message: str, hint: str = ""):
        self.code = code
        self.severity = severity
        self.location = location
        self.message = message
        self.hint = hint

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
            "hint": self.hint,
        }

    def render(self) -> str:
        tail = f" | hint: {self.hint}" if self.hint else ""
        return f"  [{self.severity}] {self.code} @ {self.location}: {self.message}{tail}"


def report_issues(title: str, issues: list, as_json: bool, extra: dict = None) -> int:
    errors = [i for i in issues if i.severity in ("P0", "P1")]
    warnings = [i for i in issues if i.severity == "P2"]
    if as_json:
        payload = {
            "check": title,
            "ok": not errors,
            "errors": len(errors),
            "warnings": len(warnings),
            "issues": [i.as_dict() for i in issues],
        }
        payload.update(extra or {})
        jprint(payload)
    else:
        status = "PASS" if not errors else "FAIL"
        say(f"[{status}] {title}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for issue in issues:
            say(issue.render())
    return 0 if not errors else 1


# --------------------------------------------------------------------------
# validate：技能包自检 + 清单规则引擎
# --------------------------------------------------------------------------
BACKTICK_PATH_RE = re.compile(r"`([^`\n]+)`")
PATH_TOKEN_RE = re.compile(r"^(?:[\w.\-]+/)*[\w.\-]+\.(?:md|py|yaml|yml|json|txt|sh)$")
DIR_TOKEN_RE = re.compile(r"^(?:[\w.\-]+/)+$")
BUNDLE_CLAIM_RE = re.compile(r"本仓库\s*`?([\w.\-]+/)`?\s*已(?:捆绑|内置)")


def _doc_files(skill_dir: Path) -> list:
    docs = list((skill_dir / "docs").glob("*.md")) if (skill_dir / "docs").is_dir() else []
    readme = skill_dir / "README.md"
    return ([readme] if readme.exists() else []) + sorted(docs)


def _iter_sections(body: str):
    """返回 [(heading_text, start_line, end_line)]，heading 为 `## xxx`。"""
    lines = body.splitlines()
    heads = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.startswith("## ")]
    out = []
    for pos, (idx, text) in enumerate(heads):
        end = heads[pos + 1][0] if pos + 1 < len(heads) else len(lines)
        out.append((text[3:].strip(), idx, end))
    return out, lines


def check_structure(skill_dir: Path, meta: dict, body: str) -> list:
    issues = []
    required = ("能力需求", "流水线", "反例黑名单", "使用示例")
    heads, _ = _iter_sections(body)
    titles = [h[0] for h in heads]
    for need in required:
        if not any(need in t for t in titles):
            issues.append(Issue("SEC-001", "P0", "SKILL.md", f"缺少必需章节：{need}"))
    for phase in ("Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4"):
        if phase not in body:
            issues.append(Issue("SEC-002", "P0", "SKILL.md", f"缺少流水线阶段：{phase}"))
    if "🛑" not in body:
        issues.append(Issue("SEC-003", "P1", "SKILL.md", "缺少硬停闸门标记（🛑）"))
    return issues


def check_frontmatter(skill_dir: Path, meta: dict) -> list:
    issues = []
    for key in ("name", "description", "version"):
        if not meta.get(key):
            issues.append(Issue("FM-002", "P0", "SKILL.md", f"frontmatter 缺少字段：{key}"))
    version = str(meta.get("version") or "")
    if version and not SEMVER_RE.match(version):
        issues.append(Issue("FM-003", "P0", "SKILL.md", f"version 非语义化：{version!r}"))
    if meta.get("name") and meta["name"] != skill_dir.name:
        issues.append(
            Issue(
                "FM-004",
                "P1",
                "SKILL.md",
                f"name={meta['name']!r} 与目录名 {skill_dir.name!r} 不一致",
                "安装后技能名以目录为准，二者应一致",
            )
        )
    desc = str(meta.get("description") or "")
    if desc and not re.search(r"(Triggers|触发)", desc):
        issues.append(Issue("FM-005", "P2", "SKILL.md", "description 缺少触发词声明（Triggers）"))
    return issues


FENCE_RE = re.compile(r"```.*?```", re.S)
PLACEHOLDER_RE = re.compile(r"(^|/)[A-Za-z]+_[A-Z](\.|/|$)|<[^>]*>|\{[^}]*\}")


def check_paths(skill_dir: Path, body: str) -> list:
    """只校验指向包内的相对路径。

    判定顺序：首段命中包内顶层条目才做存在性校验；首段与顶层条目高度相似判为笔误；
    其余视为调研产物路径（如 {slug}/report.md、results/）不参与包内校验。
    """
    issues = []
    prose = FENCE_RE.sub("", body)
    entries = {p.name for p in skill_dir.iterdir()}
    for match in BACKTICK_PATH_RE.finditer(prose):
        token = match.group(1).strip()
        if "/" not in token or "://" in token:
            continue
        if token.startswith(("~", "<", "{", ".")) or PLACEHOLDER_RE.search(token):
            continue
        first = token.split("/", 1)[0]
        if first in entries:
            if "*" in token:
                if not list(skill_dir.glob(token)):
                    issues.append(
                        Issue("PATH-001", "P0", "SKILL.md", f"通配路径未命中任何文件：{token}")
                    )
                continue
            if not (skill_dir / token).exists():
                issues.append(
                    Issue(
                        "PATH-001",
                        "P0",
                        "SKILL.md",
                        f"引用的相对路径不存在：{token}",
                        "删除该指针或在包内补上文件",
                    )
                )
            continue
        close = difflib.get_close_matches(first, sorted(entries), n=1, cutoff=0.8)
        if close:
            issues.append(
                Issue(
                    "PATH-004",
                    "P1",
                    "SKILL.md",
                    f"疑似笔误：{first}/ 不存在，最接近包内目录 {close[0]}/",
                )
            )
    for match in BUNDLE_CLAIM_RE.finditer(prose):
        token = match.group(1)
        if not (skill_dir / token).is_dir():
            issues.append(
                Issue(
                    "PATH-003",
                    "P0",
                    "SKILL.md",
                    f"声称本仓库已捆绑 {token}，但该目录不存在",
                    "改为指针+自动检测，或真正捆绑",
                )
            )
    return issues


def check_versions(skill_dir: Path, meta: dict) -> list:
    issues = []
    version = str(meta.get("version") or "")
    for doc in _doc_files(skill_dir):
        text = doc.read_text(encoding="utf-8")
        rel = doc.relative_to(skill_dir).as_posix()
        found = re.search(r"版本[：:]\s*(\d+\.\d+\.\d+)", text)
        if not found:
            issues.append(Issue("DOC-001", "P1", rel, "文档缺少 `版本：x.y.z` 头，无法自动同步"))
        elif version and found.group(1) != version:
            issues.append(
                Issue(
                    "DOC-002",
                    "P1",
                    rel,
                    f"文档版本 {found.group(1)} 与技能版本 {version} 不一致",
                    "运行 drp.py bump --level patch 或手工同步",
                )
            )
    return issues


def check_license(skill_dir: Path, meta: dict) -> list:
    issues = []
    declared = meta.get("license")
    if declared and not (skill_dir / "LICENSE").exists():
        issues.append(Issue("LIC-001", "P1", "LICENSE", f"声明 license={declared} 但缺少 LICENSE 文件"))
    return issues


def check_forbidden_patterns(body: str, params: dict, rule_id: str, severity: str) -> list:
    issues = []
    patterns = params.get("patterns") or []
    skip_sections = tuple(params.get("ignore_in_sections") or ())
    heads, lines = _iter_sections(body)
    skip_ranges = []
    for title, start, end in heads:
        if any(skip in title for skip in skip_sections):
            skip_ranges.append((start, end))

    def skipped(idx: int) -> bool:
        return any(start <= idx < end for start, end in skip_ranges)

    for pattern in patterns:
        for idx, line in enumerate(lines):
            if skipped(idx):
                continue
            if re.search(pattern, line):
                issues.append(
                    Issue(rule_id, severity, f"SKILL.md:{idx + 1}", f"命中禁用表述：{pattern}", line.strip()[:80])
                )
    return issues


def check_conflict_pairs(body: str, params: dict, rule_id: str, severity: str) -> list:
    issues = []
    for pair in params.get("pairs") or []:
        if len(pair) != 2:
            issues.append(Issue(rule_id, "P1", "checklists", f"conflict_pairs 条目应为 2 元素：{pair}"))
            continue
        first, second = pair
        if re.search(first, body) and re.search(second, body):
            issues.append(
                Issue(
                    rule_id,
                    severity,
                    "SKILL.md",
                    f"存在自相矛盾表述：/{first}/ 与 /{second}/",
                    "保留一条并补充分档限定",
                )
            )
    return issues


def check_claim_requires_dir(skill_dir: Path, body: str, params: dict, rule_id: str, severity: str) -> list:
    issues = []
    for claim in params.get("claims") or []:
        pattern = claim.get("pattern")
        target = claim.get("requires_dir")
        if not pattern or not target:
            issues.append(Issue(rule_id, "P1", "checklists", f"claim 配置不完整：{claim}"))
            continue
        if re.search(pattern, body) and not (skill_dir / target).is_dir():
            issues.append(
                Issue(rule_id, severity, "SKILL.md", f"声明依赖 {target}，但该目录不存在")
            )
    return issues


def check_manifest(skill_dir: Path, params: dict, rule_id: str, severity: str) -> list:
    issues = []
    manifest_path = skill_dir / "manifest.json"
    if not manifest_path.exists():
        return [Issue(rule_id, severity, "manifest.json", "缺少 manifest.json（打包与版本同步依赖它）")]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Issue(rule_id, "P0", "manifest.json", f"JSON 非法：{exc}")]
    for key in params.get("required_keys") or []:
        if key not in manifest:
            issues.append(Issue(rule_id, "P1", "manifest.json", f"缺少字段：{key}"))
    for entry in manifest.get("files") or []:
        if not (skill_dir / entry).exists():
            issues.append(Issue(rule_id, "P0", f"manifest.json", f"清单文件不存在：{entry}"))
    return issues


def check_gate_matrix(body: str, params: dict, rule_id: str, severity: str) -> list:
    """校验存在一张覆盖 light/standard/deep 的闸门矩阵表。"""
    issues = []
    for tier in TIERS:
        if not re.search(rf"\|[^\n]*{tier}[^\n]*\|", body):
            issues.append(Issue(rule_id, severity, "SKILL.md", f"闸门矩阵缺少档位行：{tier}"))
    return issues


def check_required_patterns(body: str, params: dict, rule_id: str, severity: str) -> list:
    issues = []
    for pattern in params.get("patterns") or []:
        if not re.search(pattern, body):
            issues.append(
                Issue(rule_id, severity, "SKILL.md", f"缺少必需内容：/{pattern}/", params.get("hint", ""))
            )
    return issues


RULE_HANDLERS = {
    "forbidden_patterns": lambda skill_dir, body, params, rid, sev: check_forbidden_patterns(body, params, rid, sev),
    "conflict_pairs": lambda skill_dir, body, params, rid, sev: check_conflict_pairs(body, params, rid, sev),
    "required_patterns": lambda skill_dir, body, params, rid, sev: check_required_patterns(body, params, rid, sev),
    "claim_requires_dir": check_claim_requires_dir,
    "manifest_files_exist": lambda skill_dir, body, params, rid, sev: check_manifest(skill_dir, params, rid, sev),
    "gate_matrix": lambda skill_dir, body, params, rid, sev: check_gate_matrix(body, params, rid, sev),
}


def load_checklist(skill_dir: Path, path_arg: str = "") -> dict:
    path = Path(path_arg) if path_arg else skill_dir / "checklists" / "skill_audit.yaml"
    if not path.exists():
        raise DrpError(f"清单文件不存在：{path}")
    data = read_yaml(path)
    if not isinstance(data, dict) or not data.get("rules"):
        raise DrpError(f"清单结构非法（需要 rules 列表）：{path}")
    return data


def run_checklist(skill_dir: Path, meta: dict, body: str, checklist: dict) -> list:
    issues = []
    for rule in checklist.get("rules") or []:
        rid = str(rule.get("id") or "CHK-???")
        rtype = str(rule.get("type") or "")
        severity = str(rule.get("severity") or "P1")
        params = rule.get("params") or {}
        handler = RULE_HANDLERS.get(rtype)
        if handler is None:
            issues.append(Issue("CHK-000", "P1", "checklists/skill_audit.yaml", f"未知规则类型：{rtype}（{rid}）"))
            continue
        issues.extend(handler(skill_dir, body, params, rid, severity))
    return issues


def cmd_validate(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    if not (skill_dir / "SKILL.md").exists():
        raise DrpError(f"未找到 SKILL.md：{skill_dir}")
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta, body, _ = parse_frontmatter(text)
    issues = []
    issues += check_frontmatter(skill_dir, meta)
    issues += check_structure(skill_dir, meta, body)
    issues += check_paths(skill_dir, body)
    issues += check_versions(skill_dir, meta)
    issues += check_license(skill_dir, meta)
    checklist = load_checklist(skill_dir, args.checklist)
    issues += run_checklist(skill_dir, meta, body, checklist)
    if args.strict:
        for issue in issues:
            if issue.severity == "P2":
                issue.severity = "P1"
    return report_issues(
        f"validate({skill_dir.name} v{meta.get('version', '?')})",
        issues,
        args.json,
        {"version": meta.get("version"), "rules": len(checklist.get("rules") or [])},
    )


# --------------------------------------------------------------------------
# detect：子技能探测 + 降级方案
# --------------------------------------------------------------------------
SUB_SKILLS = {
    "deep-research": "主干四阶段（outline → 确认 → 深调 → report）",
    "research": "引用纪律（一手来源优先）",
    "agent-reach": "社媒源路由（14 平台）",
    "market-researcher": "商业标注规范（来源+日期+假设暴露）",
}


def _candidate_roots(skill_dir: Path) -> list:
    home = Path.home()
    roots = [
        home / ".workbuddy" / "skills",
        home / ".claude" / "skills",
        home / ".codex" / "skills",
        home / ".config" / "opencode" / "skills",
        Path.cwd() / ".skills",
        Path.cwd() / "skills",
        skill_dir / "sub-skills",
        skill_dir.parent,
    ]
    seen, out = set(), []
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def detect_sub_skills(skill_dir: Path) -> dict:
    found = {}
    for name in SUB_SKILLS:
        hits = []
        for root in _candidate_roots(skill_dir):
            candidate = root / name
            if (candidate / "SKILL.md").exists():
                hits.append(str(candidate))
        if hits:
            found[name] = hits[0]
    degradation = []
    for name, role in SUB_SKILLS.items():
        if name not in found:
            degradation.append(f"缺失 {name} → {role} 降级")
    return {
        "skill_dir": str(skill_dir),
        "sub_skills": {name: {"role": SUB_SKILLS[name], "path": found.get(name)} for name in SUB_SKILLS},
        "degraded": degradation,
        "level": "zero-degradation" if not degradation else f"{len(degradation)}/4 degraded",
        "manual_capabilities": [
            "网络搜索（必需）",
            "网页抓取（可选，缺失则 summary-level）",
            "子代理并行（可选，缺失则串行）",
            "文件读写（可选，缺失则对话承载）",
        ],
    }


def cmd_detect(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    result = detect_sub_skills(skill_dir)
    if args.json:
        jprint(result)
    else:
        say(f"技能目录：{result['skill_dir']}")
        for name, info in result["sub_skills"].items():
            mark = "✓" if info["path"] else "·"
            say(f"  {mark} {name:<18} {info['role']}")
            if info["path"]:
                say(f"      -> {info['path']}")
        say(f"降级结论：{result['level']}")
        for item in result["degraded"]:
            say(f"  - {item}")
        say("需人工确认的平台能力：" + "、".join(result["manual_capabilities"]))
    return 0


# --------------------------------------------------------------------------
# init：工作区脚手架
# --------------------------------------------------------------------------
OUTLINE_TEMPLATE = """topic: {topic}
slug: {slug}
tier: standard
type: mixed
confirmed: false
confirmed_at: ""
confirmed_by: ""
items:
  - id: 1
    title: 候选一：定义与适用边界
    kind: normal
    fields: [source_of_truth]
    status: pending
  - id: 2
    title: 候选二：定义与适用边界
    kind: normal
    fields: [source_of_truth]
    status: pending
  - id: 3
    title: 横向对比：关键指标口径
    kind: normal
    fields: [source_of_truth]
    status: pending
  - id: 4
    title: 反方条目：已知缺陷与负面反馈
    kind: counter
    fields: [known_issue]
    status: pending
"""

FIELDS_TEMPLATE = """fields:
  - name: source_of_truth
    type: fact
    required: true
  - name: known_issue
    type: fact
    required: true
"""

RESULT_TEMPLATE = """item_id: {item_id}
title: {title}
status: pending
findings: []
uncertainties: []
"""

REVIEW_TEMPLATE = """rounds: 1
decisions: []
conflicts: []
uncovered: []
corrections: []
"""


def cmd_init(args) -> int:
    workspace = Path(args.workspace).resolve()
    if workspace.exists() and any(workspace.iterdir()) and not args.force:
        raise DrpError(f"目录非空，拒绝覆盖：{workspace}（如需覆盖加 --force）")
    slug = args.slug or slugify(args.topic)
    workspace.mkdir(parents=True, exist_ok=True)
    write_text(workspace / "outline.yaml", OUTLINE_TEMPLATE.format(topic=args.topic, slug=slug))
    write_text(workspace / "fields.yaml", FIELDS_TEMPLATE)
    (workspace / "results").mkdir(exist_ok=True)
    write_text(workspace / "review.yaml", REVIEW_TEMPLATE)
    if args.json:
        jprint({"workspace": str(workspace), "slug": slug, "files": ["outline.yaml", "fields.yaml", "review.yaml", "results/"]})
    else:
        say(f"已初始化：{workspace}")
        say("  下一步：编辑 outline.yaml 的 items（必须保留 1 个 kind: counter）→ gate --stage outline")
    return 0


# --------------------------------------------------------------------------
# gate：阶段闸门
# --------------------------------------------------------------------------
def _load_outline(workspace: Path, issues: list):
    path = workspace / "outline.yaml"
    if not path.exists():
        issues.append(Issue("G-OUT-001", "P0", str(path), "缺少 outline.yaml"))
        return {}
    data = read_yaml(path)
    if not isinstance(data, dict):
        issues.append(Issue("G-OUT-002", "P0", str(path), "outline.yaml 顶层应为映射"))
        return {}
    return data


def gate_outline(workspace: Path, strict: bool) -> list:
    issues = []
    data = _load_outline(workspace, issues)
    if not data:
        return issues
    for key in ("topic", "slug", "tier", "type", "items"):
        if key not in data:
            issues.append(Issue("G-OUT-003", "P0", "outline.yaml", f"缺少字段：{key}"))
    tier = str(data.get("tier") or "")
    if tier and tier not in TIERS:
        issues.append(Issue("G-OUT-004", "P0", "outline.yaml", f"tier 非法：{tier!r}（允许 {TIERS}）"))
    items = data.get("items") or []
    if not isinstance(items, list) or not items:
        issues.append(Issue("G-OUT-005", "P0", "outline.yaml", "items 为空"))
        return issues
    ids, titles = [], []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            issues.append(Issue("G-OUT-006", "P0", "outline.yaml", f"items[{idx}] 不是映射"))
            continue
        if not isinstance(item.get("id"), int):
            issues.append(Issue("G-OUT-007", "P0", "outline.yaml", f"items[{idx}].id 必须为整数"))
        else:
            ids.append(item["id"])
        title = str(item.get("title") or "").strip()
        if not title:
            issues.append(Issue("G-OUT-008", "P0", "outline.yaml", f"items[{idx}] 缺少 title"))
        titles.append(title)
        kind = item.get("kind", "normal")
        if kind not in ITEM_KINDS:
            issues.append(Issue("G-OUT-009", "P0", "outline.yaml", f"items[{idx}].kind 非法：{kind!r}"))
    if len(set(ids)) != len(ids):
        issues.append(Issue("G-OUT-010", "P0", "outline.yaml", "item id 重复"))
    dup_titles = {t for t in titles if t and titles.count(t) > 1}
    for title in sorted(dup_titles):
        issues.append(Issue("G-OUT-011", "P0", "outline.yaml", f"条目重叠（标题重复）：{title}", "条目需互斥"))
    counter = [i for i in items if isinstance(i, dict) and i.get("kind") == "counter"]
    if tier in ("standard", "deep") and not counter:
        issues.append(Issue("G-OUT-012", "P0", "outline.yaml", "缺少反方条目（kind: counter）", "R1：大纲必须含 1-2 个反方 item"))
    if tier == "light" and len(items) > TIER_MAX_ITEMS["light"]:
        issues.append(Issue("G-OUT-013", "P0", "outline.yaml", f"轻量档最多 3 个条目，当前 {len(items)}"))
    if tier == "standard" and not (TIER_MIN_ITEMS["standard"] <= len(items) <= TIER_MAX_ITEMS["standard"]):
        issues.append(Issue("G-OUT-014", "P1", "outline.yaml", f"标准档条目应在 4-8，当前 {len(items)}"))
    if tier == "deep" and len(items) < TIER_MIN_ITEMS["deep"]:
        issues.append(Issue("G-OUT-015", "P1", "outline.yaml", f"深度档条目应 ≥9，当前 {len(items)}"))
    fields_path = workspace / "fields.yaml"
    known_fields = set()
    if fields_path.exists():
        fields_data = read_yaml(fields_path)
        for entry in (fields_data.get("fields") or []):
            if isinstance(entry, dict) and entry.get("name"):
                known_fields.add(str(entry["name"]))
                if str(entry.get("type") or "fact") not in FIELD_TYPES:
                    issues.append(Issue("G-OUT-016", "P1", "fields.yaml", f"字段 {entry['name']} 的 type 非法"))
    else:
        issues.append(Issue("G-OUT-017", "P1", "fields.yaml", "缺少 fields.yaml"))
    for item in items:
        if not isinstance(item, dict):
            continue
        for field in item.get("fields") or []:
            if known_fields and str(field) not in known_fields:
                issues.append(
                    Issue("G-OUT-018", "P1", "outline.yaml", f"item {item.get('id')} 引用未定义字段：{field}")
                )
    return issues


def gate_confirm(workspace: Path, strict: bool) -> list:
    issues = []
    data = _load_outline(workspace, issues)
    if not data:
        return issues
    if data.get("confirmed") is not True:
        issues.append(Issue("G-CON-001", "P0", "outline.yaml", "confirmed 不为 true：Phase 2 闸门未通过", "用户明确确认后置 confirmed: true"))
    stamp = str(data.get("confirmed_at") or "")
    if not DATE_RE.match(stamp):
        issues.append(Issue("G-CON-002", "P0", "outline.yaml", "confirmed_at 必须是 YYYY-MM-DD"))
    elif stamp > today_iso():
        issues.append(Issue("G-CON-003", "P0", "outline.yaml", f"confirmed_at 晚于今天：{stamp}"))
    if not str(data.get("confirmed_by") or "").strip():
        issues.append(Issue("G-CON-004", "P1", "outline.yaml", "confirmed_by 为空，无法证明是用户确认"))
    items = data.get("items") or []
    if not any(isinstance(i, dict) and i.get("kind") == "counter" for i in items):
        issues.append(Issue("G-CON-005", "P0", "outline.yaml", "确认范围不含反方条目"))
    return issues


def _iter_results(workspace: Path):
    results_dir = workspace / "results"
    if not results_dir.is_dir():
        return []
    return sorted(results_dir.glob("item_*.yaml"))


def collect_findings(workspace: Path) -> dict:
    """返回 {finding_id: {...}}，附带文件来源。"""
    index = {}
    for path in _iter_results(workspace):
        try:
            data = read_yaml(path)
        except DrpError:
            continue
        for finding in (data.get("findings") or []):
            if isinstance(finding, dict) and finding.get("id"):
                item = dict(finding)
                item["_file"] = path.name
                index[str(finding["id"])] = item
    return index


def gate_results(workspace: Path, strict: bool) -> list:
    issues = []
    outline = _load_outline(workspace, issues)
    items = [i for i in (outline.get("items") or []) if isinstance(i, dict)]
    if not items:
        return issues
    files = {p.name: p for p in _iter_results(workspace)}
    seen_ids = set()
    for item in items:
        item_id = item.get("id")
        if not isinstance(item_id, int):
            continue
        path = files.get(f"item_{item_id}.yaml")
        if not path:
            if item.get("status") == "done":
                issues.append(Issue("G-RES-001", "P0", "results/", f"item {item_id} 标记完成但缺少 results/item_{item_id}.yaml"))
            else:
                issues.append(Issue("G-RES-002", "P1", "results/", f"item {item_id} 尚无结果文件"))
            continue
        data = read_yaml(path)
        rel = f"results/{path.name}"
        if data.get("item_id") != item_id:
            issues.append(Issue("G-RES-003", "P0", rel, f"item_id={data.get('item_id')!r} 与文件名不符"))
        if str(data.get("status") or "") not in ("pending", "done", "partial"):
            issues.append(Issue("G-RES-004", "P1", rel, f"status 非法：{data.get('status')!r}"))
        findings = data.get("findings") or []
        if not findings:
            issues.append(Issue("G-RES-005", "P1", rel, "findings 为空"))
        if item.get("kind") == "counter":
            negatives = [f for f in findings if isinstance(f, dict) and f.get("polarity") == "negative"]
            if not negatives and not (data.get("uncertainties") or []):
                issues.append(Issue("G-RES-006", "P1", rel, "反方条目缺少 negative 证据或 uncertainty 记录"))
        covered = set()
        for pos, finding in enumerate(findings, 1):
            if not isinstance(finding, dict):
                issues.append(Issue("G-RES-007", "P0", rel, f"findings[{pos}] 不是映射"))
                continue
            fid = str(finding.get("id") or "")
            if not fid:
                issues.append(Issue("G-RES-008", "P0", rel, f"findings[{pos}] 缺少 id"))
            elif fid in seen_ids:
                issues.append(Issue("G-RES-009", "P0", rel, f"finding id 重复：{fid}"))
            else:
                seen_ids.add(fid)
            claim = str(finding.get("claim") or "").strip()
            if len(claim) < 8:
                issues.append(Issue("G-RES-010", "P0", rel, f"{fid or pos} claim 过短或为空（<8 字符）"))
            url = str(finding.get("source_url") or "").strip()
            if not url:
                issues.append(Issue("G-RES-011", "P0", rel, f"{fid or pos} 缺少 source_url"))
            elif not url.startswith("https://"):
                issues.append(Issue("G-RES-012", "P0", rel, f"{fid or pos} source_url 必须是 https:// 完整链接：{url}", "R4：裸域名/http 不算引用"))
            date = str(finding.get("date") or "").strip()
            if not DATE_RE.match(date):
                issues.append(Issue("G-RES-013", "P0", rel, f"{fid or pos} date 必须是 YYYY-MM-DD"))
            elif date > today_iso():
                issues.append(Issue("G-RES-014", "P0", rel, f"{fid or pos} date 晚于今天：{date}"))
            stype = str(finding.get("source_type") or "").strip()
            if stype not in SOURCE_TYPES:
                issues.append(Issue("G-RES-015", "P0", rel, f"{fid or pos} source_type 非法：{stype!r}（允许 {SOURCE_TYPES}）"))
            if finding.get("field"):
                covered.add(str(finding["field"]))
        required_fields = [str(f) for f in (item.get("fields") or [])]
        missing = [f for f in required_fields if f not in covered]
        if required_fields and missing and findings:
            issues.append(Issue("G-RES-016", "P2", rel, f"字段未被 findings 覆盖：{', '.join(missing)}"))
    return issues


def gate_review(workspace: Path, strict: bool) -> list:
    issues = []
    path = workspace / "review.yaml"
    if not path.exists():
        issues.append(Issue("G-REV-001", "P0", "review.yaml", "缺少 review.yaml（Phase 3.5 未执行）"))
        return issues
    data = read_yaml(path)
    rounds = data.get("rounds")
    if not isinstance(rounds, int) or rounds < 1:
        issues.append(Issue("G-REV-002", "P0", "review.yaml", f"rounds 非法：{rounds!r}"))
    elif rounds > 2:
        issues.append(Issue("G-REV-003", "P0", "review.yaml", f"修订轮次 {rounds} 超过上限 2，应列入未覆盖", "R7：修订上限 ≤2 轮"))
    decisions = data.get("decisions") or []
    if not decisions:
        issues.append(Issue("G-REV-004", "P0", "review.yaml", "decisions 为空，报告没有决策级结论"))
    index = collect_findings(workspace)
    for pos, decision in enumerate(decisions, 1):
        if not isinstance(decision, dict):
            issues.append(Issue("G-REV-005", "P0", "review.yaml", f"decisions[{pos}] 不是映射"))
            continue
        cid = str(decision.get("id") or f"#{pos}")
        evidence = [str(e) for e in (decision.get("evidence") or [])]
        if not evidence:
            issues.append(Issue("G-REV-006", "P0", "review.yaml", f"{cid} 未绑定证据", "R5：无证据结论必须降级为存疑"))
        missing = [e for e in evidence if e not in index]
        if missing:
            issues.append(Issue("G-REV-007", "P0", "review.yaml", f"{cid} 引用了不存在的证据：{', '.join(missing)}"))
        urls = {index[e]["source_url"] for e in evidence if e in index}
        types = {index[e]["source_type"] for e in evidence if e in index}
        flags = {str(f) for f in (decision.get("flags") or [])}
        if decision.get("level", "decision") == "decision":
            if len(urls) == 1 and "single-source" not in flags:
                issues.append(Issue("G-REV-008", "P0", "review.yaml", f"{cid} 仅单源支撑但未标 single-source", "R6"))
            if types and types <= {"community", "secondary"} and "high-risk" not in flags:
                issues.append(Issue("G-REV-009", "P0", "review.yaml", f"{cid} 仅二手/社区源支撑但未标 high-risk", "R6"))
        claim = str(decision.get("claim") or "")
        if not claim.strip():
            issues.append(Issue("G-REV-010", "P0", "review.yaml", f"{cid} claim 为空"))
        for pattern in CLICHE_PATTERNS:
            if re.search(pattern, claim):
                issues.append(Issue("G-REV-011", "P1", "review.yaml", f"{cid} 命中 AI 腔：{pattern}", "R2"))
    if not data.get("corrections"):
        issues.append(Issue("G-REV-012", "P2", "review.yaml", "corrections 为空：未记录评审改了什么"))
    return issues


def gate_report(workspace: Path, strict: bool) -> list:
    issues = []
    path = workspace / "report.md"
    if not path.exists():
        return [Issue("G-REP-001", "P0", "report.md", "缺少 report.md")]
    text = path.read_text(encoding="utf-8")
    for section in REQUIRED_REPORT_SECTIONS:
        if not re.search(rf"^##\s*\d*\.?\s*{re.escape(section)}", text, re.M):
            issues.append(Issue("G-REP-002", "P0", "report.md", f"缺少必需章节：{section}"))
    head = text.splitlines()[:6]
    head_text = "\n".join(head)
    for token in ("调研日期", "分档", "能力组合", "评审"):
        if token not in head_text:
            issues.append(Issue("G-REP-003", "P1", "report.md", f"报告头缺少元信息：{token}"))
    used = set(re.findall(r"\[\^([\w-]+)\]", text))
    defined = dict(re.findall(r"^\[\^([\w-]+)\]:\s*(.+)$", text, re.M))
    for ref in sorted(used - set(defined)):
        issues.append(Issue("G-REP-004", "P0", "report.md", f"尾注 [^{ref}] 未定义"))
    for ref, body in defined.items():
        if not URL_RE.search(body):
            issues.append(Issue("G-REP-005", "P0", "report.md", f"尾注 [^{ref}] 缺少完整 https 链接", "R4"))
        if not DATE_IN_TEXT_RE.search(body):
            issues.append(Issue("G-REP-006", "P0", "report.md", f"尾注 [^{ref}] 缺少日期"))
    for match in BARE_DOMAIN_RE.finditer(text):
        issues.append(Issue("G-REP-007", "P0", "report.md", f"裸域名当引用：{match.group(0)}", "R4"))
    for pattern in CLICHE_PATTERNS:
        for line_no, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                issues.append(Issue("G-REP-008", "P1", f"report.md:{line_no}", f"命中 AI 腔：{pattern}", "R2"))
    review_path = workspace / "review.yaml"
    if review_path.exists():
        decisions = read_yaml(review_path).get("decisions") or []
        tldr = re.search(r"##\s*1\.?\s*核心结论.*?\n(.*?)(?=\n##\s)", text, re.S)
        if tldr and decisions:
            bullets = len(re.findall(r"^\s*[-*]\s+", tldr.group(1), re.M))
            if bullets < len(decisions):
                issues.append(Issue("G-REP-009", "P1", "report.md", f"TL;DR 条目 {bullets} 少于决策数 {len(decisions)}"))
    return issues


GATES = {
    "outline": gate_outline,
    "confirm": gate_confirm,
    "results": gate_results,
    "review": gate_review,
    "report": gate_report,
}


def cmd_gate(args) -> int:
    workspace = Path(args.workspace).resolve()
    stages = [args.stage] if args.stage != "all" else ["outline", "confirm", "results", "review", "report"]
    issues = []
    rc = 0
    for stage in stages:
        stage_issues = GATES[stage](workspace, args.strict)
        issues.extend(stage_issues)
        if not args.json:
            rc = max(rc, report_issues(f"gate:{stage}", stage_issues, False))
    if args.json:
        return report_issues(
            f"gate:{args.stage}", issues, True, {"workspace": str(workspace), "stages": stages}
        )
    return rc


# --------------------------------------------------------------------------
# report：渲染
# --------------------------------------------------------------------------
def render_report(workspace: Path) -> str:
    outline = read_yaml(workspace / "outline.yaml")
    review = read_yaml(workspace / "review.yaml") if (workspace / "review.yaml").exists() else {}
    index = collect_findings(workspace)
    topic = outline.get("topic") or outline.get("slug") or "调研"
    tier = outline.get("tier") or "standard"
    version = "unknown"
    skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
    if skill_md.exists():
        meta, _, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        version = str(meta.get("version") or version)

    # 尾注：按首次出现顺序给 URL 编号
    url_index = {}
    order = []

    def note(url: str, date: str, stype: str) -> str:
        key = url
        if key not in url_index:
            order.append((url, date, stype))
            url_index[key] = f"s{len(order)}"
        return f"[^{url_index[key]}]"

    decisions = [d for d in (review.get("decisions") or []) if isinstance(d, dict)]
    lines = []
    lines.append(f"# {topic} 深度调研报告")
    lines.append("")
    lines.append(
        f"> 调研日期：{today_iso()} ｜ 方法：deep-research-plus v{version}（分档：{tier}）"
        f" ｜ 能力组合：{review.get('capabilities') or '串行+抓取'} ｜ 评审：反方评审已过（{review.get('rounds', 1)} 轮）"
    )
    lines.append("")
    lines.append("## 1. 核心结论（TL;DR）")
    lines.append("")
    for decision in decisions:
        flags = "".join(f" `{f}`" for f in (decision.get("flags") or []))
        refs = []
        for eid in (decision.get("evidence") or []):
            finding = index.get(str(eid))
            if finding:
                refs.append(note(str(finding.get("source_url")), str(finding.get("date")), str(finding.get("source_type"))))
        lines.append(f"- {decision.get('claim', '').strip()}{flags} {' '.join(refs)}".rstrip())
    if not decisions:
        lines.append("- （review.yaml 尚未给出决策级结论）")
    lines.append("")
    lines.append("## 2. 对比总表")
    lines.append("")
    field_names = []
    for finding in index.values():
        if finding.get("field") and str(finding["field"]) not in field_names:
            field_names.append(str(finding["field"]))
    header = "| 条目 | " + " | ".join(field_names) + " |" if field_names else "| 条目 | 结论 |"
    lines.append(header)
    lines.append("|" + "---|" * (len(field_names) + 1) if field_names else "|---|---|")
    for item in [i for i in (outline.get("items") or []) if isinstance(i, dict)]:
        cells = []
        for field in field_names:
            value = "—"
            for finding in index.values():
                if finding.get("field") == field and finding.get("_file") == f"item_{item.get('id')}.yaml":
                    value = str(finding.get("value") or finding.get("claim") or "—").replace("|", "/")
                    break
            cells.append(value)
        if field_names:
            lines.append(f"| {item.get('title')} | " + " | ".join(cells) + " |")
        else:
            lines.append(f"| {item.get('title')} | 见逐项详析 |")
    lines.append("")
    lines.append("## 3. 逐项详析")
    lines.append("")
    for item in [i for i in (outline.get("items") or []) if isinstance(i, dict)]:
        result_path = workspace / "results" / f"item_{item.get('id')}.yaml"
        result = read_yaml(result_path) if result_path.exists() else {}
        lines.append(f"### {item.get('id')}. {item.get('title')}")
        lines.append("")
        findings = [f for f in (result.get("findings") or []) if isinstance(f, dict)]
        if not findings:
            lines.append("- 尚无证据（未覆盖）")
        for finding in findings:
            ref = note(str(finding.get("source_url")), str(finding.get("date")), str(finding.get("source_type")))
            lines.append(
                f"- {finding.get('claim')}：{finding.get('value', '')}"
                f"（`{finding.get('source_type')}`，{finding.get('date')}）{ref}"
            )
        for note_text in (result.get("uncertainties") or []):
            lines.append(f"- 不确定性：{note_text}")
        lines.append("")
    lines.append("## 4. 冲突与存疑")
    lines.append("")
    conflicts = review.get("conflicts") or []
    if not conflicts:
        lines.append("- 本轮未发现多源矛盾；无证据绑定的结论已降级移出 TL;DR。")
    for conflict in conflicts:
        lines.append(f"- {conflict}")
    lines.append("")
    lines.append("## 5. 未覆盖与限制")
    lines.append("")
    uncovered = review.get("uncovered") or []
    if not uncovered:
        lines.append("- 无（反方评审 2 轮内未发现未覆盖项）。")
    for entry in uncovered:
        lines.append(f"- {entry}")
    lines.append("")
    lines.append("## 6. 来源清单")
    lines.append("")
    for url, date, stype in order:
        key = url_index[url]
        lines.append(f"[^{key}]: <{url}> ｜ {date} ｜ `{stype}`")
    lines.append("")
    return "\n".join(lines)


def cmd_report(args) -> int:
    workspace = Path(args.workspace).resolve()
    if not (workspace / "outline.yaml").exists():
        raise DrpError(f"缺少 outline.yaml：{workspace}")
    content = render_report(workspace)
    out = Path(args.out) if args.out else workspace / "report.md"
    write_text(out, content)
    if args.json:
        jprint({"report": str(out), "bytes": len(content.encode("utf-8"))})
    else:
        say(f"已生成：{out}（{len(content.splitlines())} 行）")
        say("下一步：gate --stage report --workspace {}".format(workspace))
    return 0


# --------------------------------------------------------------------------
# 版本同步
# --------------------------------------------------------------------------
VERSION_SYNC_GLOBS = ("README.md", "docs/*.md")
VERSION_LINE_RE = re.compile(r"(版本[：:]\s*)(\d+\.\d+\.\d+)")
UPDATED_LINE_RE = re.compile(r"(更新[：:]\s*)(\d{4}-\d{2}-\d{2})")


def read_version(skill_dir: Path) -> str:
    meta, _, _ = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    version = str(meta.get("version") or "")
    if not SEMVER_RE.match(version):
        raise DrpError(f"SKILL.md version 非法：{version!r}")
    return version


def changelog_unreleased(skill_dir: Path) -> list:
    path = skill_dir / "CHANGELOG.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    match = re.search(r"##\s*\[Unreleased\](.*?)(?=\n##\s*\[|\Z)", text, re.S)
    if not match:
        return []
    entries = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            entries.append(stripped[2:].strip())
    return entries


def detect_bump_level(skill_dir: Path):
    entries = changelog_unreleased(skill_dir)
    if not entries:
        return None
    joined = " ".join(entries).lower()
    if "breaking" in joined or "不兼容" in joined:
        return "major"
    if any(word in joined for word in ("feat", "added", "新增", "增加", "支持")):
        return "minor"
    return "patch"


def apply_version(skill_dir: Path, new_version: str) -> list:
    changed = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    new_text = re.sub(r"(?m)^version:\s*\S+\s*$", f"version: {new_version}", text, count=1)
    if new_text != text:
        write_text(skill_md, new_text)
        changed.append("SKILL.md")

    manifest_path = skill_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["version"] = new_version
        manifest["updated_at"] = today_iso()
        write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        changed.append("manifest.json")

    for pattern in VERSION_SYNC_GLOBS:
        for doc in sorted(skill_dir.glob(pattern)):
            if not doc.is_file():
                continue
            raw = doc.read_text(encoding="utf-8")
            updated = VERSION_LINE_RE.sub(lambda m: m.group(1) + new_version, raw)
            updated = UPDATED_LINE_RE.sub(lambda m: m.group(1) + today_iso(), updated)
            if updated != raw:
                write_text(doc, updated)
                changed.append(doc.relative_to(skill_dir).as_posix())

    changelog = skill_dir / "CHANGELOG.md"
    if changelog.exists():
        raw = changelog.read_text(encoding="utf-8")
        entries = changelog_unreleased(skill_dir)
        body = "\n".join(f"- {entry}" for entry in entries) if entries else "- 维护性更新"
        block = f"## [{new_version}] - {today_iso()}\n\n{body}\n\n"
        if "## [Unreleased]" in raw:
            head, _, tail = raw.partition("## [Unreleased]")
            tail = tail.lstrip("\n")
            end = tail.find("\n## [")
            rest = tail[end + 1:] if end != -1 else ""
            raw = f"{head}## [Unreleased]\n\n{block}{rest}"
        else:
            marker = raw.find("\n## [")
            raw = raw[:marker] + "\n" + block + raw[marker:] if marker != -1 else raw + "\n" + block
        write_text(changelog, raw)
        changed.append("CHANGELOG.md")
    return changed


def cmd_bump(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    current = read_version(skill_dir)
    level = args.level
    if level == "auto":
        level = detect_bump_level(skill_dir)
        if level is None:
            if args.json:
                jprint({"version": current, "changed": False, "reason": "CHANGELOG [Unreleased] 为空"})
            else:
                say(f"无待发布变更，保持 {current}")
            return 0
    new_version = bump_semver(current, level)
    if args.dry_run:
        if args.json:
            jprint({"from": current, "to": new_version, "level": level, "dry_run": True})
        else:
            say(f"{current} -> {new_version}（{level}，dry-run）")
        return 0
    changed = apply_version(skill_dir, new_version)
    if args.json:
        jprint({"from": current, "to": new_version, "level": level, "changed_files": changed})
    else:
        say(f"{current} -> {new_version}（{level}）")
        for name in changed:
            say(f"  更新 {name}")
    return 0


# --------------------------------------------------------------------------
# package
# --------------------------------------------------------------------------
PACKAGE_INCLUDE = (
    "SKILL.md",
    "manifest.json",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "scripts",
    "checklists",
    "docs",
)
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "dist", "tests", ".github", ".workbuddy"}


def _package_files(skill_dir: Path) -> list:
    files = []
    for entry in PACKAGE_INCLUDE:
        path = skill_dir / entry
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in sorted(path.rglob("*")):
            if child.is_dir():
                continue
            if any(part in SKIP_DIRS for part in child.relative_to(skill_dir).parts):
                continue
            if child.suffix in (".pyc", ".pyo"):
                continue
            files.append(child)
    return sorted(files, key=lambda p: p.relative_to(skill_dir).as_posix())


def build_zip(skill_dir: Path, out_dir: Path, version: str) -> tuple:
    files = _package_files(skill_dir)
    missing = [name for name in ("SKILL.md", "manifest.json") if not (skill_dir / name).exists()]
    if missing:
        raise DrpError(f"打包缺少必需文件：{', '.join(missing)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"deep-research-plus-v{version}.zip"
    stamp = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(skill_dir).as_posix()
            info = zipfile.ZipInfo(rel, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
        manifest = {
            "name": skill_dir.name,
            "version": version,
            "built_at": today_iso(),
            "files": [
                {
                    "path": path.relative_to(skill_dir).as_posix(),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in files
            ],
        }
        info = zipfile.ZipInfo("BUILD-MANIFEST.json", date_time=stamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    digest = sha256_file(zip_path)
    (out_dir / "SHA256SUMS.txt").write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8", newline="\n")
    return zip_path, digest, len(files)


def write_release_notes(skill_dir: Path, out_dir: Path, version: str, zip_path: Path, digest: str) -> Path:
    text = (skill_dir / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"##\s*\[{re.escape(version)}\](.*?)(?=\n##\s*\[|\Z)", text, re.S)
    body = match.group(1).strip() if match else "- 维护性更新"
    notes = [
        f"# deep-research-plus v{version}",
        "",
        body,
        "",
        "## 产物",
        "",
        "| 文件 | 说明 |",
        "|------|------|",
        f"| `{zip_path.name}` | 技能包（解压到 skills/deep-research-plus 即用） |",
        "| `SHA256SUMS.txt` | 产物校验值 |",
        "| `docs/USER_MANUAL.md` | 用户手册 |",
        "| `docs/TECHNICAL_MANUAL.md` | 技术手册 |",
        "",
        f"SHA256：`{digest}`",
        "",
    ]
    path = out_dir / f"release-notes-v{version}.md"
    write_text(path, "\n".join(notes))
    return path


def _package_impl(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    out_dir = Path(args.out).resolve() if args.out else skill_dir / "dist"
    before = read_version(skill_dir)
    if args.no_bump:
        version = before
        level = "none"
        changed = []
    else:
        level = args.level
        if level == "auto":
            level = detect_bump_level(skill_dir)
            if level is None:
                level = "none"
        if level == "none":
            version = before
            changed = []
        else:
            version = bump_semver(before, level)
            changed = apply_version(skill_dir, version)

    # 打包前强制校验（P0/P1 阻断）
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta, body, _ = parse_frontmatter(text)
    issues = []
    issues += check_frontmatter(skill_dir, meta)
    issues += check_structure(skill_dir, meta, body)
    issues += check_paths(skill_dir, body)
    issues += check_versions(skill_dir, meta)
    issues += check_license(skill_dir, meta)
    issues += run_checklist(skill_dir, meta, body, load_checklist(skill_dir, ""))
    blocking = [i for i in issues if i.severity in ("P0", "P1")]
    if blocking and not args.force:
        if args.json:
            jprint({"ok": False, "stage": "validate", "issues": [i.as_dict() for i in blocking]})
        else:
            say("[FAIL] 打包前校验未通过，已中止：")
            for issue in blocking:
                say(issue.render())
        return 1

    zip_path, digest, count = build_zip(skill_dir, out_dir, version)
    notes = write_release_notes(skill_dir, out_dir, version, zip_path, digest)
    payload = {
        "ok": True,
        "from": before,
        "to": version,
        "level": level,
        "changed_files": changed,
        "zip": str(zip_path),
        "bytes": zip_path.stat().st_size,
        "sha256": digest,
        "files": count,
        "release_notes": str(notes),
        "warnings": [i.as_dict() for i in issues if i.severity == "P2"],
    }
    if args.json:
        jprint(payload)
    else:
        say(f"版本：{before} -> {version}（{level}）")
        say(f"产物：{zip_path}（{count} 个文件，{zip_path.stat().st_size} bytes）")
        say(f"SHA256：{digest}")
        say(f"说明：{notes}")
        for issue in issues:
            if issue.severity == "P2":
                say(issue.render())
    return 0


# --------------------------------------------------------------------------
# selfcheck：清单兜底 + 流水线回归
# --------------------------------------------------------------------------
def _fixture_pipeline(skill_dir: Path) -> list:
    """用 tests/fixtures/pass 跑通 init → gate → report。"""
    fixture = skill_dir / "tests" / "fixtures" / "pass"
    if not fixture.is_dir():
        return [("FIXTURE", "SKIP", "无 tests/fixtures/pass，跳过流水线回归")]
    results = []
    steps = [
        ("gate:outline", lambda: gate_outline(fixture, False)),
        ("gate:confirm", lambda: gate_confirm(fixture, False)),
        ("gate:results", lambda: gate_results(fixture, False)),
        ("gate:review", lambda: gate_review(fixture, False)),
    ]
    for name, fn in steps:
        issues = fn()
        bad = [i for i in issues if i.severity in ("P0", "P1")]
        status = "PASS" if not bad else "FAIL"
        detail = ", ".join(f"{i.code}" for i in bad[:3]) or "0 issue"
        results.append((name, status, detail))
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_ws = Path(tmp) / "ws"
        shutil.copytree(fixture, tmp_ws)
        content = render_report(tmp_ws)
        write_text(tmp_ws / "report.md", content)
        issues = gate_report(tmp_ws, False)
        bad = [i for i in issues if i.severity in ("P0", "P1")]
        results.append(("gate:report(rendered)", "PASS" if not bad else "FAIL", ", ".join(i.code for i in bad[:3]) or "0 issue"))
    return results


def cmd_selfcheck(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta, body, _ = parse_frontmatter(text)
    checklist = load_checklist(skill_dir, args.checklist)
    rows = []
    for rule in checklist.get("rules") or []:
        rid = str(rule.get("id"))
        handler = RULE_HANDLERS.get(str(rule.get("type")))
        if handler is None:
            rows.append((rid, "FAIL", "未知规则类型"))
            continue
        issues = handler(skill_dir, body, rule.get("params") or {}, rid, str(rule.get("severity") or "P1"))
        bad = [i for i in issues if i.severity in ("P0", "P1")]
        rows.append((rid, "PASS" if not bad else "FAIL", f"{len(bad)} 处命中" if bad else "0 命中"))
    base_issues = (
        check_frontmatter(skill_dir, meta)
        + check_structure(skill_dir, meta, body)
        + check_paths(skill_dir, body)
        + check_versions(skill_dir, meta)
        + check_license(skill_dir, meta)
    )
    invalid = [i for i in base_issues if i.severity in ("P0", "P1")]
    rows.insert(0, ("BASE", "PASS" if not invalid else "FAIL", ", ".join(i.code for i in invalid) or "0 issue"))
    if not args.no_pipeline:
        rows.extend(_fixture_pipeline(skill_dir))
    failed = [row for row in rows if row[1] == "FAIL"]
    if args.json:
        jprint({"ok": not failed, "version": meta.get("version"), "rows": [{"rule": r[0], "status": r[1], "detail": r[2]} for r in rows]})
    else:
        say(f"selfcheck v{meta.get('version')}（{len(rows)} 项，失败 {len(failed)}）")
        for rid, status, detail in rows:
            say(f"  {status:<4} {rid:<22} {detail}")
    return 0 if not failed else 1


def cmd_version(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    version = read_version(skill_dir)
    if args.json:
        jprint({"name": skill_dir.name, "version": version, "python": sys.version.split()[0], "pyyaml": _HAS_PYYAML})
    else:
        say(version)
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _default_skill_dir() -> str:
    return str(Path(__file__).resolve().parent.parent)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="drp", description="deep-research-plus 工具链")
    parser.add_argument("--skill-dir", default=_default_skill_dir(), help="技能根目录（默认脚本上一级）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    sub = parser.add_subparsers(dest="command", required=True)

    def _shared(p) -> None:
        """让 --json / --skill-dir 也能写在子命令后面（SUPPRESS 避免覆盖全局值）。"""
        p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        p.add_argument("--skill-dir", default=argparse.SUPPRESS)

    p_validate = sub.add_parser("validate", help="校验技能包")
    p_validate.add_argument("--strict", action="store_true", help="P2 也按失败处理")
    p_validate.add_argument("--checklist", default="", help="自定义清单路径")
    _shared(p_validate)
    p_validate.set_defaults(func=cmd_validate)

    p_detect = sub.add_parser("detect", help="探测依赖子技能")
    _shared(p_detect)
    p_detect.set_defaults(func=cmd_detect)

    p_init = sub.add_parser("init", help="初始化调研工作区")
    p_init.add_argument("--workspace", required=True)
    p_init.add_argument("--topic", required=True)
    p_init.add_argument("--slug", default="")
    p_init.add_argument("--force", action="store_true")
    _shared(p_init)
    p_init.set_defaults(func=cmd_init)

    p_gate = sub.add_parser("gate", help="阶段闸门")
    p_gate.add_argument("--workspace", required=True)
    p_gate.add_argument("--stage", default="all", choices=list(GATES) + ["all"])
    p_gate.add_argument("--strict", action="store_true")
    _shared(p_gate)
    p_gate.set_defaults(func=cmd_gate)

    p_report = sub.add_parser("report", help="渲染报告")
    p_report.add_argument("--workspace", required=True)
    p_report.add_argument("--out", default="")
    _shared(p_report)
    p_report.set_defaults(func=cmd_report)

    p_bump = sub.add_parser("bump", help="递增版本并同步文档")
    p_bump.add_argument("--level", default="auto", choices=["auto", "major", "minor", "patch"])
    p_bump.add_argument("--dry-run", action="store_true")
    _shared(p_bump)
    p_bump.set_defaults(func=cmd_bump)

    p_pkg = sub.add_parser("package", help="构建发布产物")
    p_pkg.add_argument("--out", default="")
    p_pkg.add_argument("--level", default="auto", choices=["auto", "major", "minor", "patch", "none"])
    p_pkg.add_argument("--no-bump", action="store_true")
    p_pkg.add_argument("--force", action="store_true", help="校验失败仍打包（仅调试用）")
    _shared(p_pkg)
    p_pkg.set_defaults(func=_package_impl)

    p_self = sub.add_parser("selfcheck", help="清单兜底校验")
    p_self.add_argument("--no-pipeline", action="store_true")
    p_self.add_argument("--checklist", default="")
    _shared(p_self)
    p_self.set_defaults(func=cmd_selfcheck)

    p_ver = sub.add_parser("version", help="输出版本")
    _shared(p_ver)
    p_ver.set_defaults(func=cmd_version)
    return parser


def main(argv=None) -> int:
    _utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except DrpError as exc:
        if args.json:
            jprint({"ok": False, "error": str(exc)})
        else:
            say(f"[ERROR] {exc}")
        return 2
    except BrokenPipeError:  # pragma: no cover
        return 2


if __name__ == "__main__":
    sys.exit(main())
