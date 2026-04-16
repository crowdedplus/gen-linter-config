"""
一个粗糙的生成lint配置的代码。
"""
import json
import os
import re
from gen_linter_config import GPTAgent


def generate_lint_config(rule: str, lint_name: str, model: str):
    """
    一键整合函数：输入自然语言规则、工具名和模型名，输出最终配置文件内容。
    """
    gpt_agent = GPTAgent()

    print("\n" + "=" * 60)
    print("步骤 1: 将自然语言规范转换为 DSL")
    print("=" * 60)
    prompt_dsl = nl_2_dsl(rule)
    dsl_result = gpt_agent.get_response(prompt_dsl, model=model)
    print("="*30+"LLM 返回 DSL 结果:\n", dsl_result)

    print("\n" + "=" * 60)
    print(f"步骤 2: 根据 DSL 从 {lint_name} 中检索相关的规则名列表")
    print("=" * 60)
    prompt_rule_list = dsl_2_rule_list(dsl_result, lint_name)

    # 如果该工具目录不存在，提前终止
    if prompt_rule_list == "暂时不支持该工具！":
        print("执行终止: 暂时不支持该工具！")
        return None

    rule_list_str = gpt_agent.get_response(prompt_rule_list, model=model)
    print("="*30+"LLM 返回规则名列表:\n", rule_list_str)

    print("\n" + "=" * 60)
    print("步骤 3: 获取详细 JSON 文档并生成最终配置")
    print("=" * 60)
    prompt_config = rule_list_2_config(rule_list_str, lint_name, rule)

    # 如果正则提取规则名失败，提前终止
    if prompt_config.startswith("error"):
        print("="*30+"执行终止 error :", prompt_config)
        return None

    llm_response = gpt_agent.get_response(prompt_config, model=model)
    print("="*30+"LLM 返回原始配置生成结果 (Part A & Part B):\n", llm_response)

    print("\n" + "=" * 60)
    print("步骤 4: 提取并清洗最终的配置文件")
    print("=" * 60)
    final_config = extract_config_from_llm(llm_response)

    if final_config:
        print("="*30+"提取成功，最终配置如下:\n")
        print(final_config)
        return final_config
    else:
        print("警告: 未能从大模型回答中通过正则提取到代码块。")
        print("降级处理: 返回大模型原始回答。")
        return llm_response

def nl_2_dsl(rule: str):
    prompt = """
    ### Notes for Coding Rules:
1. One sentence may contain **0, 1, or multiple rules**.  
2. Multiple sentencesOne rule may a rule.
3. **Edge case clarification**, such as constraint introduced by "even when", "except", or "unless",  must be extracted as **individual atomic rules**.
### Strictly Follow the Steps: 
1. Treat **edge case clarifications** as individual atomic coding rules.
2. Remove sentences that contain **no coding rules**.
3. If a sentence contains **multiple coding rules**, split it into separate atomic rules.
4. If multiple sentences together form a single coding rule, treat them as **one atomic rule**.
5. Complete and clarify each atomic rule so that it is explicit and self-contained.
6. Split the coding standard into atomic coding rules. 
7. Count the total number of atomic coding rules (0, 1, 2, 3, ...).
8. Parse all coding rules using given grammar by understanding its semantics. 
Note: **Edge case clarification**, such as constraint introduced by even when, except, or unless,  must be extracted as **individual atomic rules**.
### RuleSet Grammar is as follows:
```
RuleSet: 1. Rule₁ ; 
         2. Rule₂ ; 
            ... ; 
         n. Ruleₙ ;
Rule ::= [Must | Optional] /  RuleUnit | [Must | Optional] / If RuleUnit, RuleUnit
RuleUnit ::= RuleEntitySet₁ (if needed) / [Not (if needed)] **ConstraintOperator (Value if needed)** /  RuleEntitySetₙ;
RuleEntitySet ::= [ Entity₁, ... , Entityₖ ] 
Entity ::= PLTerm₁(Value if needed) (of/at/within/is/... PLTermₖ constrain PLTerm₁ if needed) 
Note: In the ObligationLevel position of each rule, you **must only use Must or Optional.**
```
### Example RuleSet is as follows::
Rule₁: Must / [PLTerm] / **ConstraintOperator** / [PLTerm];
Rule₂: Must / **Not ConstraintOperator** / [WildcardImport, StaticImport];
...
Ruleₙ: Optional / [PLTerm of/at/within/is/ PLTerm] / **Before** / [NonAssignmentOperator]

### Coding Rules are as Follows :
{{rules}}

### you should answer like this :

Rule1:Must / [PLTerm] / **ConstraintOperator** / [PLTerm];
Rule2:Must / **Not ConstraintOperator** / [WildcardImport, StaticImport];
...
rulen:Optional / [PLTerm of/at/within/is/ PLTerm] / **Before** / [NonAssignmentOperator]
"""
    prompt = prompt.replace("{{rules}}",rule)
    return prompt

