import json
import pytest

from gen_linter_config.checkstyle.gen_checkstyle_config import gen_checkstyle


CHECKSTYLE_CASES = [
    "coding_format",
    "complexity_control",
    "comprehensive_quality",
    "exception_handling",
    "OO",
]


@pytest.mark.parametrize("case", CHECKSTYLE_CASES)
def test_checkstyle_generation(case, load_fixture, default_model):
    # 1. 加载输入文本
    input_text = load_fixture("checkstyle", case, "input")

    # 2. 实例化生成器并调用入口方法
    generator = gen_checkstyle()
    # 假设 process_input 返回的是字符串（DSL 结果），你可能需要将其解析为 dict
    dsl_output = generator.process_input(
        input_content=input_text,
        model=default_model,
        output_format="text",
        examples=""
    )

    # 3. 如果 process_input 返回的是 JSON 字符串，需解析
    #    （若返回已经是 dict 则直接使用）
    try:
        actual_output = json.loads(dsl_output)
    except json.JSONDecodeError:
        # 如果不是 JSON，可能是纯文本，可根据需要调整比较方式
        actual_output = dsl_output

    # 4. 加载期望输出
    expected_output = load_fixture("checkstyle", case, "expected")

    # 5. 断言
    assert actual_output == expected_output, f"Case '{case}' output mismatch"