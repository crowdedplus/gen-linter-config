import os, sys, inspect, copy
import re, json
import shutil

# 将Checkstyle规则的自然语言描述解析为自定义DSL格式。使用GPT模型将Checkstyle规则转换为结构化的DSL规则。

from gen_linter_config import util,util_java
from openai import OpenAI
from retry import retry
from gen_linter_config import GPTAgent


# 构建用于将Checkstyle规则描述转换为DSL的GPT提示词
# rule=rule_description, DSL_Syntax=dsl
def preprocess_promt(rule: str, DSL_Syntax: str, style="CheckStyle Rule", grammar="Grammar", example=""):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Analyze the following {{Style}} and parse the description and options as rules using given {{grammar}}. please delete unexisted OptionName. 

1. Analyze whether each sentence of descriptions of {{Style}} is a rule or not. If the sentence is subjective or vague, do not classify it as a rule.
2. Parse each sentence that is a rule using the given {{grammar}} by understanding the complete semantics of the description, pay attention to map to suitable formal Java term and select appropriate real operator characters to make its semantics clear and correct.
3. Analyze all options (option name, option description, option data type and data value range instead of default value, the all specific values of option names is from https://checkstyle.sourceforge.io/property_types.html {{option values}}. For each option, 
4. Parse each option using the given {{grammar}} by understanding the complete semantics of the description:
    4.1 If the option's data type is a single-element enumerable data type (like boolean, enum) instead of list, array, set ..., analyze the option description to get semantics of different values, and parse all values into different rules the given {{grammar}} based on the option description.
    4.2 Otherwise, if the option's value is a set, parse the option as a single rule using the given {{grammar}} by understanding the complete semantics of the option description, with the option name enclosed in {{}}.
    4.3 For regular expression options, if option name contains "exception" or "ignore" its rule type is "Optional";  Otherwise, go to 4.4.
    4.4 Otherwise, use "Mandatory" as the rule type of regular expression options.
5. Parse a rule using the given {{grammar}} by understanding the complete semantics of the description, ensuring follow given {{grammar}}, ensuring correctness of semantics and pay attention to map to suitable formal Java term and select appropriate real operator characters.

***Note*** Generally, 'Mandatory' means rule must be satisfied, 'Optional' means rule may be satisfied or not be satisfied, or not applied the rule 
For example, exceptions or ignore XX, the rule type of rule is "Optional". 
Generally, For regular expression options, if option name contains "exception" or "ignore" its rule type is "Optional";  Otherwise, use "Mandatory" as the rule type of regular expression options.



{{Style}}:
{{Description}}

{{grammar}}:
{{Syntax}}

Response Format: 

**Analysis:**
...

**Final RuleSet Representation:**

If there is no option, you only give basic rule
    Final RuleSet Representation:
    Basic Rule:
    ...

Otherwise,
    Final RuleSet Representation:
    Basic Rule:
    ...

    Option Rule:
        if an option is finite and enumerable
        option1: datatype; value range; 
        value1: parse it as rule using given {{grammar}} by analyzing its semantics 
        valuek: 

        else 
        option1: datatype; value range; 
        parse it as rule using given {{grammar}} by analyzing its semantics

{{Example}}
'''
    # '''

    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{Description}}", rule)
    prompt = prompt.replace("{{grammar}}", grammar)
    prompt = prompt.replace("{{option values}}", util_java.options)

    return prompt