def dsl_2_rule_list(dsl:str,lint_name:str):
    # 1. 处理路径逻辑：保持目录层级结构
    # 例如 "PMD/Java" -> 目录路径为 data/PMD/Java
    dir_parts = lint_name.split("/")
    dir_path = os.path.join(os.getcwd(),"others", "data", *dir_parts)

    # 2. 处理文件名逻辑：将 / 替换为 _
    # 例如 "PMD/Java" -> 文件名前缀为 PMD_Java
    filename_prefix = lint_name.replace("/", "_")
    target_filename_lower = f"{filename_prefix}Index.json".lower()

    # 基础检查：目录必须存在
    if not os.path.isdir(dir_path):
        print(f"目录不存在: {dir_path}")
        return "暂时不支持该工具！"

    index_data = None
    target_file_path = None

    try:
        # 3. 在目标目录中忽略大小写寻找匹配的文件
        files = os.listdir(dir_path)
        for file_name in files:
            if file_name.lower() == target_filename_lower:
                target_file_path = os.path.join(dir_path, file_name)
                break

        # 4. 读取文件
        if target_file_path and os.path.isfile(target_file_path):
            with open(target_file_path, 'r', encoding='utf-8') as f:
                print("="*30+"成功读取文件 : \n" + target_file_path)
                index_data = json.load(f)
        else:
            # 这里的打印信息包含了预期的文件名，方便调试
            print(f"未在 {dir_path} 中找到索引文件: {filename_prefix}Index.json")

    except Exception as e:
        print(f"读取索引文件时出错: {e}")
        return None
    # 此时index_data中含有指定工具的所有Index内容。
    prompt = """
The Configuration file is organized as follows :
{
 rule_name1:{
 description:"...",
 url:"..."
 },
 ...,
 rule_namen:{
 description:"...",
 url:"..."
 }
}
    For each coding rule:
- Refer to the Configuration file .
- Identify and select the corresponding {{lint_name}} rule names.

Here is the Configuration file :
{{index_data}}
Here is the coding rule :
{{dsl}}

    Finally you should answer all rule names you select ,form is like this :
    {
    rule_name1,...,rule_namen
    }
    """
    index_data_str = json.dumps(index_data, ensure_ascii=False, indent=2)
    prompt = prompt.replace("{{index_data}}",index_data_str)
    prompt = prompt.replace("{{lint_name}}",lint_name)
    prompt = prompt.replace("{{dsl}}",dsl)
    return prompt


