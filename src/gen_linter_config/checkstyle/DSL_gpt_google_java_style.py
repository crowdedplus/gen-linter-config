import os, json, sys
import re
import shutil
import inspect

# 转换Google的Java规则为DSL。
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandparentdir = os.path.dirname(parentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, grandparentdir)
import util, copy

from openai import OpenAI
from retry import retry
from gpt_wrapper import GPTAgent


#  构建用于将Google Java风格描述转换为DSL的GPT提示词
# rule=rule_description, DSL_Syntax=dsl
def preprocess_promt(rule: str, DSL_Syntax: str, style="Google Java Style Guide", grammar="Grammar", example=""):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    # 2. Please revise the rule by replacing vague reference words with specific and clear Java terminology. 这种问题,不是很容易解决的，如each section
    prompt = '''Analyze the following {{Style}} based on the following steps. For each sentence, please independently analyze using step 0-6. Do not miss analyzing the sentence that is like a title starting with 1.1, ..., 6.2.

1. Analyze all Java objects or terminology of the descriptions. Clearly identify ambiguous references such as "these" and replace them with explicit objects. 
2. A sentence may have multiple rules, making each rule is semantically complete, clear and no lacking scope that rule checks! 
3. Analyze each rule and then classify each rule as mandatory or optional. If the sentence is Subjective, Ambiguous and examples, do not classify it as a rule.
4. Parse each rule using given {{grammar}} by understanding the semantics of the description. Pay attention to map to appropriate Java terms and operator characters to make its semantics clear and correct. 
5. Check if parsed rule miss any Java objects of description. If yes, please improve it. ensuring each rule is semantically complete and clear! 
6. Give the Final RuleSet Representation using given {{grammar}}. 

***Note*** Generally, 'Mandatory' means rule must be satisfied, 'Optional' means rule may be satisfied or not be satisfied, or not applied the rule 
For example, exceptions or a rule not applied to XXX, the rule type is "Optional". 



In the process, do not miss any steps for each sentence!

{{Style}}:

{{Description}}

{{grammar}}:
{{Syntax}}

Response Format:
Final RuleSet Representation:
...

{{Example}}'''
    # '''
    prompt = prompt.replace("{{Description}}", rule)
    prompt = prompt.replace(" (", " ")
    prompt = prompt.replace("(", " ")
    prompt = prompt.replace(") ", ", ")
    prompt = prompt.replace(").", ".")
    prompt = prompt.replace(": ", " is ")
    # prompt = prompt.replace(", ", " ")
    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


# 从GPT响应中提取“Final RuleSet Representation”部分，即DSL规则。用于后处理。
def Extract_DSL_Repr(text):
    prompt = '''Only Extract Final Ruleset Representation from given analyze text. Please respond based on given Response Format.

Text:
{{Input}}

Response Format: 
Final Ruleset Representation:
...
'''
    prompt = prompt.replace("{{Input}}", text)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


# 批量处理Google Java风格规则，调用GPT进行转换为DSL，并保存结果。
def get_all_gpt_res_for_java_checkstyle(rule_list, dsl, examples=None, style="Google Java Style Guide", model="gpt-4o",
                                        temperature=0):
    '''
    1. parse each rule of style guide as a string
    2. parse all rules of style tool as a string
    3. get and save GPT results
    '''

    agent = GPTAgent()

    for ind, rule_description in enumerate(rule_list[:]):

        if ind not in [27]:#11,6,7
            continue
        # if ind >=15:
        #     continue
        #     break
        # rule_description = "\n".join([rule_name, description])
        # print("")
        print(">>>>>>rule: ", ind, rule_description)
        # continue
        if "terminology note" in rule_description.lower():
            print(">>>>ind terminology: ", ind)
            util.save_json(gpt_answer_dir, str(ind), {ind: ""})
            continue
        # continue
        prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
        print(">>>>>prompt: ", prompt)
        dsl_answer_list = []
        for i in range(1):
            answer = agent.get_response(prompt, model=model, temperature=0.2)
            print(">>>>>>answer: ", ind, answer)
            extract_dsl_prompt = Extract_DSL_Repr(answer)
            dsl_answer = agent.get_response(extract_dsl_prompt, model=model, temperature=0)
            dsl_answer_list.append(dsl_answer)
            # if "Final RuleSet Representation:" in answer:
            #     answer=answer[answer.index("Final RuleSet Representation:"):]
            #     if "```" in answer:
            #         answer = answer[:answer.index("```")]

        answer = dsl_answer_list[0]

        util.save_json(gpt_answer_dir, str(ind), {ind: answer})



if __name__ == "__main__":
    gpt_answer_dir = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example8/"
    gpt_answer_dir = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example8/"
    parent_dir = util.data_root + "gpt_dsl_answer_gleJava_CheckStyle_many_steps4/"
    gpt_answer_dir = util.data_root + "GenDSL_Java_CheckStyle_no_except_imprv_dsl/google_java_dsl_one_review/"

    all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze.csv")
    rule_list = ["\n".join([rule_name, description]) for ind, (url, rule_name, description, *remain) in
                 enumerate(all_rules) if ind > 0]

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

    import util_java

    # get_all_gpt_res_for_java_checkstyle(rule_list,util_java.dsl,  examples=examples,style="Google Java Style Guide",model="gpt-4o",temperature=0)#gpt-4o o1-preview ,temperature=1

    complete_info_checkstyle_to_dsl = []
    file_num = len(os.listdir(gpt_answer_dir))
    for ind in range(file_num):
        gpt_dsl_rule_list = util.load_json(gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        text = gpt_dsl_rule_list[str(ind)]
        # if ind ==3:
        print(">>>>>: ",ind, text)
        ruleone = copy.deepcopy(all_rules[ind + 1])
        ruleone.insert(3, gpt_dsl_rule_list_original_answer[str(ind)])
        ruleone.insert(3, text)
        complete_info_checkstyle_to_dsl.append(all_rules[ind + 1][:2] + [text])
        # if ind == 3:
        #     print(text)
        # rule_list_add_gpt_result.append(ruleone)
        # rule_list_add_gpt_result[ind+1].insert
    print("len: ", len(complete_info_checkstyle_to_dsl))
    # util.save_json(util.data_root + "GenDSL_Java_CheckStyle_no_except_imprv_dsl/", "javastyle_url_rulename_dsl_one_review",
    #                complete_info_checkstyle_to_dsl)