# 从GPT响应中提取“Final RuleSet Representation”部分，即DSL规则。用于后处理。
def Extract_DSL_Repr(text):
    prompt = '''Only Extract Final Ruleset Representation from the following Text. Please respond based on given Response Format.


Text:
{{Input}}

Response Format: No explanation. Remove Analysis.
Final Ruleset Representation:
...

For example, for the following Text,
**Final RuleSet Representation:**

Basic Rule:
Mandatory: [catch block] is not [empty]
Or
Optional: [catch block] is [empty] with [any comment inside]

Option Rule:

commentFormat option: Pattern; regular expression
commentFormat >>> Mandatory: [empty block] is suppressed if [first comment inside empty catch block] matches {{commentFormat}}

exceptionVariableName option: Pattern; regular expression
exceptionVariableName >>> Optional: [empty block] is suppressed if [variable name associated with exception] matches {{exceptionVariableName}}

**Analysis:**

1. **Basic Rule Analysis:**
   - The rule checks for empty catch blocks, which is a straightforward rule. The rule allows for an exception if there is any comment inside the catch block, making it optional for the block to be empty if a comment is present.

2. **Option Rule Analysis:**
   - **commentFormat Option:**
     - This option specifies a regular expression for the first comment inside an empty catch block. If the comment matches the specified format, the empty block is suppressed. This is parsed as a mandatory rule because the presence of a matching comment format directly affects whether the block is considered empty or not.

   - **exceptionVariableName Option:**
     - This option specifies a regular expression for the name of the variable associated with the exception. If the variable name matches the specified value, the empty block is suppressed. This is parsed as an optional rule because it provides an additional condition under which the empty block can be considered acceptable.

The rules and options are parsed according to the given grammar, ensuring that the semantics are clear and correctly mapped to formal Java terms. The use of "Mandatory" and "Optional" aligns with the rule's requirements and exceptions.

You should respond like,

Final RuleSet Representation:

Basic Rule:
Mandatory: [catch block] is not [empty]
Or
Optional: [catch block] is [empty] with [any comment inside]

Option Rule:
commentFormat option: Pattern; regular expression
commentFormat >>> Mandatory: [empty block] is suppressed if [first comment inside empty catch block] matches {{commentFormat}}

exceptionVariableName option: Pattern; regular expression
exceptionVariableName >>> Optional: [empty block] is suppressed if [variable name associated with exception] matches {{exceptionVariableName}}
'''
    prompt = prompt.replace("{{Input}}", text)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt

# 批量处理Checkstyle规则，调用GPT进行转换
def get_all_gpt_res_for_java_checkstyle(rule_list, dsl, examples=None, style="Google Java Style Guide", model="gpt-4o"):

    agent = GPTAgent()

    for ind, rule_description in enumerate(rule_list[:]):

        # if ind not in [3, 10,183]:#95:
        #     continue

        # if "LineLength" not in rule_description and "NoLineWrap" not in rule_description: #
        #     continue
        if "FallThrough" not in rule_description:  # LineLength JavadocMethod NoLineWrap MissingJavadocMethod AnnotationLocation
            continue
        # if "ConstructorsDeclarationGrouping" not in rule_description:#JavadocParagraph CustomImportOrder JavadocParagraph SingleLineJavadoc
        #     continue
        print(">>>>>>rule: ", ind, rule_description)

        continue
        # break
        prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
        print(">>>>>prompt: ", ind, prompt)
        answer = agent.get_response(prompt, model=model, temperature=0)
        print(">>>>>>answer: ", ind, answer)
        extract_dsl_prompt = Extract_DSL_Repr(answer)
        answer = agent.get_response(extract_dsl_prompt, model=model, temperature=0)
        print(">>>>>>final answer: ", ind, answer)

        # util.save_json(util.data_root + gpt_answer_dir, str(ind), {ind: answer})
        util.save_json(gpt_answer_dir, str(ind), {ind: answer})

        # break


