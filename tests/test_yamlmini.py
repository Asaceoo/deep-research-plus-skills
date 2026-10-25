"""YAML 层：内置子集解析必须与 PyYAML 结果一致。"""

import pytest

CASES = {
    "nested_map": "a:\n  b: 1\n  c: text\n",
    "seq_scalar": "- 1\n- two\n- true\n",
    "seq_of_maps": "items:\n  - id: 1\n    title: 甲\n  - id: 2\n    title: 乙\n",
    "inline_list": "fields: [license, perf]\n",
    "inline_map": "meta: {owner: asaceoo, level: 2}\n",
    "quotes": "a: \"x: y\"\nb: '单引号 # 不是注释'\n",
    "comment": "a: 1  # 行尾注释\n# 整行注释\nb: 2\n",
    "empty_value": "a:\nb: 2\n",
    "nulls": "a: null\nb: ~\n",
    "numbers": "i: 42\nf: 3.5\nneg: -7\n",
    "date_string": "date: 2026-10-01\n",
    "block_scalar": "desc: |\n  一行说明\n",
    "list_of_inline": "a:\n  - [1, 2]\n  - [3]\n",
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_mini_matches_pyyaml(drp_module, name):
    if not drp_module._HAS_PYYAML:
        pytest.skip("未安装 PyYAML，跳过等值比对")
    text = CASES[name]
    assert drp_module.loads(text) == drp_module.load_yaml_text(text)


def test_dates_stay_strings(drp_module):
    if not drp_module._HAS_PYYAML:
        pytest.skip("未安装 PyYAML")
    parsed = drp_module.load_yaml_text("d: 2026-10-01\n")
    assert parsed["d"] == "2026-10-01"
    assert isinstance(parsed["d"], str)


def test_tab_indent_rejected(drp_module):
    with pytest.raises(drp_module.YamlError):
        drp_module.loads("a:\n\tb: 1\n")


def test_unexpected_indent_rejected(drp_module):
    with pytest.raises(drp_module.YamlError):
        drp_module.loads("a: 1\n  b: 2\n")


def test_empty_document(drp_module):
    assert drp_module.loads("\n# nothing\n") is None
