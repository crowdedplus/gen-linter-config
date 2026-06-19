"""Lightweight prompt for ESLint — uses JSON instead of DSL grammar.
Contains Step 3 and Step 4 prompt functions adapted for JSON mode (no Mandatory/Optional
type matching on tool-side options)."""

# Re-export shared utility functions from the original module
from .Config_set_ESLint_for_googleJS import (
    extract_config_promt,
    extract_non_empty_config_promt,
    extract_merge_mappings_promt,
    extract_correct_mapping,
    gen_config_format,
    extract_specific_config_promt,
)


# ── Step 3: Detailed Option Mapping (JSON mode) ──────────────────────────

def step3_preprocess_promt(style="RuleSet of Google JavaScript Style Guide", DSLruleset=None,
                           tool="ESLint", toolruleset=None, example=""):
    prompt = '''Extract each rule from the following {{Style}} where starting with "Mandatory" or "Optional".
Identify if each rule in RuleSet of {{Style}} has semantically equivalent rules from the {{tool}} JSON rules below.

1. From the {{tool}} JSON rules below, find rules whose "desc" or "name" matches the semantics of {{Style}}. The "desc" field describes what the rule enforces.
2. From each matched rule's options list, find options whose "name" and "type" match what {{Style}} requires using the option "description". Use the "default" value if {{Style}} does not specify a different value.
3. Extract all key terms enclosed in "[]" from the rule of {{Style}}.
4. Determine whether options exist that correspond to the extracted terms.
5. If the option "type" is a regular expression, set the option value as a regular expression string. Otherwise, set a specific value from {{Style}}.
6. Give the corresponding RuleName for each match and list all matched options.
7. Ensure that specified option values are supported by the valid range for the corresponding option.

Note: Do not miss any in {{Style}}. For each rule, individually provide detailed analysis for each step!

*********************

{{Style}}:
{{DSLruleset}}

*********************

{{tool}} rules in JSON format. Each rule has "name", "desc", "description", and "options" keys. Each option has "name", "type", "default", "description".

{{toolruleset}}

{{Example}}

*********************

Response Format:
Note first give analysis of each step for each rule of {{Style}}!!! and then give the answer!!!
###Analysis:###
...
###Mappings:###
Note before ">>>" is rule of {{Style}}, after ">>>" is the corresponding rule from {{tool}}
Format:
1. excerpt first rule from {{Style}}  ">>>" corresponding RuleName and options from {{tool}}
   RuleName: <Give corresponding RuleName from {{tool}}>
   option 1: optionName; optionValue;
   ...

For example:
1. Optional: [ReturnStatement] is not [Expression]
   >>>
   RuleName: consistent-return
   option 1: treatUndefinedAsUnspecified; false;

Otherwise, give None.
'''
    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{DSLruleset}}", DSLruleset)
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("```plaintext", "")
    prompt = prompt.replace("```", "")
    prompt = prompt.replace("{{toolruleset}}", toolruleset)

    return prompt


# ── Step 4.1: Merge Option Rules (JSON mode) ─────────────────────────────

def merge_basic_option_rules_lightweight(answer_map):
    prompt = '''For the following ToolSEM rules,

For each ToolSEM rule consisting of the **Basic Rule** and the **Option Rules**, let's break down and combine setting option values of each ToolSEM rule to derive only one new ToolSEM rule begin with "Mandatory:" or "Optional:" using given grammar.

**Note: For the rule type of new ToolSEM rule, use the SAME rule type ("Mandatory" or "Optional") as the corresponding StyleSEM rule (the label before ">>>" in the original mapping). Do not infer the type from the ToolSEM rules.**

Ensure new ToolSEM rule is clearer and aligns more accurately with rule details of old ToolSEM rule! Avoid ambiguous wording.

new ToolSEM rule should not be impacted by StyleSEM!!!

{{answer_map}}

Response Format:
**Mappings:**
1. old ToolSEM rule
   >>>
   New ToolSEM rule starting with "Mandatory" or "Optional"

2. ...'''
    prompt = prompt.replace("{{answer_map}}", answer_map)
    return prompt


# ── Step 4.3: Semantic Validation (JSON mode, no type comparison) ────

def validation_config_superset_semantics_lightweight(mapping: str, style="RuleSet of Google JavaScript Style Guide",
                                                     DSL_Syntax="", tool="ESLint",
                                                     toolruleset=None, grammar="Grammar", example=""):
    prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:

For each mapping, do the following steps:

Step 1: Compare Semantics:
 - If their semantics are identical, the mapping result is Yes.
 - Or if the semantics of one rule are a subset of or superset within the semantics of the other, the mapping result is Yes.
 - Otherwise, If the semantics are not identical and no subset of or superset relationship exists, the mapping result is No.

Note for Comparison:
1. When comparing, consider the definitions of JavaTerms and account for synonym relationships where applicable.


{{Mapping}}


Response Format:
Analysis: ...
Mapping 1: Yes or No

Analysis: ...
Mapping 2: Yes or No
'''

    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{style}}", style)
    prompt = prompt.replace("{{Mapping}}", mapping)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt
