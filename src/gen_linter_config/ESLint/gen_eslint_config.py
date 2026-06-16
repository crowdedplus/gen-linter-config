"""
Generates ESLint configuration from user-provided rules and model parameters.
"""
import os
import re
import json

from . import GPTAgent
from . import util_js
from .DSL_gpt_google_JSstyle import preprocess_promt as nl_preprocess, \
    Extract_DSL_Repr as DSL_final_extract
from . import gpt_instr_select_eslint_for_googleJS as RuleSelector
extract_basic_rule = RuleSelector.extract_basic_rule
from . import Config_set_ESLint_for_googleJS as EslintGenerator
current_dir = os.path.dirname(os.path.abspath(__file__))

class gen_eslint:
    def __init__(self, api_key=None, debug=False):
        self.dsl_syntax = util_js.dsl
        self.gpt_agent = GPTAgent(api_key, debug=debug) if GPTAgent else None
        self.debugger = self.gpt_agent.debugger if self.gpt_agent else None

    # Main entry point for processing coding standards
    def process_input(self, input_content, model, output_format="text", examples="", lightweight=True):
        print("=" * 60)
        print("Step 1: NL-to-DSL Parsing")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 1: NL-to-DSL Parsing")
        dsl_result = self.process_nl_rule(input_content, model, output_format, examples)
        print(dsl_result)

        print("\n" + "=" * 60)
        print("Step 2: Candidate Rule Name Selection")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 2: Candidate Rule Name Selection")
        mapping_result = self.map_to_eslint(dsl_result, model, output_format=output_format, examples=examples, lightweight=lightweight)
        print(mapping_result)

        print("\n" + "=" * 60)
        print("Step 3: Option Rule Configuration")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 3: Option Rule Configuration")
        detailed_mapping = self.step_3_detailed_mapping(dsl_result,mapping_result,model,examples,lightweight=lightweight)
        print(detailed_mapping)

        print("\n" + "=" * 60)
        print("Step 4: Configuration Generation")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 4: Alignment Check & Configuration Generation")
        config_result = self.generate_config(detailed_mapping, model, output_format=output_format, examples=examples)

        final_res = self.generate_full_eslint_js(config_result)
        # print("\n" + "=" * 30 + "    :")
        print(final_res)
        return final_res

    # Step 1: NL to DSL
    def process_nl_rule(self, rule_description, model, output_format="text", examples=""):
        """
        Convert natural language coding style rules to DSL
        """
        prompt = nl_preprocess(
            rule=rule_description,
            DSL_Syntax=self.dsl_syntax,
            example=examples,
            PL="JavaScript"
        )

        # First call: NL analysis -> DSL with reasoning steps. Second call: extract pure DSL.
        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("1.1 NL Analysis -> DSL")
            gpt_response = self.gpt_agent.get_response(prompt, model=model)
            final_ruleset = DSL_final_extract(gpt_response)
            if self.debugger:
                self.debugger.sub_step("1.2 Extract Pure DSL")
            final_response = self.gpt_agent.get_response(final_ruleset, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "rule_description": rule_description,
                "type": "google_js_to_dsl"
            }

        return self._format_output(final_response, output_format)

    # Step 2: Map DSL to ESLint DSL rule set
    def map_to_eslint(self, dsl_ruleset, model, output_format="text", examples="", lightweight=True):
        """
        Map DSL rules to ESLint rules
        """
        if lightweight:
            dsl_basic_rules = self._load_eslint_json_rules(mode="basic")
        else:
            dsl_basic_rules = self._load_eslint_dsl_basic_rules()

        rule_count = dsl_basic_rules.count('"name"') if lightweight else (dsl_basic_rules.count("RuleName:") if dsl_basic_rules else 0)
        print("="*15 + f"Mapping against {rule_count} ESLint rules.")

        if lightweight:
            dsl_basic_rules = "ESLint rules in JSON format. Each line is a JSON object with 'name' and 'options' keys.\n" + dsl_basic_rules

        prompt = RuleSelector.preprocess_promt(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google JavaScript Style Guide",
            DSLruleset=dsl_ruleset,
            tool="ESLint",
            toolruleset=dsl_basic_rules,
            example=examples
        )

        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("2.1 Candidate Rule Name Selection")
            # The model should only return a list of rule names.
            final_response = self.gpt_agent.get_response(prompt, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_eslint_mapping"
            }
        return self._format_output(final_response, output_format)

    # Step 3: Map sub configuration options
    def step_3_detailed_mapping(self,dsl_ruleset, candidate_names, model, examples="", lightweight=True):
        if lightweight:
            filtered_tool_rules = self._get_detailed_tool_rules_json(candidate_names, data_type="eslint")
        else:
            filtered_tool_rules = self._get_detailed_tool_rules(candidate_names)

        if lightweight:
            filtered_tool_rules = "ESLint rules in JSON format.\n" + filtered_tool_rules
        prompt = EslintGenerator.preprocess_promt(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google JavaScript Style Guide",
            DSLruleset=dsl_ruleset,
            tool="ESLint",
            toolruleset=filtered_tool_rules,
            example=examples
        )
        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("3.1 Detailed Option Mapping")
            mapping_res = self.gpt_agent.get_response(prompt,model=model)
            extract_prompt = EslintGenerator.extract_config_promt(mapping_res)
            if self.debugger:
                self.debugger.sub_step("3.2 Extract Mappings")
            final_mapping = self.gpt_agent.get_response(extract_prompt,model=model)
            # Step 3.1: Extract non-empty config mappings
            extract_non_empty_prompt = EslintGenerator.extract_non_empty_config_promt(final_mapping)
            if self.debugger:
                self.debugger.sub_step("3.3 Filter Empty Mappings")
            final_mapping = self.gpt_agent.get_response(extract_non_empty_prompt, model=model)
            if "Yes" not in final_mapping:
                return "No valid mappings found."
            # Step 3.2: Regex placeholder processing
            if "regular expression" in final_mapping.lower():
                if self.debugger:
                    self.debugger.sub_step("3.4 Regex Value Analysis")
                set_value_answer = self.gpt_agent.get_response(
                    f'For each mapping, if any option name value is "regular expression", only set specific regular expression value of option names to match rule\n'
                    f' Must set specific regular expression values!\n\n'
                    f'        {final_mapping}',
                    model=model)
                if self.debugger:
                    self.debugger.sub_step("3.5 Replace Regex Placeholder")
                answer_map_with_value = self.gpt_agent.get_response(
                    f'Based on the following Analysis, only Replace "regular expression" with setting regular expression values for the following mapping. And then give new Mappings.\n'
                    f'1. Extract specific regular expression values for "regular expression" value from the following Analysis.\n'
                    f'2. Replace "regular expression" value with corresponding specific regular expression values within the following mapping.\n'
                    f'Must set specific specific regular expression values!\n\n'
                    f'Finally give new Mappings with same number of mappings.\n\n'
                    f'Analysis:\n{set_value_answer}\n\n'
                    f'Mapping:\n{final_mapping}\n        ',
                    model=model)
                extract_with_value = EslintGenerator.extract_config_promt(answer_map_with_value)
                if self.debugger:
                    self.debugger.sub_step("3.6 Extract Regex-Replaced Mappings")
                final_mapping = self.gpt_agent.get_response(extract_with_value, model=model)
            return final_mapping
        else :
            final_mapping = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_eslint_mapping"
            }
        return final_mapping

    # Step 4: Semantic validation & generate ESLint config
    def generate_config(self, detailed_mappings, model, eslint_ruleset=None, output_format="text", examples=""):
        """
        Generate ESLint configuration (JSON snippet)
        """
        if eslint_ruleset is None:
            eslint_ruleset = self._load_default_eslint_rules()

        if self.gpt_agent:
            # Step 4.0: Merge option rules — combine Basic Rule and Option Rule into one compact ToolSEM rule
            if self.debugger:
                self.debugger.sub_step("4.0 Extract ToolSEM Rules")
            tool_sem_rules = self.gpt_agent.get_response(
                f'For the following mappings,before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. \n'
                f'You only excerpt ToolSEM rule consisting of Rulename, Basic rule and Option rules.\n\n'
                f'Mappings:\n{detailed_mappings}\n\n'
                f'Response Format: Please do not give explanation.\n'
                f'1. RuleName: ...\n'
                f'   Basic Rule: ...\n'
                f'   Option Rule: \n'
                f'     ...\n'
                f'2. ...\n'
                f'...\n',
                model=model)
            merg_prompt = EslintGenerator.merge_basic_option_rules(tool_sem_rules)
            if self.debugger:
                self.debugger.sub_step("4.1 Merge Option Rules")
            merge_answer_map = self.gpt_agent.get_response(merg_prompt, model=model)
            prompt_extract_merge = EslintGenerator.extract_merge_mappings_promt(
                text=merge_answer_map, answer_map=detailed_mappings)
            if self.debugger:
                self.debugger.sub_step("4.2 Extract Merged Mappings")
            detailed_mappings = self.gpt_agent.get_response(prompt_extract_merge, model=model)

            # 1. Validate semantic match
            prompt = EslintGenerator.validation_config_superset_semantics(
                mapping=detailed_mappings,
                tool="ESLint",
                style="Google JavaScript Style",
                toolruleset=eslint_ruleset
            )
            if self.debugger:
                self.debugger.sub_step("4.3 Semantic Validation")
            val_response = self.gpt_agent.get_response(prompt, model=model)
            # 2. Extract correct mappings
            filter_prompt = EslintGenerator.extract_correct_mapping(
                mapping=detailed_mappings,
                correct_information=val_response
            )
            if self.debugger:
                self.debugger.sub_step("4.4 Extract Correct Mappings")
            val_mapping = self.gpt_agent.get_response(filter_prompt, model=model)
            if "Yes" not in val_mapping and "Mapping:" not in val_mapping:
                print("Warning: No valid mappings found after validation.")
                return None

            # 3. JSON first draft
            gen_prompt = EslintGenerator.gen_config_format(
                mapping=val_mapping,
                tool="ESLint",
                format="JSON"
            )
            if self.debugger:
                self.debugger.sub_step("4.5 Generate JSON Draft")
            raw_config = self.gpt_agent.get_response(gen_prompt, model=model)

            # 4. Extract clean config
            clean_prompt = EslintGenerator.extract_specific_config_promt(
                text=raw_config,
                format="JSON"
            )
            if self.debugger:
                self.debugger.sub_step("4.6 Extract Clean JSON")
            final_res = self.gpt_agent.get_response(clean_prompt, model=model)
            final_res = util_js.process_ESLint_Json(final_res)
            final_res = re.search(r'\{[^{}]*\}', final_res, re.DOTALL).group() if re.search(r'\{[^{}]*\}', final_res, re.DOTALL) else ""

            # 5. Clean Markdown markers
            final_res = final_res.replace("```json", "").replace("```", "").strip()
            if "Configuration:" in final_res:
                final_res = final_res.replace("Configuration:", "").strip()

            return final_res
        else:
            final_response = {
                "dsl_ruleset": detailed_mappings,
                "type": "eslint_config_generation"
            }

        return self._format_output(final_response, output_format)

    # Load ESLint rules (for semantic validation etc.)
    def _load_default_eslint_rules(self, return_raw=False):
        """
        Load default ESLint rules
        Args:
            return_raw: if True, return list; otherwise return formatted string
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
            print(f"Warning: failed to load rules file {rule_file}: {e}")

        if return_raw:
            return all_rules

        # Default behavior remains (for compatibility, though we modify map_to_eslint below)
        ruleset_text = "\n".join([
            f"RuleName: {rule.get('name', 'Unknown')}\n"
            f"Description: {rule.get('description', 'No description')}\n"
            for rule in all_rules
        ])
        return ruleset_text


    def _load_eslint_json_rules(self, mode="basic"):
        """Lightweight mode: load raw JSON rules instead of DSL-formatted text."""
        json_file = os.path.join(current_dir, "data", "eslint_rules_complete.json")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Warning: failed to load JSON rules from {json_file}: {e}\n")
            return ""

        if mode == "basic":
            lines = []
            for r in rules:
                opts = r.get("options", [])
                if isinstance(opts, list) and opts and isinstance(opts[0], dict) and "properties" in opts[0]:
                    opt_names = list(opts[0]["properties"].keys())
                elif isinstance(opts, list):
                    opt_names = [o.get("name", str(o)) for o in opts]
                else:
                    opt_names = []
                line = f'{{"name": "{r["name"]}", "category": "{r.get("category","")}", "options": {json.dumps(opt_names, ensure_ascii=False)}}}'
                lines.append(line)
            return "\n".join(lines)
        else:
            lines = []
            for r in rules:
                line = json.dumps({"name": r["name"], "category": r.get("category", ""), "description": r.get("description", ""), "options": r.get("options", [])}, ensure_ascii=False)
                lines.append(line)
            return "\n".join(lines)

    def _get_detailed_tool_rules_json(self, name_list_str, data_type="eslint"):
        """Lightweight mode: filter JSON rules by candidate names and return as compact JSON."""
        if isinstance(name_list_str, list):
            candidate_names = [str(n).strip() for n in name_list_str]
        else:
            candidate_names = re.findall(r'([a-z0-9\-]+)', name_list_str.lower())
        unique_candidates = set(candidate_names)
        if not unique_candidates:
            return "No candidate rules provided."

        json_file = os.path.join(current_dir, "data", "eslint_rules_complete.json")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                all_rules = json.load(f)
        except Exception as e:
            print(f"Error loading JSON rules: {e}")
            return ""

        matched = []
        for r in all_rules:
            if r["name"] in unique_candidates:
                matched.append(json.dumps({"name": r["name"], "description": r.get("description", ""), "options": r.get("options", [])}, ensure_ascii=False))
        if not matched:
            return "No matching detailed rules found."
        return "\n".join(matched)

    def _load_eslint_dsl_basic_rules(self):
        dsl_file = os.path.join(current_dir, "data", "DSL_ESLint_all.json")
        try:
            with open(dsl_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Warning: failed to load DSL rule file {dsl_file}: {e}\n")
            return ""

        basic_rules_lines = []
        for item in rules:
            if isinstance(item, list) and len(item) >= 3:
                rule_name = item[1]
                dsl_content = item[2]
                basic_rule = extract_basic_rule(dsl_content)
                basic_rules_lines.append(f"RuleName: {rule_name}\n{basic_rule}")
        return "\n".join(basic_rules_lines)

    def generate_full_eslint_js(self, snippet: str) -> str:
        if not snippet:
            return "// Error: No configuration generated."

        try:
            rules_obj = json.loads(snippet)
            formatted = json.dumps(rules_obj, indent=4)
            # Remove outer { and }, keep original indentation of each internal line
            lines = formatted.strip().split("\n")[1:-1]
            indented = "\n".join("        " + line for line in lines)
        except json.JSONDecodeError:
            try:
                import ast
                obj = ast.literal_eval(snippet.strip())
                formatted = json.dumps(obj, indent=4)
                lines = formatted.strip().split("\n")[1:-1]
                indented = "\n".join("        " + line for line in lines)
            except Exception:
                # Final fallback: handle line by line
                inner = snippet.strip()
                if inner.startswith("{") and inner.endswith("}"):
                    inner = inner[1:-1].strip()
                indented = "\n".join(
                    "            " + line.strip()
                    for line in inner.replace(",", ",\n").split("\n") if line.strip()
                )

        return (
            "// eslint.config.js\n"
            "import { defineConfig } from \"eslint/config\";\n"
            "\n"
            "export default defineConfig([\n"
            "    {\n"
            "        rules: {\n"
            + indented + "\n"
            "        }\n"
            "    }\n"
            "]);"
        )


    def _get_detailed_tool_rules(self, name_list_str):
        # Extract detailed DSL containing Option Rule from DSL_ESLint_all.json by selected rule names
        """
            Based on the candidate rule name list returned by Step 2, extract detailed information from ESLint DSL library.

            Args:
                name_list_str (str): rule name info returned by GPT, may be "1. rule-a\n2. rule-b"
                                      or "['rule-a', 'rule-b']".
            Returns:
                str: formatted detailed DSL rule text for Step 3 Prompt.
            """
        # 1. Parse input rule name list
        # Use regex to extract all strings matching ESLint naming (lowercase letters, digits, hyphens)
        if isinstance(name_list_str, list):
            candidate_names = [str(n).strip() for n in name_list_str]
        else:
            # Compatible handling: extract rule names from GPT output text, filter serial numbers and brackets
            candidate_names = re.findall(r'([a-z0-9\-]+)', name_list_str.lower())

        unique_candidates = set(candidate_names)
        if not unique_candidates:
            return "No candidate rules provided."

        # 2. Load DSL data file
        # Path should point to DSL_ESLint_all.json
        dsl_file_path = os.path.join(current_dir, "data", "DSL_ESLint_all.json")

        try:
            with open(dsl_file_path, 'r', encoding='utf-8') as f:
                all_dsl_data = json.load(f)
        except Exception as e:
            print(f"Error loading DSL data: {e}")
            return ""

        # 3. Iterate library to find matching details
        detailed_results = []
        found_names = set()

        for entry in all_dsl_data:
            # entry format: [url, rule_name, dsl_content]
            if len(entry) < 3:
                continue

            rule_url = entry[0]
            rule_name = entry[1]
            dsl_content = entry[2]

            if rule_name in unique_candidates:
                # Clean DSL content, remove redundant headers, keep core rule structure
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()

                # Construct Step 3-compatible format
                rule_info = (
                    f"RuleName: {rule_name}\n"
                    f"{clean_dsl}"
                )
                detailed_results.append(rule_info)
                found_names.add(rule_name)

        # 4. If not found, try fuzzy match (optional logic, adjust based on needs)
        if not detailed_results:
            return "No matching detailed rules found in DSL database."

        # Return aggregated text as {{toolruleset}} for Step 3 Prompt
        return "\n\n*********************\n\n".join(detailed_results)

    def _format_output(self, content, output_format):
        """Format output"""
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