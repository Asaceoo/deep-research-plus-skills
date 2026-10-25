"""五个闸门的通过与失败路径，逐条断言错误码。"""


def codes(issues):
    return {i.code for i in issues}


def patch(path, old, new, count=-1):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture 中找不到待替换内容：{old!r}"
    path.write_text(text.replace(old, new, count), encoding="utf-8")


# ---------------------------------------------------------------- outline
def test_outline_pass(drp_module, pass_ws):
    issues = drp_module.gate_outline(pass_ws, False)
    assert not [i for i in issues if i.severity in ("P0", "P1")], [i.render() for i in issues]


def test_outline_without_counter_item(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "kind: counter", "kind: normal")
    assert "G-OUT-012" in codes(drp_module.gate_outline(pass_ws, False))


def test_outline_duplicate_title(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "三方 benchmark 横向对比", "Weaviate 性能口径")
    assert "G-OUT-011" in codes(drp_module.gate_outline(pass_ws, False))


def test_outline_light_tier_too_many_items(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "tier: standard", "tier: light")
    assert "G-OUT-013" in codes(drp_module.gate_outline(pass_ws, False))


def test_outline_deep_tier_needs_nine_items(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "tier: standard", "tier: deep")
    assert "G-OUT-015" in codes(drp_module.gate_outline(pass_ws, False))


def test_outline_undefined_field(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "fields: [ecosystem]", "fields: [ghost_field]")
    assert "G-OUT-018" in codes(drp_module.gate_outline(pass_ws, False))


def test_outline_missing_file(drp_module, tmp_path):
    assert "G-OUT-001" in codes(drp_module.gate_outline(tmp_path, False))


# ---------------------------------------------------------------- confirm
def test_confirm_pass(drp_module, pass_ws):
    assert drp_module.gate_confirm(pass_ws, False) == []


def test_confirm_not_confirmed(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "confirmed: true", "confirmed: false")
    assert "G-CON-001" in codes(drp_module.gate_confirm(pass_ws, False))


