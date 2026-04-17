import json
import pytest

from gen_linter_config.ESLint.gen_eslint_config import gen_eslint


ESLINT_CASES = [
    "asychronous_program",
    "code_quality",
    "coding_form",
    "react_develop",
]


@pytest.mark.parametrize("case", ESLINT_CASES)
def test_eslint_generation(case, load_fixture, default_model):
    input_text = load_fixture("eslint", case, "input")
    expected_output = load_fixture("eslint", case, "expected")

    generator = gen_eslint()
    dsl_output = generator.process_input(
        input_content=input_text,
        model=default_model,
        output_format="text",
        examples=""
    )

    try:
        actual_output = json.loads(dsl_output)
    except json.JSONDecodeError:
        actual_output = dsl_output

    assert actual_output == expected_output, f"Case '{case}' output mismatch"