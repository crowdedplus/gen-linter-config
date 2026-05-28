"""
Core functionality:
Generate a Checkstyle XML configuration from natural language style instructions.
"""
import os
import re
import json

from . import GPTAgent
from . import util_java
from .DSL_gpt_google_java_style import preprocess_promt as nl_preprocess, \
    Extract_DSL_Repr as DSL_final_extract
from .Config_name_select_checkstyle_for_googlejava_one import preprocess_promt as rule_mapper_preprocess, \
    extract_basic_rule
from . import Config_set_checkstyle_for_googlejava_ours_o1 as CheckstyleGenerator
current_dir = os.path.dirname(os.path.abspath(__file__))

class gen_checkstyle:
    def __init__(self, api_key=None, debug=False):
        self.dsl_syntax = util_java.dsl
        self.gpt_agent = GPTAgent(api_key, debug=debug) if GPTAgent else None
        self.debugger = self.gpt_agent.debugger if self.gpt_agent else None

    # Main entry point for processing code style rules
    def process_input(self,  input_content, model, output_format="text", examples=""):
        print("=" * 60)
        print("Step 1: NL-to-DSL Parsing")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 1: NL-to-DSL Parsing")
        dsl_result = self.process_nl_rule(input_content, model, output_format, examples)
        print(dsl_result)

        print("\n" + "=" * 60)
        print("Step 2: Selection of the configuration name.")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 2: Selection of the configuration name")
        mapping_result = self.map_to_checkstyle(dsl_result,model, output_format=output_format, examples=examples)
        print(mapping_result)

        # --- Step 3: Detailed Option Mapping (sub-option config generation) ---
        print("\n" + "=" * 60)
        print("Step 3: Option Rule Configuration")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 3: Option Rule Configuration")
        detailed_mapping = self.detailed_mapping(dsl_result, mapping_result, model, examples)
        print(detailed_mapping)

        # --- Step 4: Configuration Generation ---
        print("\n" + "=" * 60)
        print("Step 4: Alignment Check & Configuration Generation")
        print("=" * 60)
        if self.debugger:
            self.debugger.step("Step 4: Alignment Check & Configuration Generation")
        config_result = self.generate_config(detailed_mapping, model, output_format=output_format, examples=examples)
        final_res = self.generate_full_checkstyle_xml(config_result)
        print(final_res)
        return final_res

    # Step 1: Convert natural language to DSL
    def process_nl_rule(self, rule_description, model, output_format="text", examples=""):
        """
        Convert natural language code style to DSL
        """
        examples = '''For Example, Analyze the following {{Style}}, please parse the style using the given {{grammar}}.

        {{Style}}:
        The column limit, Section 4.4, Column limit: 100, does not apply to package statements.
        Braces are used with `if` , `else` , `for` , `do` and `while` statements (even when the body is empty or contains only a single statement).
        Each type variable is named in one of two styles:
        A single capital letter, optionally followed by a single numeral (such as `E` , `T` , `X` , `T2` )
        A name in the form used for classes (see Section 5.2.2, Class names ), followed by the capital letter `T` (examples: `RequestT` , `FooBarT` ).
        A single blank line always appears:
        Between consecutive members or initializers of a class: fields, constructors, methods, nested classes, static initializers, and instance initializers.
        Exception: A blank line between two consecutive fields (having no other code between them) is optional. Such blank lines are used as needed to create logical groupings of fields.
        Exception: Blank lines between enum constants are covered in Section 4.8.1 .
        Any of the standard "block tags" that are used appear in the order `@param` , `@return` , `@throws` , `@deprecated` , and these four types never appear with an empty description.

        Final RuleSet Representation:
        Mandatory: [ColumnLimit] is [100]
        ;
        Optional: [ColumnLimit] not for [PackageStatement]
        ;
        Mandatory: [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
        Or
        Mandatory: if [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] is [Null]
                   then [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
        Or
        Mandatory: if Number of [statement] of [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] = 1
                   then [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
        ;
        Mandatory: [TypeVariable] is [CapitalLetter]
        Or
        Mandatory: [TypeVariable] is [CapitalLetter] + [Numeral]
        Or
        Mandatory: [TypeVariable] is [ClassName] + [CapitalLetterT]
        ;
        Mandatory: [BlankLine] between [ConsecutiveMembers] or [Initializers] of [Class] : [fields, constructors, methods, nested classes, static initializers, and instance initializers]
        And
        Mandatory: Number of [BlankLine] between [ConsecutiveMembers] or [Initializers] of [Class] : [fields, constructors, methods, nested classes, static initializers, and instance initializers] = 1
        Or
        Optional: [BlankLine] between [two consecutive fields] that not have [other code] between [two consecutive fields]
        Or
        Optional: [BlankLine] between [enum constants] in Section 4.8.1
        ;
        Mandatory: Order of [BlockTag] is [@param, @return, @throws, @deprecated]
        And
        Mandatory: No [EmptyDescription] for [@param, @return, @throws, @deprecated
        '''
