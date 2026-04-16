"""
该文件需要实现的功能：
读取指令的所有参数之后返回eslint配置。
"""
import os
import re
import json

from gen_linter_config import GPTAgent,util_js
from .DSL_gpt_google_JSstyle import preprocess_promt as nl_preprocess, \
    Extract_DSL_Repr as DSL_final_extract
from . import gpt_instr_select_eslint_for_googleJS as RuleSelector
from . import Config_set_ESLint_for_googleJS as EslintGenerator
current_dir = os.path.dirname(os.path.abspath(__file__))

class gen_eslint:
    def __init__(self):
        self.dsl_syntax = util_js.dsl
        self.gpt_agent = GPTAgent() if GPTAgent else None

    # 处理代码规范的总入口
    def process_input(self, input_content, model, output_format="text", examples=""):
        print("=" * 60)
        print("步骤1: NL代码规范转换为DSL  --  1轮对话")
        print("=" * 60)
        dsl_result = self.process_nl_rule(input_content, model, output_format, examples)
        print(dsl_result)

        print("\n" + "=" * 60)
        print("步骤2: 提取候选规则名  --  1轮对话")
        print("=" * 60)
        mapping_result = self.map_to_eslint(dsl_result, model, output_format=output_format, examples=examples)
        print(mapping_result)

        print("\n" + "=" * 60)
        print("步骤3: 详细选项映射  --  1轮对话")
        print("=" * 60)
        detailed_mapping = self.step_3_detailed_mapping(dsl_result,mapping_result,model,examples)
        print(detailed_mapping)

        print("\n" + "=" * 60)
        print("步骤4: 生成ESLint配置  --  4轮对话")
        print("=" * 60)
        config_result = self.generate_config(detailed_mapping, model, output_format=output_format, examples=examples)

        final_res = self.generate_full_eslint_js(config_result)
        # print("\n" + "=" * 30 + "    :")
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
            example=examples,
            PL="JavaScript"
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
                "type": "google_js_to_dsl"
            }

        return self._format_output(final_response, output_format)

    # 第二步，映射DSL到ESLint的DSL规则集中
    def map_to_eslint(self, dsl_ruleset, model, output_format="text", examples=""):
        """
        映射DSL规则到ESLint规则
        """
        # 1. 获取所有规则的原始数据列表
        all_eslint_rules = self._load_default_eslint_rules(return_raw=True)

        # 2. 针对当前的 DSL 规则集，筛选出相关的 ESLint 规则
        relevant_rules = self._filter_relevant_rules(dsl_ruleset, all_eslint_rules, top_k=30)  # 选出最相关的30条

        # 3. 将筛选出的规则转换为字符串格式
        filtered_ruleset_text = "\n".join([
            f"RuleName: {rule.get('name', 'Unknown')}\n"
            f"Description: {rule.get('description', 'No description')}\n"
            f"Options: {json.dumps(rule.get('options', []), ensure_ascii=False)}\n"  # 加上 Options 有助于模型判断
            for rule in relevant_rules
        ])

        print(f"提示：已从 {len(all_eslint_rules)} 条规则中筛选出 {len(relevant_rules)} 条相关规则用于映射。")

        # 4. 生成 Prompt
        prompt = RuleSelector.preprocess_promt(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google JavaScript Style Guide",
            DSLruleset=dsl_ruleset,
            tool="ESLint",
            toolruleset=filtered_ruleset_text,  # 传入筛选后的文本
            example=examples
        )

        if self.gpt_agent:
            # 大模型应该只会返回规则名列表。
            final_response = self.gpt_agent.get_response(prompt, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_eslint_mapping"
            }
        return self._format_output(final_response, output_format)

    # 第三步，匹配子配置选项
    def step_3_detailed_mapping(self,dsl_ruleset, candidate_names, model, examples=""):
        filtered_tool_rules = self._get_detailed_tool_rules(candidate_names)
        prompt = EslintGenerator.preprocess_promt(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google JavaScript Style Guide",
            DSLruleset=dsl_ruleset,
            tool="ESLint",
            toolruleset=filtered_tool_rules,
            example=examples
        )
        if self.gpt_agent:
            mapping_res = self.gpt_agent.get_response(prompt,model=model)
            extract_prompt = EslintGenerator.extract_config_promt(mapping_res)
            final_mapping = self.gpt_agent.get_response(extract_prompt,model=model)
        else :
            final_mapping = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_eslint_mapping"
            }
        return final_mapping

    # 第四步，语义验证 & 生成ESLint配置
    def generate_config(self, detailed_mappings, model, eslint_ruleset=None, output_format="text", examples=""):
        """
        生成ESLint配置 (JSON片段)
        """
        if eslint_ruleset is None:
            eslint_ruleset = self._load_default_eslint_rules()

        # 1.验证语义匹配
        prompt = EslintGenerator.validation_config_superset_semantics(
            mapping=detailed_mappings,
            tool="ESLint",
            style="Google JavaScript Style",
            toolruleset=eslint_ruleset
        )

        if self.gpt_agent:
            val_response = self.gpt_agent.get_response(prompt, model=model)
            # print("\n" + "="*30+"语义验证分析结果 :")
            # print("\n" + val_response)
            # 2.提取正确映射
            filter_prompt = EslintGenerator.extract_correct_mapping(
                mapping=detailed_mappings,
                correct_information=val_response
            )
            val_mapping = self.gpt_agent.get_response(filter_prompt, model=model)
            # print("\n" + "="*30+"正确映射结果 :")
            # print("\n" + val_mapping)
            # 快速检查
            if "Yes" not in val_mapping and "Mapping:" not in val_mapping:
                print("Warning: No valid mappings found after validation.")
                return None

            # 3.JSON初稿
            gen_prompt = EslintGenerator.gen_config_format(
                mapping=val_mapping,
                tool="ESLint",
                format="JSON"
            )
            raw_config = self.gpt_agent.get_response(gen_prompt, model=model)
            # print("\n" + "="*30+"json初稿 :")
            # print(raw_config)

            # 4.纯净配置提取
            clean_prompt = EslintGenerator.extract_specific_config_promt(
                text=raw_config,
                format="JSON"
            )
            final_res = self.gpt_agent.get_response(clean_prompt, model=model)
            final_res = util_js.process_ESLint_Json(final_res)
            final_res = re.search(r'\{[^{}]*\}', final_res, re.DOTALL).group() if re.search(r'\{[^{}]*\}', final_res, re.DOTALL) else ""
            # print("\n" + "="*30+"提取的所谓纯净配置(util) :")
            # print(final_res)

            # 5. 清洗 Markdown 标记
            final_res = final_res.replace("```json", "").replace("```", "").strip()
            if "Configuration:" in final_res:
                final_res = final_res.replace("Configuration:", "").strip()

            return final_res
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": detailed_mappings,
                "type": "eslint_config_generation"
            }

        return self._format_output(final_response, output_format)

    # 加载ESLint规则集 (用于语义验证等)
    def _load_default_eslint_rules(self, return_raw=False):
        """
        加载默认的ESLint规则集
        Args:
            return_raw: 如果为True，返回列表对象；否则返回格式化后的字符串
        """
        rule_file = os.path.join(current_dir, "data", "eslint_rules_complete.json")
        all_rules = []

        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                if isinstance(rules, list):
                    all_rules.extend(rules)
                elif isinstance(rules, dict):
                    all_rules.extend(rules.values())
        except Exception as e:
            print(f"警告: 无法加载规则文件 {rule_file}: {e}")

        if return_raw:
            return all_rules

        # 默认行为保持不变（为了兼容其他可能的调用，虽然下面我们会改 map_to_eslint）
        ruleset_text = "\n".join([
            f"RuleName: {rule.get('name', 'Unknown')}\n"
            f"Description: {rule.get('description', 'No description')}\n"
            for rule in all_rules
        ])
        return ruleset_text

    # 加载ESLint的DSL规则集 (用于映射)
    def _load_eslint_dsl(self):
        dsl_file = os.path.join(current_dir, "data", "DSL_ESLint_all.json")

        try:
            with open(dsl_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            print(f"警告: 无法加载DSL规则集{dsl_file}: {e}\n")
            return ""

        formatted_rules = []
        for item in rules:
            # 假设结构: [url, rule_name, dsl_content]
            if isinstance(item, list) and len(item) >= 3:
                rule_name = item[1]
                dsl_content = item[2]
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()
                formatted_rules.append(f"RuleName: {rule_name}\n{clean_dsl}")

        dsl_rules = "\n\n".join(formatted_rules)
        return dsl_rules

    def generate_full_eslint_js(self, snippet: str) -> str:
        """
        将生成的 JSON 规则片段包装成完整的 eslint.config.js 文件格式。

        Args:
            snippet: 大模型生成的 JSON 规则片段，例如 { "rule-name": ["error", ...] }
        Returns:
            完整的 JS 配置文件字符串
        """
        if not snippet:
            return "// Error: No configuration generated."

        # 尝试解析 JSON 以便重新格式化（如果需要美化），或者直接使用字符串
        try:
            rules_obj = json.loads(snippet)
            formatted_rules = json.dumps(rules_obj, indent=12) # 增加缩进以匹配模板
            # 去掉最外层的大括号，因为我们要把它放进 rules: { ... } 里面
            formatted_rules = formatted_rules.strip()[1:-1].strip()
        except json.JSONDecodeError:
            # 如果不是严格的 JSON (可能是 JS 对象格式)，则直接使用文本处理
            formatted_rules = snippet.strip()
            if formatted_rules.startswith("{"):
                formatted_rules = formatted_rules[1:]
            if formatted_rules.endswith("}"):
                formatted_rules = formatted_rules[:-1]
            formatted_rules = formatted_rules.strip()

        # ESLint Flat Config 模板
        js_template = """// eslint.config.js
import { defineConfig } from "eslint/config";

export default defineConfig([
    {
        rules: {
            %s
        }
    }
]);"""

        return js_template % formatted_rules

    def _filter_relevant_rules(self, dsl_text, all_rules_data, top_k=20):
        """
        根据 DSL 文本中的关键词，从所有规则中筛选出最相关的 top_k 条规则。
        这是一个简单的关键词匹配实现，也可以换成向量检索。
        """
        # 1. 提取 DSL 中的关键词 (去掉常见停用词)
        # 简单的分词：提取所有字母组成的单词
        keywords = set(re.findall(r"[a-zA-Z]+", dsl_text))
        # 过滤掉一些通用词 (根据需要补充)
        stop_words = {"Mandatory", "Optional", "Rule", "is", "not", "of", "in", "the", "and", "or", "if", "then"}
        keywords = {k for k in keywords if k not in stop_words and len(k) > 2}

        scored_rules = []

        for rule in all_rules_data:
            score = 0
            rule_content = (rule.get('name', '') + " " + rule.get('description', '')).lower()

            # 2. 计算匹配分数
            for kw in keywords:
                if kw.lower() in rule_content:
                    score += 1

            # 优先保留完全匹配规则名的
            if any(kw.lower() == rule.get('name', '').lower() for kw in keywords):
                score += 5

            if score > 0:
                scored_rules.append((score, rule))

        # 3. 排序并取前 K 个
        # 按分数降序排列
        scored_rules.sort(key=lambda x: x[0], reverse=True)

        # 如果匹配到的太少，补一些通用的或者直接返回前几个
        selected_rules = [r[1] for r in scored_rules[:top_k]]

        # 如果没匹配到任何规则，为了防止空上下文，返回全部规则的前20个作为保底
        if not selected_rules:
            return all_rules_data[:top_k]

        return selected_rules

    def _get_detailed_tool_rules(self, name_list_str):
        # 根据选中的名字从DSL_ESLint_all.json文件中提取包含Option Rule的详细DSL
        """
            根据 Step 2 返回的候选规则名列表，从 ESLint DSL 库中提取包含子配置项（Option Rule）的详细信息。

            Args:
                name_list_str (str): GPT 返回的规则名称信息，可能是 "1. rule-a\n2. rule-b"
                                     或 "['rule-a', 'rule-b']" 等格式。
            Returns:
                str: 格式化后的详细 DSL 规则文本，用于 Step 3 的 Prompt。
            """
        # 1. 解析输入的规则名列表
        # 使用正则表达式提取所有符合 ESLint 命名的字符串 (小写字母、数字、中划线)
        if isinstance(name_list_str, list):
            candidate_names = [str(n).strip() for n in name_list_str]
        else:
            # 兼容处理：提取 GPT 输出文本中的规则名，过滤掉序号、括号等
            candidate_names = re.findall(r'([a-z0-9\-]+)', name_list_str.lower())

        unique_candidates = set(candidate_names)
        if not unique_candidates:
            return "No candidate rules provided."

        # 2. 加载 DSL 数据文件
        # 路径确保指向 DSL_ESLint_all.json
        dsl_file_path = os.path.join(current_dir, "data", "DSL_ESLint_all.json")

        try:
            with open(dsl_file_path, 'r', encoding='utf-8') as f:
                all_dsl_data = json.load(f)
        except Exception as e:
            print(f"Error loading DSL data: {e}")
            return ""

        # 3. 遍历库文件，查找匹配的详细信息
        detailed_results = []
        found_names = set()

        for entry in all_dsl_data:
            # entry 格式: [url, rule_name, dsl_content]
            if len(entry) < 3:
                continue

            rule_url = entry[0]
            rule_name = entry[1]
            dsl_content = entry[2]

            if rule_name in unique_candidates:
                # 清理 DSL 内容（移除冗余的标题，保留核心规则结构）
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()

                # 构造 Step 3 识别的格式
                rule_info = (
                    f"RuleName: {rule_name}\n"
                    f"{clean_dsl}"
                )
                detailed_results.append(rule_info)
                found_names.add(rule_name)

        # 4. 如果没找到，尝试模糊匹配（可选逻辑，根据实际需求决定）
        if not detailed_results:
            return "No matching detailed rules found in DSL database."

        # 返回聚合后的长文本，作为 Step 3 Prompt 中的 {{toolruleset}}
        return "\n\n*********************\n\n".join(detailed_results)

    def _format_output(self, content, output_format):
        """格式化输出"""
        if output_format == "json":
            if isinstance(content, str):
                try:
                    return json.dumps({"response": content}, ensure_ascii=False, indent=2)
                except:
                    return json.dumps({"response": content}, ensure_ascii=False)
            else:
                return json.dumps(content, ensure_ascii=False, indent=2)
        else:
            if isinstance(content, dict):
                return "\n".join([f"{k}: {v}" for k, v in content.items()])
            else:
                return str(content)