def test_confirm_future_date(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", 'confirmed_at: "2026-10-20"', 'confirmed_at: "2099-01-01"')
    assert "G-CON-003" in codes(drp_module.gate_confirm(pass_ws, False))


def test_confirm_without_operator(drp_module, pass_ws):
    patch(pass_ws / "outline.yaml", "confirmed_by: user", 'confirmed_by: ""')
    assert "G-CON-004" in codes(drp_module.gate_confirm(pass_ws, False))


# ---------------------------------------------------------------- results
def test_results_pass(drp_module, pass_ws):
    issues = drp_module.gate_results(pass_ws, False)
    assert not [i for i in issues if i.severity in ("P0", "P1")], [i.render() for i in issues]


def test_results_http_url(drp_module, pass_ws):
    patch(pass_ws / "results" / "item_1.yaml", "https://milvus.io", "http://milvus.io")
    assert "G-RES-012" in codes(drp_module.gate_results(pass_ws, False))


def test_results_bare_domain(drp_module, pass_ws):
    patch(pass_ws / "results" / "item_1.yaml", "https://milvus.io/docs/overview.md", "milvus.io")
    assert "G-RES-012" in codes(drp_module.gate_results(pass_ws, False))


def test_results_missing_date(drp_module, pass_ws):
    patch(pass_ws / "results" / "item_1.yaml", "    date: 2026-09-18\n", "")
    assert "G-RES-013" in codes(drp_module.gate_results(pass_ws, False))


def test_results_bad_source_type(drp_module, pass_ws):
    patch(pass_ws / "results" / "item_1.yaml", "source_type: official", "source_type: blog")
    assert "G-RES-015" in codes(drp_module.gate_results(pass_ws, False))


def test_results_short_claim(drp_module, pass_ws):
    patch(
        pass_ws / "results" / "item_1.yaml",
        "claim: Milvus 采用 Apache-2.0 许可证，允许闭源商用",
        "claim: 短",
    )
    assert "G-RES-010" in codes(drp_module.gate_results(pass_ws, False))


def test_results_duplicate_finding_id(drp_module, pass_ws):
    patch(pass_ws / "results" / "item_2.yaml", "id: f2", "id: f1")
    assert "G-RES-009" in codes(drp_module.gate_results(pass_ws, False))


def test_results_missing_file_for_done_item(drp_module, pass_ws):
    (pass_ws / "results" / "item_5.yaml").unlink()
    assert "G-RES-001" in codes(drp_module.gate_results(pass_ws, False))


def test_results_counter_without_negative_evidence(drp_module, pass_ws):
    path = pass_ws / "results" / "item_4.yaml"
    patch(path, "polarity: negative", "polarity: positive")
    text = path.read_text(encoding="utf-8")
    text = text.replace("uncertainties:\n  - 社区样本量有限，不能代表全部用户\n", "")
    path.write_text(text, encoding="utf-8")
    assert "G-RES-006" in codes(drp_module.gate_results(pass_ws, False))


# ---------------------------------------------------------------- review
def test_review_pass(drp_module, pass_ws):
    issues = drp_module.gate_review(pass_ws, False)
    assert not [i for i in issues if i.severity in ("P0", "P1")], [i.render() for i in issues]


def test_review_rounds_over_limit(drp_module, pass_ws):
    patch(pass_ws / "review.yaml", "rounds: 1", "rounds: 3")
    assert "G-REV-003" in codes(drp_module.gate_review(pass_ws, False))


def test_review_evidence_not_found(drp_module, pass_ws):
    patch(pass_ws / "review.yaml", "evidence: [f1, f2]", "evidence: [f1, f99]")
    assert "G-REV-007" in codes(drp_module.gate_review(pass_ws, False))


def test_review_single_source_unflagged(drp_module, pass_ws):
    patch(pass_ws / "review.yaml", "evidence: [f1, f2]", "evidence: [f1]")
    assert "G-REV-008" in codes(drp_module.gate_review(pass_ws, False))


def test_review_community_only_decision(drp_module, pass_ws):
    patch(
        pass_ws / "review.yaml",
        "  - id: d2\n    claim: Qdrant 的运维复杂度是社区反馈最集中的短板\n    level: supporting\n    evidence: [f5]\n    flags: [single-source, high-risk]\n",
        "  - id: d2\n    claim: Qdrant 运维复杂度是最大短板\n    level: decision\n    evidence: [f5]\n    flags: []\n",
    )
    assert "G-REV-009" in codes(drp_module.gate_review(pass_ws, False))


def test_review_cliche_claim(drp_module, pass_ws):
    patch(
        pass_ws / "review.yaml",
        "claim: 三个候选均为宽松许可证，闭源商用无障碍",
        "claim: 综上所述，三个候选均为宽松许可证",
    )
    assert "G-REV-011" in codes(drp_module.gate_review(pass_ws, False))


def test_review_missing_file(drp_module, pass_ws):
    (pass_ws / "review.yaml").unlink()
    assert "G-REV-001" in codes(drp_module.gate_review(pass_ws, False))


# ---------------------------------------------------------------- report
def rendered(drp_module, pass_ws):
    content = drp_module.render_report(pass_ws)
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    return content


def test_report_rendered_passes(drp_module, pass_ws):
    rendered(drp_module, pass_ws)
    issues = drp_module.gate_report(pass_ws, False)
    assert not [i for i in issues if i.severity in ("P0", "P1")], [i.render() for i in issues]


def test_report_has_six_sections_and_footnotes(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    for section in drp_module.REQUIRED_REPORT_SECTIONS:
        assert section in content
    assert "[^s1]:" in content
    assert "https://" in content


def test_report_missing_section(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    content = content.replace("## 5. 未覆盖与限制", "## 五、其他")
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    assert "G-REP-002" in codes(drp_module.gate_report(pass_ws, False))


def test_report_undefined_footnote(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    content = content.replace("## 2. 对比总表", "追加引用 [^s99]\n\n## 2. 对比总表")
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    assert "G-REP-004" in codes(drp_module.gate_report(pass_ws, False))


def test_report_bare_domain(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    content = content.replace("## 4. 冲突与存疑", "## 4. 冲突与存疑\n\n来源：arxiv.org")
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    assert "G-REP-007" in codes(drp_module.gate_report(pass_ws, False))


def test_report_cliche(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    content = content.replace("## 2. 对比总表", "值得注意的是，这里还要补充一点。\n\n## 2. 对比总表")
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    assert "G-REP-008" in codes(drp_module.gate_report(pass_ws, False))


def test_report_missing_meta(drp_module, pass_ws):
    content = rendered(drp_module, pass_ws)
    content = "\n".join(line for line in content.splitlines() if not line.startswith("> 调研日期"))
    (pass_ws / "report.md").write_text(content, encoding="utf-8")
    assert "G-REP-003" in codes(drp_module.gate_report(pass_ws, False))