if __name__ == "__main__":

    gpt_answer_dir = util.data_root + "GenDSL_Java_CheckStyle_no_except_imprv_dsl/checkstyle_DSL/"
    check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/",
                                           "checkstyle_name_completedes_options_3_process")
    rule_list = ["\n".join(["Rulename", rule_name, description, "Options", options]) if options else "\n".join(
        ["Rulename", rule_name, description]) for url, rule_name, description, options in check_style_rule_list]

    examples = '''For Example, 
For the CustomImportOrder description: 
Rulename
CustomImportOrder
Description

Checks that the groups of import declarations appear in the order specified
by the user. If there is an import but its group is not specified in the
configuration such an import should be placed at the end of the import list.
Options

customImportOrderRules, Specify ordered list of import groups., String[], {}
separateLineBetweenGroups, Force empty line separator between import groups., boolean, true
sortImportsInGroupAlphabetically, Force grouping alphabetically, in ASCII sort order., boolean, false
specialImportsRegExp, Specify RegExp for SPECIAL_IMPORTS group imports., Pattern, "^$"
standardPackageRegExp, Specify RegExp for STANDARD_JAVA_PACKAGE group imports., Pattern, "^(java|javax)\."
thirdPartyPackageRegExp, Specify RegExp for THIRD_PARTY_PACKAGE group imports., Pattern, ".*"

You respond like: 
Final RuleSet Representation:
Basic Rule:
Mandatory: Order of [import groups] is [specified by the user]
And
Mandatory: if [import] not in [specified group] then [import] at end of [import groups]

Option Rule:
separateLineBetweenGroups option: boolean; {true, false} ## value range instead of default value
true >>> Mandatory: [empty line] between [import groups]
false >>> Optional: [empty line] not between [import groups]

sortImportsInGroupAlphabetically option: boolean; {true, false}
true >>> Mandatory: Order of [imports] of [import group] is [ASCII sort order]
false >>> Optional: Order of [imports] of [import group] is not [ASCII sort order]

allowNewlineParagraph option: Control whether the <p> tag should be placed immediately before the first word; boolean; {true, false}
true >>> Mandatory: [<p>] immediately before [first word] of [paragraph]
false >>> Optional: [<p>] not immediately before [first word] of [paragraph]

Specify the RegExp for the first comment inside empty catch block. If check meets comment inside empty catch block matching specified format - empty block is suppressed. If it is multi-line comment - only its first line is analyzed.
commentFormat option: Pattern; regular expression
commentFormat >>> Mandatory: [empty block] is suppressed if [comment inside empty catch block] matches {{commentFormat}}

********************
For another Example, 
For the NeedBraces description: 
Rulename
NeedBraces
Description
Checks for braces around code blocks. Checks for empty blocks.

Options

allowEmptyLoopBody, Allow loops with empty bodies., boolean, false
allowSingleLineStatement, Allow single-line statements without braces., boolean, false
tokens, tokens to check, subset of tokens

LITERAL_DO,LITERAL_ELSE,LITERAL_FOR,LITERAL_IF,LITERAL_WHILE,LITERAL_CASE,LITERAL_DEFAULT,LAMBDA.
,
LITERAL_DO,LITERAL_ELSE,LITERAL_FOR,LITERAL_IF,LITERAL_WHILE.

You respond like: 

Final RuleSet Representation:
Mandatory: [block] have [Brace]
;
Mandatory: No [EmptyBlock]

Option Rule:
allowEmptyLoopBody option: boolean; {true, false} (option name: data type; value range)
    false >>> Mandatory: [body] of [loop statement] is not [Null] (different values of option name: different option rules)
    true >>> Optional: [body] of [loop statement] is [Null]

allowSingleLineStatement option: boolean; {true, false}
    false >>> Mandatory: if Number of [statement] of [body] is 1 then [body] have [Brace]
    true >>> Optional: if Number of [statement] of [body] is 1 then [body] not have [Brace]

Specify pattern for lines to ignore.    
ignorePattern option: Pattern; regular expression;
    ignorePattern >>> Optional: [LineLength] not for {{ignorePattern}} 

tokens option: String[]; {LITERAL_DO, LITERAL_ELSE, LITERAL_FOR, LITERAL_IF, LITERAL_WHILE, LITERAL_CASE, LITERAL_DEFAULT,LAMBDA};
    tokens >>> Mandatory: Check block of {{tokens}}

For another Example, 
For the SingleLineJavadoc description: 
Rulename
SingleLineJavadoc
Description
Checks that a Javadoc block can fit in a single-line and doesn't contain block tags. Javadoc comment that contains at least one block tag should be formatted in a few lines.

You respond like: 

Final RuleSet Representation:
Optional: [Javadoc block] fit in [single-line] 
And 
No [block tags] in [Javadoc block]
; 
Mandatory: if [Javadoc comment] have [block tag] then [Javadoc comment] formatted in [few lines]
'''  # ignorePattern option: Pattern; regular expression;
    # ignorePattern >>> Optional: [block] have [Brace] Except {{ignorePattern}}
    # examples=''

    dsl = util_java.dsl
    # get_all_gpt_res_for_java_checkstyle(rule_list,dsl,  examples=examples,style="CheckStyle Rule",model="gpt-4o-2024-08-06")

    complete_info_checkstyle_to_dsl = []
    for ind in range(len(os.listdir(gpt_answer_dir))):
        gpt_dsl_rule_list = util.load_json(gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        text = gpt_dsl_rule_list[str(ind)]

        ruleone = copy.deepcopy(check_style_rule_list[ind])
        # if "NonEmptyAtclauseDescription" in ruleone[1]:
        #     print(text)
        if "fallthru" in text:
            print(">>>>>>: ",ind, check_style_rule_list[ind][:3],text)
        # ruleone.insert(3, gpt_dsl_rule_list_original_answer[str(ind)])
        ruleone.insert(4, text)
        # print(">>>: ", check_style_rule_list[ind][:2] + [text])
        complete_info_checkstyle_to_dsl.append(check_style_rule_list[ind][:2] + [text])
        # rule_list_add_gpt_result.append(ruleone)
        # rule_list_add_gpt_result[ind+1].insert
    # util.save_json(util.data_root + "GenDSL_Java_CheckStyle_no_except_imprv_dsl/", "DSL_checkstyle_all",
    #                complete_info_checkstyle_to_dsl)
    # all_checkstyle_dsls = util.load_json(util.data_root + dir_name, "DSL_checkstyle_all")
