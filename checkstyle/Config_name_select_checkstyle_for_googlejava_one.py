import copy
import os, json, sys,inspect
import re
import shutil
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandparentdir= os.path.dirname(parentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, grandparentdir)
import util
import util_java
from openai import OpenAI
from retry import retry
from gpt_wrapper import GPTAgent


def preprocess_promt(DSL_Syntax: str, style="RuleSet of Google Java Style Guide", DSLruleset=None, tool = "Checkstyle",toolruleset=None,grammar="Grammar", example=""):

    prompt = '''Select the corresponding possible RuleNames from {{tool}} for each DSL rule from {{Style}}.
Each rule representation from {{Style}} splited by ";", "And", "Or"

{{Style}}:
{{DSLruleset}}

{{tool}}:
{{toolruleset}}

Response Format:
Mapping of {{Style}} to {{tool}}:
first rule representation from {{Style}} : if exists, only give corresponding RuleName of {{tool}} as a list. otherwise, gives None
second rule representation from {{Style}} : ...
...

{{Example}}
'''

    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{DSLruleset}}", DSLruleset)
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt

# 批量处理Google Java风格规则，获取GPT的映射结果
def get_all_gpt_res_for_java_checkstyle(rule_list,DSL_Syntax=None, example="", model="gpt-4o"):

    agent = GPTAgent()

    for ind, rule_description in enumerate(rule_list[:]):
        # if ind < 50:
        #     continue
        # if ind in [63]:  #13,20,25,28,64 1 25 68 22 24, 37,52,56,,68 ,60 23,52, 37, 56, 33, 8,14,23, 14,34 55,57,70
        #         continue

        print(">>>>>>rule: ", rule_description)
        if rule_description:
            # break
            prompt = preprocess_promt(DSL_Syntax=DSL_Syntax, style="RuleSet of Google Java Style Guide", DSLruleset=rule_description,
                                 tool="Checkstyle", toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=example)

            # prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
            print(">>>>>prompt: ", prompt)
            answer = agent.get_response(prompt, model=model)
            print(">>>>>>answer: ", ind, answer)
        else:
            answer=""
        # util.save_json(util.data_root + gpt_answer_dir, str(ind), {ind: answer})
        util.save_json(gpt_answer_dir, str(ind), {ind: answer})
        # break
        # break


# 从Checkstyle规则描述中提取"Basic Rule"部分
def extract_basic_rule(tex):
    # print(">>>>a checkstyle rule: ",tex)
    if "Basic Rule" in tex:
        ind = tex.index("Basic Rule") if "Basic Rule" in tex else tex.index("plaintext")
        pre = tex[ind:].strip()
    else:
        # print(">>>>tex: ",tex)
        pre = tex.split("plaintext")[1] if "plaintext" in tex else tex
        pre = "Basic Rule: " + pre
    # print("pre: ",pre)
    basic_rule = []
    for e in pre.split("\n"):
        # print(">>e: ",e)
        if e:
            basic_rule.append(e)
        else:
            break
    # print(">>>>","\n".join(basic_rule))
    return "\n".join(basic_rule)

# 从JSON文件中加载Google Java风格的DSL规则。预处理规则文本（如提取“Description”部分），并返回规则列表。
def get_all_javastyle_dsl_json_file(gpt_preprocess_answer_dir_standard_example,file_name):
    gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example,file_name)

    google_java_dsl_rules = []

    def preprocess_javastyle_dsl(text):
        # print(">>>javastyle text: ",text)
        if "Description is:" in text:
            ind = text.index("Description is:")
            return text[ind + len("Description is:"):].strip()
        if "Description:" in text:
            ind = text.index("Description:")
            return text[ind + len("Description:"):].strip()
        return text
    # print(">>>>>gpt_preprocess_answer_dir_standard_example: ",gpt_preprocess_answer_dir_standard_example,len(os.listdir(gpt_preprocess_answer_dir_standard_example)))
    # check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/","checkstyle_name_completedes_options_3_process")
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    for ind,(url,rule_name,text) in enumerate(gpt_dsl_rule_list):

        # text = gpt_dsl_rule_list[w[:-5]]
        # print(">>>>>JavaStyle: ", text)
        checkstype_dsl = preprocess_javastyle_dsl(text)
        # if "NO RULE"
        # print(">>>>>checkstype_dsl: ", checkstype_dsl)
        if "Mandatory" not in checkstype_dsl and "Optional" not in checkstype_dsl:#"NO RULE" in checkstype_dsl:
            google_java_dsl_rules.append([url, rule_name, ""])
            continue
        google_java_dsl_rules.append([url,rule_name,checkstype_dsl])
        # '''
    return google_java_dsl_rules


import tiktoken
def count_token(tex):
    # tiktok.get_encoding
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    # encoding = tiktoken.encoding_for_model("gpt-3.5turbo")
    num_tokens = len(encoding.encode(tex))
    print("num_tokens: ",num_tokens)


# 加载Check style和Google Java style的DSL表达，并构建示例，然后批量映射
if __name__ == "__main__":
    # util.save_json(util.data_root+"GenDSL_Java_CheckStyle_no_except/","javastyle_url_rulename_dsl_one_review", complete_info_checkstyle_to_dsl)

    dir_name="GenDSL_Java_CheckStyle_no_except_imprv_dsl/"#"GenDSL_Java_CheckStyle_no_except/"
    all_checkstyle_dsls = util.load_json(util.data_root + dir_name, "DSL_checkstyle_all")
    checkstyle_dsl_basic_rules="\n".join(["RuleName: "+rulename+"\n"+extract_basic_rule(tex) for url,rulename,tex in all_checkstyle_dsls])
    print("len checkstyle_dsl_basic_rules: ",len(checkstyle_dsl_basic_rules))

    # for e in checkstyle_dsl_basic_rules:
    #     print(e)
    # count_token(checkstyle_dsl_basic_rules)

    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    javastyle_dsls_results= get_all_javastyle_dsl_json_file(util.data_root + dir_name, "javastyle_url_rulename_dsl_one_review")
    javastyle_dsls = [dsl for *r,dsl in javastyle_dsls_results]    # break
    print("len javastyle_dsls: ",len(javastyle_dsls))

    examples = '''For Example, for the following RuleSet of Google Java Style Guide
Final RuleSet Representation:
Mandatory: [BlankLine] have [AlignedLeadingAsterisk] between [Paragraphs]
And
Mandatory: if [BlockTags] is [Present] then [BlankLine] have [AlignedLeadingAsterisk] before [BlockTags]
;
Mandatory: [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
;
Mandatory: [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] is [Null] —> [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]

You should respond like:
Mapping of {{Style}} to {{tool}}:
"Mandatory: [BlankLine] have [AlignedLeadingAsterisk] between [Paragraphs]  : ['XXXX'],
"Mandatory: if [BlockTags] is [Present] then [BlankLine] have [AlignedLeadingAsterisk] before [BlockTags]" : ["RequireEmptyLineBeforeBlockTagGroup","JavadocMissingLeadingAsterisk","JavadocParagraph"],
"Mandatory: [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]" : ["NeedBraces"],
"Mandatory: [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] is [Null] —> [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]" : []
'''

    gpt_answer_dir = util.data_root + dir_name+"Config_name_select_googlejava_to_checkstyle_one_review/"

    get_all_gpt_res_for_java_checkstyle(javastyle_dsls,DSL_Syntax=util_java.dsl, example=examples, model="gpt-4o")

