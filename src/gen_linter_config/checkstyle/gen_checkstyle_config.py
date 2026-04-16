"""
该文件需要实现的功能：
读取指令的所有参数之后返回checkstyle配置。
"""
import os
import re
import json

from gen_linter_config import util_java,GPTAgent
from .DSL_gpt_google_java_style import preprocess_promt as nl_preprocess, \
    Extract_DSL_Repr as DSL_final_extract
from .Config_name_select_checkstyle_for_googlejava_one import preprocess_promt as rule_mapper_preprocess, \
    extract_basic_rule
from . import Config_set_checkstyle_for_googlejava_ours_o1 as CheckstyleGenerator
current_dir = os.path.dirname(os.path.abspath(__file__))

class gen_checkstyle:
    def __init__(self):
        self.dsl_syntax = util_java.dsl
        self.gpt_agent = GPTAgent() if GPTAgent else None

    # 处理代码规范的总入口
    def process_input(self,  input_content, model, output_format="text", examples=""):
        print("=" * 60)
        print("步骤1: NL代码规范转换为DSL")
        print("=" * 60)
        dsl_result = self.process_nl_rule(input_content, model, output_format, examples)
        print(dsl_result)

        print("\n" + "=" * 60)
        print("步骤2: DSL规则映射到Checkstyle规则")
        print("=" * 60)
        mapping_result = self.map_to_checkstyle(dsl_result,model, output_format=output_format, examples=examples)
        print(mapping_result)

        # --- 步骤3：详细选项映射 (子配置项生成) ---
        print("\n" + "=" * 60)
        print("步骤3: 详细子配置项映射 (Sub-options Mapping)")
        print("=" * 60)
        detailed_mapping = self.detailed_mapping(dsl_result, mapping_result, model, examples)
        print(detailed_mapping)

        # ---  步骤4：配置生成 ---
        print("\n" + "=" * 60)
        print("步骤4: 生成 Checkstyle 配置")
        print("=" * 60)
        config_result = self.generate_config(detailed_mapping, model, output_format=output_format, examples=examples)
        final_res = self.generate_full_checkstyle_xml(config_result)
        print(final_res)
        return final_res

    # 第一步，自然语言转DSL
    def process_nl_rule(self, rule_description, model, output_format="text", examples=""):
        """
        处理自然语言代码风格转换为DSL
        """
        prompt = nl_preprocess(
            rule=rule_description,
            DSL_Syntax=self.dsl_syntax,
            example=examples
        )

        # 第一次转为带思考过程的DSL，后一次提取DSL。
        if self.gpt_agent:
            gpt_response = self.gpt_agent.get_response(prompt, model=model)
            final_ruleset = DSL_final_extract(gpt_response)
            final_response = self.gpt_agent.get_response(final_ruleset, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "rule_description": rule_description,
                "type": "google_java_to_dsl"
            }

        return self._format_output(final_response, output_format)

    # 第二步，映射DSL到checkstyle
    def map_to_checkstyle(self, dsl_ruleset, model, checkstyle_ruleset=None, output_format="text", examples=""):
        """
        映射DSL规则到Checkstyle规则
        """
        # 如果没有提供checkstyle规则集，加载默认的
        if checkstyle_ruleset is None:
            checkstyle_ruleset = self._load_checkstyle_dsl()

        prompt = rule_mapper_preprocess(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google Java Style Guide",
            DSLruleset=dsl_ruleset,
            tool="Checkstyle",
            toolruleset=checkstyle_ruleset,
            example=examples
        )

        if self.gpt_agent:
            final_response = self.gpt_agent.get_response(prompt, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_checkstyle_mapping"
            }

        return self._format_output(final_response, output_format)

    # 第三步，映射子配置项
    def detailed_mapping(self, dsl_ruleset, candidate_names, model, examples=""):
        filtered_tool_rules = self._get_detailed_tool_rules(candidate_names)
        prompt = CheckstyleGenerator.preprocess_promt(  # 调用 O1 版本的 Generator Prompt
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google Java Style Guide",
            DSLruleset=dsl_ruleset,
            tool="Checkstyle",
            toolruleset=filtered_tool_rules,
            example=examples
        )
        if self.gpt_agent:
            mapping_res = self.gpt_agent.get_response(prompt, model=model)
            # 执行一遍提取，获得纯净的 "Style -> Tool (Detailed)" 映射关系
            extract_prompt = CheckstyleGenerator.extract_config_promt(mapping_res)
            final_mapping = self.gpt_agent.get_response(extract_prompt, model=model)
            return final_mapping
        return candidate_names

    # 第四步，生成checkstyle配置
    def generate_config(self, dsl_ruleset, model, checkstyle_ruleset=None, output_format="text", examples=""):
        """
        生成Checkstyle配置
        """
        if checkstyle_ruleset is None:
            checkstyle_ruleset = self._load_default_checkstyle_rules()

        # 1.验证语义匹配
        prompt = CheckstyleGenerator.validation_config_superset_semantics(
            mapping=dsl_ruleset,
            tool="Checkstyle",
            style="Google Java Style",
            toolruleset=checkstyle_ruleset
        )

        if self.gpt_agent:
            val_response = self.gpt_agent.get_response(prompt, model=model)
            # 2.提取正确映射
            filter_prompt = CheckstyleGenerator.extract_correct_mapping(
                mapping=dsl_ruleset,
                correct_information=val_response
            )
            val_mapping = self.gpt_agent.get_response(filter_prompt, model=model)
            # 快速检查一下
            if "Yes" not in val_mapping and "Mapping:" not in val_mapping:
                print("Warning: No valid mappings found after validation.")
                return None
            # 3.XML初稿
            gen_prompt = CheckstyleGenerator.gen_config_format(
                mapping=val_mapping,
                tool="Checkstyle",
                format="XML"
            )
            raw_config = self.gpt_agent.get_response(gen_prompt, model=model)
            # 4.纯净配置
            clean_prompt = CheckstyleGenerator.extract_specific_config_promt(
                text=raw_config,
                format="XML"
            )
            final_res = self.gpt_agent.get_response(clean_prompt, model=model)
            # 5.正则提取
            match = re.search(r"(<module.*</module>)", final_res, re.DOTALL)
            if match:
                return match.group(1)
            else:
                # 如果正则没匹配到，尝试直接返回（有时 GPT 会只返回 XML）
                return final_res.replace("Configuration:", "").strip()
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "checkstyle_config_generation"
            }

        return self._format_output(final_response, output_format)

    def _get_detailed_tool_rules(self, name_list_str):
        """
        根据 Step 2 返回的候选规则名列表，从 Checkstyle DSL 库中提取包含子配置项（Option Rule）的详细信息。
        逻辑完全对齐 gen_eslint_config.py。
        """
        # 1. 解析输入的规则名列表
        if isinstance(name_list_str, list):
            candidate_names = [str(n).strip() for n in name_list_str]
        else:
            # 兼容处理：提取 GPT 输出文本中的规则名
            # 注意：Checkstyle 的规则名通常是大驼峰（如 NeedBraces），所以正则不加 .lower()
            # 匹配字母和数字组成的单词
            candidate_names = re.findall(r'([a-zA-Z0-9]+)', name_list_str)

        unique_candidates = set(candidate_names)
        if not unique_candidates:
            return "No candidate rules provided."

        # 2. 加载 Checkstyle DSL 数据文件 (对应原项目的存储路径)
        # 确保此路径指向 gen_checkstyle_config.py 同级或 data 目录下的 JSON
        dsl_file_path = os.path.join(current_dir, "data", "DSL_checkstyle_all.json")

        try:
            with open(dsl_file_path, 'r', encoding='utf-8') as f:
                all_dsl_data = json.load(f)
        except Exception as e:
            print(f"Error loading Checkstyle DSL data from {dsl_file_path}: {e}")
            return ""

        # 3. 遍历库文件，查找匹配的详细信息 (包含 Basic Rule 和 Option Rule)
        detailed_results = []
        found_names = set()

        for entry in all_dsl_data:
            # entry 结构符合原项目逻辑: [url, rule_name, dsl_content]
            if len(entry) < 3:
                continue

            rule_name = entry[1]
            dsl_content = entry[2]

            if rule_name in unique_candidates:
                # 清理 DSL 内容，去除冗余标题
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()

                # 构造 Step 3 (Generator) 识别的格式
                rule_info = (
                    f"RuleName: {rule_name}\n"
                    f"{clean_dsl}"
                )
                detailed_results.append(rule_info)
                found_names.add(rule_name)

        # 4. 如果没找到任何匹配项，返回提示以免 Step 3 的 Prompt 为空
        if not detailed_results:
            return "No matching detailed rules found in Checkstyle DSL database."

        # 使用分隔符聚合，作为 Step 3 Prompt 中的 {{toolruleset}}
        return "\n\n*********************\n\n".join(detailed_results)

    # 加载checkstyle规则集
    def _load_default_checkstyle_rules(self):
        """加载默认的Checkstyle规则集"""
        # rules_dir = os.path.join(current_dir, "checkstyle", "data", "checkstyle_rules_by_category")
        rule_file = os.path.join(current_dir,"data", "checkstyle_rules_complete.json")
        all_rules = []

        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                all_rules.extend(rules)
        except Exception as e:
            print(f"警告: 无法加载规则文件 {rule_file}: {e}")

        # 转换为规则集字符串
        ruleset_text = "\n".join([
            f"RuleName: {rule.get('name', 'Unknown')}\n"
            f"Description: {rule.get('description', 'No description')}\n"
            f"Category: {rule.get('category', 'Unknown')}\n"
            for rule in all_rules  # 去除了数量限制可能导致提示词太长，原本all_rules[:50]
        ])
        # 实际上根据测试，去除数量限制不会导致提示词过长，在测试中这部分的长度大约为20k。
        return ruleset_text

    # 加载checkstyle的DSL规则集
    def _load_checkstyle_dsl(self):
        dsl_file = os.path.join(current_dir, "data", "DSL_checkstyle_all.json")

        try:
            with open(dsl_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            print(f"警告: 无法加载DSL规则集{dsl_file}: {e}\n")
            return ""
        formatted_rules = []
        for item in rules:
            if isinstance(item, list) and len(item) >= 3:
                rule_name = item[1]
                dsl_content = item[2]
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()
                # 格式化为清晰的文本块，仅保留规则名和规则逻辑
                formatted_rules.append(f"RuleName: {rule_name}\n{clean_dsl}")
        dsl_rules = "\n\n".join(formatted_rules)
        return dsl_rules

    def generate_full_checkstyle_xml(self, snippet: str) -> str:
        """
        将单个规则的配置片段包装成完整的 Checkstyle 配置文件。

        Args:
            snippet: 大模型生成的 XML 片段，如 <module name='ParameterNumber'>...</module>
        Returns:
            完整的 XML 字符串
        """
        # 处理无效输入
        if not snippet or not isinstance(snippet, str):
            print("=" * 60)
            print("输入为空或无效，返回默认配置")
            print("=" * 60)
            return """<?xml version="1.0"?>
  <!DOCTYPE module PUBLIC
  "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
  "https://checkstyle.org/dtds/configuration_1_3.dtd">

  <module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>
    <property name="fileExtensions" value="java, properties, xml"/>
  </module>"""

        # 1. 加载规则元数据 (构建 Name -> Parent 的映射字典，提高查询效率)
        rule_parent_map = {}
        rule_file = os.path.join(current_dir, "data", "checkstyle_rules_complete.json")
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                for rule in rules:
                    name = rule.get('name')
                    parent = rule.get('parent', '')
                    if name:
                        rule_parent_map[name] = parent
        except Exception as e:
            print(f"Warning: 无法读取规则元数据: {e}，将默认使用 TreeWalker 嵌套。")

        # 2. 提取所有 module 片段
        # 正则解释：匹配 <module name='Name'> ... </module>，re.DOTALL 让 . 匹配换行符
        # group(1) 是整个XML片段，group(2) 是规则名称
        # 有时用户输入不合法会产生TypeError
        try:
            module_pattern = re.compile(r"(<module\s+name=['\"](\w+)['\"].*?</module>)", re.DOTALL)
            matches = module_pattern.findall(snippet)
        except Exception as e:
            print(f"警告：无法提取配置片段: {e}\n")
            matches = None
        # 如果没有匹配到任何内容，返回默认配置
        if not matches:
            return """<?xml version="1.0"?>
  <!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">

    <module name="Checker">
      <property name="charset" value="UTF-8"/>
      <property name="severity" value="warning"/>
      <property name="fileExtensions" value="java, properties, xml"/>
    </module>"""

        checker_children = []  # 直接挂在 Checker 下的模块
        treewalker_children = []  # 挂在 TreeWalker 下的模块

        for full_xml, rule_name in matches:
            # 判断父级
            parent = rule_parent_map.get(rule_name, '')

            # 这里的逻辑是：如果明确是 Checker 下的规则（如 LineLength, FileTabCharacter），放入 checker_children
            # 否则（包括 TreeWalker 下的规则、未知规则、或者没找到元数据的规则），统统放入 TreeWalker
            # 这样鲁棒性最强，因为 Checkstyle 90% 的规则都在 TreeWalker 下
            if parent.endswith('Checker'):
                is_treewalker = False
            else:
                is_treewalker = True

            # 3. 缩进处理函数
            def reindent_snippet(xml_str, base_indent_level):
                lines = xml_str.strip().split('\n')
                formatted_lines = []
                indent_str = "  " * base_indent_level  # 每一级2个空格

                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if i == 0:
                        # <module ...> 标签
                        formatted_lines.append(f"{indent_str}{stripped}")
                    elif i == len(lines) - 1:
                        # </module> 标签
                        formatted_lines.append(f"{indent_str}{stripped}")
                    else:
                        # 中间的 <property ...> 或其他内容，增加一级缩进
                        formatted_lines.append(f"{indent_str}  {stripped}")
                return "\n".join(formatted_lines)

            # 根据归属分类并调整缩进
            if is_treewalker:
                # TreeWalker 本身在 Checker 下 (1级)，所以子模块在 (2级)
                treewalker_children.append(reindent_snippet(full_xml, 2))
            else:
                # Checker 的直接子模块在 (1级)
                checker_children.append(reindent_snippet(full_xml, 1))

        # 4. 组装最终 XML
        xml_header = """<?xml version="1.0"?>
  <!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">

  <module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>
    <property name="fileExtensions" value="java, properties, xml"/>
        """

        # 拼接 Checker 的直接子模块 (如 LineLength)
        body_content = ""
        if checker_children:
            body_content += "\n" + "\n".join(checker_children) + "\n"

        # 拼接 TreeWalker 及其子模块
        if treewalker_children:
            body_content += '\n  <module name="TreeWalker">\n'
            body_content += "\n".join(treewalker_children)
            body_content += '\n  </module>\n'

        xml_footer = "</module>"

        return xml_header + body_content + xml_footer

    def _format_output(self, content, output_format):
        """格式化输出"""
        if output_format == "json":
            if isinstance(content, str):
                try:
                    # 尝试解析为JSON
                    return json.dumps({"response": content}, ensure_ascii=False, indent=2)
                except:
                    return json.dumps({"response": content}, ensure_ascii=False)
            else:
                return json.dumps(content, ensure_ascii=False, indent=2)
        else:
            # 文本格式
            if isinstance(content, dict):
                return "\n".join([f"{k}: {v}" for k, v in content.items()])
            else:
                return str(content)