def rule_list_2_config(rule_list_str: str, lint_name: str, original_rule: str):
    # --- 1. 解析规则名 ---
    selected_names = []
    try:
        # 如果是大模型返回的标准 JSON 格式
        data = json.loads(rule_list_str)
        if isinstance(data, dict):
            # 兼容 {"rules": {"a":1}} 或 {"a":1}
            target = data.get("rules", data)
            selected_names = list(target.keys())
    except:
        # 如果是字符串形式 {rule1, rule2}
        match = re.search(r'\{(.*?)\}', rule_list_str, re.DOTALL)
        if match:
            raw_content = match.group(1)
            # 提取单词，过滤掉引号
            selected_names = re.findall(r'[a-zA-Z0-9\-_/]+', raw_content)

    # 清洗：去重、去空、转小写比对前保留原始格式用于显示
    selected_names = list(
        set([n.strip() for n in selected_names if n.strip() and n.lower() not in ["rules", "severity"]]))

    # --- 2. 确定工具类型与格式指导 ---
    name_up = lint_name.upper()

    # 默认配置
    fmt = "JSON"
    boilerplate = "Include standard environment and parser options."
    syntax = '"rule-name": ["error", { "option": value }]'

    if "PMD" in name_up or "CHECKSTYLE" in name_up:
        fmt = "XML"
        boilerplate = "Include XML declaration and root wrapper (<ruleset> for PMD, <module name='Checker'> for Checkstyle)."
        syntax = '<property name="option_name" value="value" />'
    elif any(x in name_up for x in ["RUBOCOP", "REEK", "CLANGTIDY"]):
        fmt = "YAML"
        boilerplate = "Standard YAML hierarchy."
        syntax = "RuleName:\n  OptionName: value"
    elif any(x in name_up for x in ["PYLINT", "FLAKE8"]):
        fmt = "INI/RC"
        boilerplate = "Use [MASTER] or [flake8] section headers."
        syntax = "option_name = value"
    elif "RUFF" in name_up:
        fmt = "TOML/JSON"
        boilerplate = "Standard Ruff configuration (pyproject.toml or ruff.toml)."
        syntax = "rule_name = { option = value }"
    elif "BIOME" in name_up:
        fmt = "JSON/JSONC"
        boilerplate = "Biome configuration structure (biome.json)."
        syntax = '"ruleName": { "options": { "key": "value" } }'
    elif "CPPCHECK" in name_up:
        fmt = "CPPCHECK"
        # TODO : cppcheck其实没有广义上的配置文件，其使用方法类似：cppcheck --enable=warning,performance file.cpp
    else :
        print("="*10+"调用大模型生成pmt"+"="*10)
        # 调用prompt

    # --- 3. 读取详细 JSON 信息 ---
    dir_parts = lint_name.split("/")
    rules_base_dir = os.path.join(os.getcwd(),"others", "data", *dir_parts, "rules")
    rules_detailed_context = []

    for rule_name in selected_names:
        target_json_lower = f"{rule_name}.json".lower()
        if os.path.isdir(rules_base_dir):
            for file_name in os.listdir(rules_base_dir):
                if file_name.lower() == target_json_lower:
                    try:
                        with open(os.path.join(rules_base_dir, file_name), 'r', encoding='utf-8') as f:
                            inner = list(json.load(f).values())[0]  # 获取内部第一个对象
                            rules_detailed_context.append(
                                f"### RULE: {rule_name}\n[DESC]: {inner.get('description')}\n[OPTS]: {inner.get('option')}"
                            )
                            print("成功读取详细配置文件 : ",os.path.join(rules_base_dir, file_name))
                    except:
                        pass
                    break

    all_rules_info = "\n\n".join(rules_detailed_context) if rules_detailed_context else "NO DATA FOUND."
    print("="*30+"所有rules内容 : \n",all_rules_info)
    # --- 4. 构建最终 Prompt ---
    final_prompt = f"""
        You are a senior DevOps expert specialized in **{lint_name}**.

        ### 1. USER REQUIREMENT (THE TARGET)
        The user wants to enforce the following rules:
        "{original_rule}" 

        ### 2. CONTEXT: Technical Specifications (THE TOOL RULES)
        Use the following specifications to find valid property names:
        {all_rules_info}

        ---

        ### 3. TASK OBJECTIVES
        - Map the **USER REQUIREMENT** to **{lint_name}** configuration.
        - **Format**: {fmt}
        - **MANDATORY**: You MUST read the [OPTS] documentation. 
        - If the USER REQUIREMENT specifies a value (like "100 characters"), BIND that value to the correct property. DO NOT use the default values from the documentation if the user has specified a custom one.

        ---

        ### 4. RESPONSE FORMAT (Mandatory)
        #### Part A: Configuration Analysis
        #### Part B: Final Configuration File
        Provide the COMPLETE, valid configuration file for **{lint_name}** in a single code block.
        """
    return final_prompt

def extract_config_from_llm(llm_response):
    # 提取 Markdown 代码块中的内容
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', llm_response, re.DOTALL)
    if code_blocks:
        return code_blocks[-1] # 通常返回最后一个代码块（Part B）
    return None

# if __name__ == "__main__":
#     ## 使用示例
#     # nl_rule = "变量必须使用驼峰命名法，并且行宽不能超过 100 个字符。"
#     # lint_tool = "ESLint"
#     # model_name = "dashscope/qwen3-max"
#     #
#     # # 一键调用生成配置并打印全部过程
#     # final_config = generate_lint_config(nl_rule, lint_tool, model_name)