#         examples="""{{Style}}:
# The column limit, Section 4.4, Column limit: 100, does not apply to package statements.
#
# Final RuleSet Representation:
# Optional: [ColumnLimit] is [100] not for [PackageStatement]"""
        prompt = nl_preprocess(
            rule=rule_description,
            DSL_Syntax=self.dsl_syntax,
            example=examples
        )

        # First pass: NL to DSL with reasoning; second pass: extract pure DSL.
        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("1.1 NL Analysis -> DSL")
            gpt_response = self.gpt_agent.get_response(prompt, model=model)
            # print("="*60+"\n"+gpt_response+"="*60)
            final_ruleset = DSL_final_extract(gpt_response)
            if self.debugger:
                self.debugger.sub_step("1.2 Extract Pure DSL")
            final_response = self.gpt_agent.get_response(final_ruleset, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "rule_description": rule_description,
                "type": "google_java_to_dsl"
            }

        return self._format_output(final_response, output_format)

# Step 2: Map DSL to Checkstyle
    def map_to_checkstyle(self, dsl_ruleset, model, checkstyle_ruleset=None, output_format="text", examples=""):
        """
        Map DSL rules to Checkstyle rules
        """
        dsl_basic_rules = self._load_checkstyle_dsl_basic_rules()

        rule_count = dsl_basic_rules.count("RuleName:") if dsl_basic_rules else 0
        print("="*15 + f"Mapping against {rule_count} Checkstyle DSL Basic Rules.")

        if checkstyle_ruleset is None:
            checkstyle_ruleset = dsl_basic_rules

        prompt = rule_mapper_preprocess(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google Java Style Guide",
            DSLruleset=dsl_ruleset,
            tool="Checkstyle",
            toolruleset=checkstyle_ruleset,
            example=examples
        )

        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("2.1 Candidate Rule Name Selection")
            final_response = self.gpt_agent.get_response(prompt, model=model)
        else:
            final_response = {
                "prompt": prompt,
                "dsl_ruleset": dsl_ruleset,
                "type": "dsl_to_checkstyle_mapping"
            }

        return self._format_output(final_response, output_format)

    # Step 3: Map sub-option rules
    def detailed_mapping(self, dsl_ruleset, candidate_names, model, examples=""):
        filtered_tool_rules = self._get_detailed_tool_rules(candidate_names)
        prompt = CheckstyleGenerator.preprocess_promt(
            DSL_Syntax=self.dsl_syntax,
            style="RuleSet of Google Java Style Guide",
            DSLruleset=dsl_ruleset,
            tool="Checkstyle",
            toolruleset=filtered_tool_rules,
            example=examples
        )
        if self.gpt_agent:
            if self.debugger:
                self.debugger.sub_step("3.1 Detailed Option Mapping")
            mapping_res = self.gpt_agent.get_response(prompt, model=model)
            extract_prompt = CheckstyleGenerator.extract_config_promt(mapping_res)
            if self.debugger:
                self.debugger.sub_step("3.2 Extract Mappings")
            final_mapping = self.gpt_agent.get_response(extract_prompt, model=model)
            extract_non_empty_prompt = CheckstyleGenerator.extract_non_empty_config_promt(final_mapping)
            if self.debugger:
                self.debugger.sub_step("3.3 Filter Empty Mappings")
            final_mapping = self.gpt_agent.get_response(extract_non_empty_prompt, model=model)
            if "Yes" not in final_mapping:
                return "No valid mappings found."

            if "regular expression" in final_mapping.lower():
                if self.debugger:
                    self.debugger.sub_step("3.4 Regex Value Analysis")
                set_value_answer = self.gpt_agent.get_response(
                    f'For each mapping, if it contains "regular expression", set specific regular expression of option names to match rule\n\n        {final_mapping}',
                    model=model)
                if self.debugger:
                    self.debugger.sub_step("3.5 Replace Regex Placeholder")
                answer_map_with_value = self.gpt_agent.get_response(
                    f'Based on the following Analysis, Replace "regular expression" with setting regular expression values for the following mapping. And then give new Mappings.\n'
                    f'1. Extract specific regular expression values for "regular expression" value from the following Analysis.\n'
                    f'2. Replace "regular expression" value with corresponding specific regular expression values within the following mapping.\n\n'
                    f'Analysis:\n{set_value_answer}\n\n'
                    f'Mapping:\n{final_mapping}\n        ',
                    model=model)
                extract_with_value = CheckstyleGenerator.extract_config_promt(answer_map_with_value)
                if self.debugger:
                    self.debugger.sub_step("3.6 Extract Regex-Replaced Mappings")
                final_mapping = self.gpt_agent.get_response(extract_with_value, model=model)
            return final_mapping
        return candidate_names

    # Step 4: Generate Checkstyle configuration
    def generate_config(self, dsl_ruleset, model, checkstyle_ruleset=None, output_format="text", examples=""):
        """
        Generate Checkstyle configuration
        """
        if checkstyle_ruleset is None:
            checkstyle_ruleset = self._load_default_checkstyle_rules()

        if self.gpt_agent:
            # Merge Basic Rule and Option Rule into a single concise ToolSEM rule
            if self.debugger:
                self.debugger.sub_step("4.0 Extract ToolSEM Rules")
            tool_sem_rules = self.gpt_agent.get_response(
                f'For the following mappings,before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. You only excerpt toolSEM rule consisting of Rulename, Basic rule and Option rules.\n\n'
                f'{dsl_ruleset}\n\n'
                f'Response Format: Please do not give explanation.\n'
                f'1. RuleName: ...\n'
                f'   Basic Rule: ...\n'
                f'   Option Rule: \n'
                f'     ...\n'
                f'2. ...\n'
                f'...\n',
                model=model)
            merg_prompt = CheckstyleGenerator.merge_basic_option_rules(tool_sem_rules)
            if self.debugger:
                self.debugger.sub_step("4.1 Merge Option Rules")
            merge_answer_map = self.gpt_agent.get_response(merg_prompt, model=model)
            prompt_extract_merge = CheckstyleGenerator.extract_merge_mappings_promt(
                text=merge_answer_map, answer_map=dsl_ruleset)
            if self.debugger:
                self.debugger.sub_step("4.2 Extract Merged Mappings")
            dsl_ruleset = self.gpt_agent.get_response(prompt_extract_merge, model=model)

            # 1. Validate semantic match
            prompt = CheckstyleGenerator.validation_config_superset_semantics(
                mapping=dsl_ruleset,
                tool="Checkstyle",
                style="Google Java Style",
                toolruleset=checkstyle_ruleset
            )
            if self.debugger:
                self.debugger.sub_step("4.3 Semantic Validation")
            val_response = self.gpt_agent.get_response(prompt, model=model)
            # 2. Extract correct mappings
            filter_prompt = CheckstyleGenerator.extract_correct_mapping(
                mapping=dsl_ruleset,
                correct_information=val_response
            )
            if self.debugger:
                self.debugger.sub_step("4.4 Extract Correct Mappings")
            val_mapping = self.gpt_agent.get_response(filter_prompt, model=model)
            if "Yes" not in val_mapping and "Mapping:" not in val_mapping:
                print("Warning: No valid mappings found after validation.")
                return None
            # 3. Generate XML draft
            gen_prompt = CheckstyleGenerator.gen_config_format(
                mapping=val_mapping,
                tool="Checkstyle",
                format="XML"
            )
            if self.debugger:
                self.debugger.sub_step("4.5 Generate XML Draft")
            raw_config = self.gpt_agent.get_response(gen_prompt, model=model)
            # 4. Extract clean XML
            clean_prompt = CheckstyleGenerator.extract_specific_config_promt(
                text=raw_config,
                format="XML"
            )
            if self.debugger:
                self.debugger.sub_step("4.6 Extract Clean XML")
            final_res = self.gpt_agent.get_response(clean_prompt, model=model)
            # 5. Regex extraction
            match = re.search(r"(<module.*</module>)", final_res, re.DOTALL)
            if match:
                return match.group(1)
            else:
                return final_res.replace("Configuration:", "").strip()
        else:
            final_response = {
                "dsl_ruleset": dsl_ruleset,
                "type": "checkstyle_config_generation"
            }

        return self._format_output(final_response, output_format)

    def _get_detailed_tool_rules(self, name_list_str):
        """
        Extract detailed rules (with sub-option rules) from the Checkstyle DSL library
        based on the candidate rule name list from Step 2.
        Logic is aligned with gen_eslint_config.py.
        """
        # 1. Parse the input rule name list
        if isinstance(name_list_str, list):
            candidate_names = [str(n).strip() for n in name_list_str]
        else:
            # Extract rule names from GPT output text
            # Match words composed of letters and digits
            candidate_names = re.findall(r'([a-zA-Z0-9]+)', name_list_str)

        unique_candidates = set(candidate_names)
        if not unique_candidates:
            return "No candidate rules provided."

        # 2. Load Checkstyle DSL data file
        dsl_file_path = os.path.join(current_dir, "data", "DSL_checkstyle_all.json")

        try:
            with open(dsl_file_path, 'r', encoding='utf-8') as f:
                all_dsl_data = json.load(f)
        except Exception as e:
            print(f"Error loading Checkstyle DSL data from {dsl_file_path}: {e}")
            return ""

        # 3. Iterate through the library, find matching detailed rules (Basic Rule + Option Rule)
        detailed_results = []
        found_names = set()

        for entry in all_dsl_data:
            # Entry structure: [url, rule_name, dsl_content]
            if len(entry) < 3:
                continue

            rule_name = entry[1]
            dsl_content = entry[2]

            if rule_name in unique_candidates:
                # Clean DSL content, remove redundant title
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()

                # Build the format recognized by Step 3 (Generator)
                rule_info = (
                    f"RuleName: {rule_name}\n"
                    f"{clean_dsl}"
                )
                detailed_results.append(rule_info)
                found_names.add(rule_name)

        # 4. If no matches found, return a hint so Step 3 prompt is not empty
        if not detailed_results:
            return "No matching detailed rules found in Checkstyle DSL database."

        # Use separator to aggregate, as {{toolruleset}} in Step 3 Prompt
        return "\n\n*********************\n\n".join(detailed_results)

    # Load Checkstyle rule set
    def _load_default_checkstyle_rules(self, return_raw=False):
        """
        Load the default Checkstyle rule set
        Args:
            return_raw: if True, return raw list; otherwise return formatted string
        """
        rule_file = os.path.join(current_dir, "data", "checkstyle_rules_complete.json")
        all_rules = []

        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                all_rules.extend(rules)
        except Exception as e:
            print(f"Warning: failed to load rules file {rule_file}: {e}")

        if return_raw:
            return all_rules

        # Default: return formatted string
        ruleset_text = "\n".join([
            f"RuleName: {rule.get('name', 'Unknown')}\n"
            f"Description: {rule.get('description', 'No description')}\n"
            f"Category: {rule.get('category', 'Unknown')}\n"
            for rule in all_rules
        ])
        return ruleset_text

    # Filter relevant rules by DSL keywords
    def _filter_relevant_rules(self, dsl_text, all_rules_data, top_k=30):
        """
        Filter the top_k most relevant rules from all rules based on DSL keyword matching.
        Simple keyword match implementation; can be replaced with vector retrieval.
        """
        # 1. Extract keywords from DSL (excluding common stop words)
        keywords = set(re.findall(r"[a-zA-Z]+", dsl_text))
        stop_words = {"Mandatory", "Optional", "Rule", "is", "not", "of", "in", "the", "and", "or", "if", "then",
                      "Java", "Google", "Style", "Guide", "class", "method", "field", "variable"}
        keywords = {k for k in keywords if k not in stop_words and len(k) > 2}

        scored_rules = []

        for rule in all_rules_data:
            score = 0
            rule_content = (rule.get('name', '') + " " + rule.get('description', '')).lower()

            # 2. Calculate match score
            for kw in keywords:
                if kw.lower() in rule_content:
                    score += 1

            # Prefer exact rule name matches
            if any(kw.lower() == rule.get('name', '').lower() for kw in keywords):
                score += 5

            if score > 0:
                scored_rules.append((score, rule))

        # 3. Sort and take top K
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        selected_rules = [r[1] for r in scored_rules[:top_k]]

        # Fallback: if no rules matched, return first top_k of all rules
        if not selected_rules:
            return all_rules_data[:top_k]

        return selected_rules

    # Load Checkstyle DSL rule set
    def _load_checkstyle_dsl(self):
        dsl_file = os.path.join(current_dir, "data", "DSL_checkstyle_all.json")

        try:
            with open(dsl_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            print(f"Warning: failed to load DSL rule file {dsl_file}: {e}\n")
            return ""
        formatted_rules = []
        for item in rules:
            if isinstance(item, list) and len(item) >= 3:
                rule_name = item[1]
                dsl_content = item[2]
                clean_dsl = dsl_content.replace("Final RuleSet Representation:", "").strip()
                # Format as clean text blocks, keeping only rule name and logic
                formatted_rules.append(f"RuleName: {rule_name}\n{clean_dsl}")
        dsl_rules = "\n\n".join(formatted_rules)
        return dsl_rules

    def _load_checkstyle_dsl_basic_rules(self):
        dsl_file = os.path.join(current_dir, "data", "DSL_Checkstyle_all.json")
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

    def generate_full_checkstyle_xml(self, snippet: str) -> str:
        """
        Wrap a single-rule configuration snippet into a complete Checkstyle config file.

        Args:
            snippet: XML fragment generated by LLM, e.g. <module name='ParameterNumber'>...</module>
        Returns:
            Complete XML string
        """
        # Handle invalid input
        if not snippet or not isinstance(snippet, str):
            print("=" * 60)
            print("Input is empty or invalid, returning default config.")
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

        # 1. Load rule metadata (build Name -> Parent lookup dict for efficiency)
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
            print(f"Warning: failed to read rule metadata: {e}, defaulting to TreeWalker nesting.")

        # 2. Extract all module fragments
        # Regex: match <module name='Name'> ... </module>, re.DOTALL makes . match newlines
        # group(1) is the full XML fragment, group(2) is the rule name
        try:
            module_pattern = re.compile(r"(<module\s+name=['\"](\w+)['\"].*?</module>)", re.DOTALL)
            matches = module_pattern.findall(snippet)
        except Exception as e:
            print(f"Warning: failed to extract configuration snippet: {e}\n")
            matches = None
        # If no matches, return default config
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

        checker_children = []   # Modules directly under Checker
        treewalker_children = []  # Modules under TreeWalker

        for full_xml, rule_name in matches:
            # Determine parent
            parent = rule_parent_map.get(rule_name, '')

            # If explicitly a Checker-level rule (e.g. LineLength, FileTabCharacter),
            # put under checker_children. Otherwise default to TreeWalker
            # (90% of Checkstyle rules are under TreeWalker).
            if parent.endswith('Checker'):
                is_treewalker = False
            else:
                is_treewalker = True

            # 3. Indentation helper
            def reindent_snippet(xml_str, base_indent_level):
                lines = xml_str.strip().split('\n')
                formatted_lines = []
                indent_str = "  " * base_indent_level  # 2 spaces per level

                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if i == 0:
                        # <module ...> tag
                        formatted_lines.append(f"{indent_str}{stripped}")
                    elif i == len(lines) - 1:
                        # </module> tag
                        formatted_lines.append(f"{indent_str}{stripped}")
                    else:
                        # Inner <property ...> or other content, add one more indent level
                        formatted_lines.append(f"{indent_str}  {stripped}")
                return "\n".join(formatted_lines)

            # Classify by parent and adjust indentation
            if is_treewalker:
                # TreeWalker is level 1 under Checker, so its children are level 2
                treewalker_children.append(reindent_snippet(full_xml, 2))
            else:
                # Checker direct children are level 1
                checker_children.append(reindent_snippet(full_xml, 1))

        # 4. Assemble final XML
        xml_header = """<?xml version="1.0"?>
  <!DOCTYPE module PUBLIC
    "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
    "https://checkstyle.org/dtds/configuration_1_3.dtd">

  <module name="Checker">
    <property name="charset" value="UTF-8"/>
    <property name="severity" value="warning"/>
    <property name="fileExtensions" value="java, properties, xml"/>
        """

        # Append Checker direct children (e.g. LineLength)
        body_content = ""
        if checker_children:
            body_content += "\n" + "\n".join(checker_children) + "\n"

        # Append TreeWalker and its children
        if treewalker_children:
            body_content += '\n  <module name="TreeWalker">\n'
            body_content += "\n".join(treewalker_children)
            body_content += '\n  </module>\n'

        xml_footer = "</module>"

        return xml_header + body_content + xml_footer

    def _format_output(self, content, output_format):
        """Format output"""
        if output_format == "json":
            if isinstance(content, str):
                try:
                    # Try to parse as JSON
                    return json.dumps({"response": content}, ensure_ascii=False, indent=2)
                except:
                    return json.dumps({"response": content}, ensure_ascii=False)
            else:
                return json.dumps(content, ensure_ascii=False, indent=2)
        else:
            # Text format
            if isinstance(content, dict):
                return "\n".join([f"{k}: {v}" for k, v in content.items()])
            else:
                return str(content)
