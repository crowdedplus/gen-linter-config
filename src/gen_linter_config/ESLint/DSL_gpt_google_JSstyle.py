import os,json,sys
import re
import shutil
import inspect

import copy
from gen_linter_config import util

from openai import OpenAI
from retry import retry
from gen_linter_config import GPTAgent
# rule=rule_description, DSL_Syntax=dsl
def preprocess_promt(rule: str, DSL_Syntax: str, style="Google Java Style Guide",grammar="Grammar",example="",PL="JavaScript"):
    #then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    #2. Please revise the rule by replacing vague reference words with specific and clear Java terminology. 这种问题,不是很容易解决的，如each section
    prompt = '''Analyze the following {{Style}} based on the following steps. For each sentence, please independently analyze using step 0-6. 

0. Remove code examples from the following {{Style}}.
1. Analyze all Java objects or terminology of the descriptions.
2. A sentence may have multiple rules, Do not ignore any Java objects or numbers related rule for each rule!
3. Analyze each rule and then classify each rule as mandatory or optional. If the sentence is Subjective, Ambiguous and code examples, do not classify it as a rule.
4. Parse each rule using given {{grammar}} by understanding the semantics of the description. Pay attention to map to appropriate Java terms and operator characters to make its semantics clear and correct. 
5. Check if parsed rule miss any Java objects of description. If yes, please improve it.
6. Give the Final RuleSet Representation. 
 
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
    #    For each sentence, please independently analyze using step 0-8. Do not miss analyzing the sentence that is like a title starting with 1.1, ..., 6.2.

    prompt='''Analyze the following {{Style}} based on the following steps. 
For each sentence, please independently analyze using step 0-8. Do not miss analyzing the sentence that is like a title starting with 1.1, ..., 6.2.

0. Remove code examples from the following {{Style}}.
1. Analyze all {{PL}} objects or terminology of the descriptions. Clearly identify ambiguous references such as "these" and replace them with explicit objects. 
2. Determine if the sentence implies multiple rules, if its description is ambiguous related to human or represents code, do not classify it as a rule.
3. If description has definitive terms (e.g., "must," "shall", "require", "should usually" ), classify the rule as "Mandatory"; If description uncertain terms ( e.g., "maybe" "might" ), classify the rule as "Optional".
4. Analyze each rule to determine appropriate constraint type.
5. Explain meaning of each rule to make its semantics complete, clear and no lacking scope that rule checks.
6. Parse the rules' meaning using given {{grammar}}. Pay attention to determine appropriate {{PL}} terms and operators to make its semantics clear and correct. 
7. Check if parsed rule miss any {{PL}} objects of description. If yes, please improve it. ensuring each rule is semantically complete and clear! 
8. Give the Final RuleSet Representation using given {{grammar}}. 

***Note*** Generally, 'Mandatory' means rule must be satisfied, 'Optional' means rule may be satisfied or not be satisfied, or not applied the rule 
For example, exceptions or a rule not applied to XXX, the rule type is "Optional". 



In the process, do not miss any steps for each sentence!

{{Style}}:

{{Description}}

{{grammar}}:
{{Syntax}}

Response Format:
Give analysis.

Final RuleSet Representation:
...

{{Example}}'''
    # '''
    prompt = prompt.replace("{{PL}}", PL)
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
def Extract_DSL_Repr(text):
    prompt='''Only Extract Final Ruleset Representation from given analyze text. Please respond based on given Response Format.
    
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
def Review_prompt(rule: str, dsl_rep_list:str, DSL_Syntax: str, style="Google Java Style Guide",grammar="Grammar",example=""):
    prompt='''Analyze the following {{Style}} and each rule of ##References## to make more accurate, complete and clear Final RuleSet Representation using given {{grammar}} that fully captures all rules of the {{Style}} description by checking: 

1. Verify that each rule type (Optional, Mandatory) aligns with the {{Style}}.
2. Improve that operators and JavaTerms in each rule accurately, completely and clearly represent the {{Style}}.
3. Identify if there are missing rules specified in the {{Style}} description, and add it as rules.
4. Note give the final RuleSet representation based on given grammar

{{Style}}:
{{Description}}

References:
{{ReferenceRuleSet1}}

{{grammar}}:
{{Syntax}}

{{Example}}'''
    prompt = prompt.replace("{{Description}}", rule)
    prompt = prompt.replace(" (", " ")
    prompt = prompt.replace("(", " ")
    prompt = prompt.replace(") ", ", ")
    prompt = prompt.replace(").", ".")
    prompt = prompt.replace(": ", " is ")
    prompt = prompt.replace("{{ReferenceRuleSet1}}", dsl_rep_list[0])
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)
    prompt = prompt.replace("{{Example}}", example)

    return prompt
#     answer = util.load_json(parent_dir + "google_java_dsl_preprocess/", str(ind))[str(ind)]
#     prompt = f'''For the following Style, check whether lacking sentences that are not parsed as rules among the following rules.
#
# rules:
# {answer}
#
# Style:
# {rule_description}
#
# Grammar:
# {util_java.dsl}
#         '''
#     print(">>>>>>check prompt: ", ind, prompt)
#     agent = GPTAgent()
#     answer = agent.get_response(prompt, model=model)
#
#     print(">>>>>>check answer: ", ind, answer)
def get_all_gpt_res_for_java_checkstyle(rule_list,dsl, examples=None,style="Google Java Style Guide",model="gpt-4o",temperature=0):
    '''
    1. parse each rule of style guide as a string
    2. parse all rules of style tool as a string
    3. get and save GPT results
    '''

    agent = GPTAgent()

    # rule_list = util.load_json(util.data_root +"rule/google_java_style/","google_java_style")

    # all_rules = util.load_csv(data_dir + "javaguide_refine.csv")
    # all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/googlejavastyle 2.csv")

    # html
    '''
    GPT results_rule_name_descr_options
    GPT results_rule_name_descr	
    GPT results_html
    '''
    # util.save_json(util.data_root + "style_tool_rules/", "checkstyle_name_des_options", all_checkstyle_details)

    # check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/", "checkstyle_name_des_options_process_control_length")
    # check_style_rule_list = ["\n".join(["Rulename", rule_name, description, options]) if options else "\n".join(
    #     ["Rulename", rule_name, description]) for url, rule_name, description, options in check_style_rule_list]
    # checkstyle_str = "\n".join(check_style_rule_list)
    # print(">>>>checkstyle_str: ",checkstyle_str)
    # util.save_json(util.data_root + "style_tool_rules/", "checkstyle_name_des_options", all_checkstyle_details)
    # print(">>>all_rules: ", len(all_rules))
    # for ind,each in enumerate(examples):
    #     examples[ind][0] = preprocess_promt(rule=each[0], DSL_Syntax=dsl, style=style)

    for ind, rule_description in enumerate(rule_list[:]):
        # if ind >10:
        #     continue
        if ind not in [131]:#133 82 106 82 72 51,26 87 88 28 87 6642 41 12 7,22 26 55
            continue
        # if ind in [3,6,8,40,47]:#3, 6,8,40, ,47 , 6,8,40,47
        #     continue
        # if ind not in [2,4,68]:#37 3, 6,8,40, 55,59 57 23 47 23
        #     continue
        # if ind<15:
        #     continue
        # if "7.1.3 Block tags" not in rule_description:
        #     continue
        # if "Use of optional braces" not in rule_description:
        #     continue
        # if ind not in [6]:
        #     continue
        # if ind  in [4]:#14
        #     continue
        # if ind not in [55,57]:#,43 ,8,43 [6,8]:  #65 42 8 19 23 57 1 25 68 22 24, 37,52,56,,68 ,60 23,52, 37, 56, 33, 8,14,23, 14,34 55,57,70
        #         continue
        # if ind >=15:
        #     continue
        #     break
        # rule_description = "\n".join([rule_name, description])
        # print("")
        print(">>>>>>rule: ", ind, rule_description)
        # continue

        prompt= preprocess_promt(rule=rule_description,example=examples,DSL_Syntax=dsl, style=style)
        print(">>>>>prompt: ",prompt)
        dsl_answer_list = []
        for i in range(1):
            # answer = agent.get_response(prompt, model='o1-mini')#,temperature=0.2

            answer = agent.get_response(prompt, model=model,temperature=0.2)#,temperature=0.2
            print(">>>>>>answer: ", ind,answer)
            extract_dsl_prompt=Extract_DSL_Repr(answer)
            dsl_answer = agent.get_response(extract_dsl_prompt, model=model,temperature=0)
            dsl_answer_list.append(dsl_answer)
            # if "Final RuleSet Representation:" in answer:
            #     answer=answer[answer.index("Final RuleSet Representation:"):]
            #     if "```" in answer:
            #         answer = answer[:answer.index("```")]
        # review_prompt= Review_prompt(rule=rule_description,dsl_rep_list=dsl_answer_list,example=examples,DSL_Syntax=dsl, style=style)
        # print(">>>>>Reviewed prompt: ",review_prompt)
        # answer = agent.get_response(review_prompt, model=model, temperature=0.7)
        # print(">>>>>>Reviewed answer: ", ind, answer)
        answer=dsl_answer_list[0]
        # continue
        # extract_dsl_prompt = Extract_DSL_Repr(answer)
        # answer = agent.get_response(extract_dsl_prompt, model=model)

        # util.save_json(util.data_root + gpt_answer_dir, str(ind), {ind: answer})
        util.save_json(gpt_answer_dir, str(ind), {ind: answer})

        # break

if __name__ == "__main__":
    gpt_answer_dir=util.data_root + "GenDSL_JS_ESLint_no_except_new/GleJS_DSL_new/"

    # all_rules = util.load_csv(util.data_root + "benchmark/benchmark_javascript/google_js_rules_new2.csv")
    all_rules = util.load_csv(util.data_root + "benchmark/benchmark_javascript/google2eslint_js_benchmark_v6.csv")

    rule_list = ["\n".join([rule_name, description]) for ind, (rule_html, rule_name, description, *remain) in
                 enumerate(all_rules) if ind > 0]

    examples='''For Example, Analyze the following {{Style}}, please parse the style using the given {{grammar}}. 

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
'''

    examples = '''For Example, Analyze the following {{Style}}, please parse the style using the given {{grammar}}. 

{{Style}}:
Do not `goog.require` another ES module.
`exportfrom` statements must not be line wrapped and are therefore an exception to the 80-column limit. 
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
Mandatory: No [goog.require] for another [ES module]
;
Mandatory: No [LineWrap] for [exportfrom Statement]
;
Optional: [80 ColumnLimit] not for [exportfrom Statement]
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
Mandatory: No [EmptyDescription] for [@param, @return, @throws, @deprecated]
'''

    import util_js
    dsl = util_js.dsl

    get_all_gpt_res_for_java_checkstyle(rule_list, dsl, examples=examples,style="Google JavaScript Style Guide",model="gpt-4o-2024-08-06")#gpt-4o o1-preview ,temperature=1

    complete_info_checkstyle_to_dsl=[]
    file_num=len(os.listdir(gpt_answer_dir))
    print(">>>file_num: ", file_num, gpt_answer_dir)
    file_num=149
    for ind in range(file_num):
        print(">>>ind: ",ind)
        gpt_dsl_rule_list = util.load_json(gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        text =gpt_dsl_rule_list[str(ind)]
        # print(text)
        ruleone=copy.deepcopy(all_rules[ind + 1])
        ruleone.insert(3, gpt_dsl_rule_list_original_answer[str(ind)])
        ruleone.insert(3, text)
        complete_info_checkstyle_to_dsl.append(all_rules[ind + 1][:2]+[text])
        # if ind ==13:
        #     print(text)
        # rule_list_add_gpt_result.append(ruleone)
        # rule_list_add_gpt_result[ind+1].insert
    print("len: ",len(complete_info_checkstyle_to_dsl))
    util.save_json(util.data_root+"GenDSL_JS_ESLint_no_except_new/","javascriptstyle_url_rulename_dsl", complete_info_checkstyle_to_dsl)



    '''
    data_dir = util.data_root + "rule/google/"

    all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/googlejavastyle.csv")
    gpt_answer_dir=util.data_root + "gpt_dsl_answer/GoogleJavaStyle_DSL/"
    '''
    '''
    csv_results=[]
    for index in range(len(os.listdir(gpt_answer_dir))):
    # for file_name in os.listdir(gpt_answer_dir):
    #     ind=file_name[:-5]
        ind=str(index)
        csv_results.append(all_rules[int(ind)])

        rule_dict = util.load_json(gpt_answer_dir,ind)
        answer_list=rule_dict[ind]
        if 1:
        # try:
        #     json_object = json.loads(answer_list)
            csv_results[-1].insert(3,answer_list)
            # print(answer_list)
            # print(">>>>>>: ", json_object)
            # y_or_n = json_object['Answer']
            # csv_results[-1].append(y_or_n)
            # configuration_list = json_object['Configuration']
            # csv_results[-1].append("\n******\n".join(configuration_list))
        # except:
        #     print(">>>>>>>exception")
        #     if "'Answer': 'Yes'" in answer_list:
        #         config=answer_list.split("'Configuration': [")[-1]
        #         config=config.split("']'")[0]
        #         config_str="\n******\n".join(["<module"+each_config for each_config in config.split("<module") ])
        #         csv_results[-1].append('Yes')
        #         csv_results[-1].append(config_str)
        #         # for each_config in config.split("<module"):
        #         #     new_config="<module"+each_config
        #         # print(">>>>config:",config.split("<module"))
        #         # json_object = json.loads(config)
        #     elif '"Answer": "Yes"' in answer_list:
        #         config = answer_list.split('"Configuration": [')[-1]
        #         config=config.split('"]"')[0]
        #         config_str = "\n******\n".join(["<module" + each_config for each_config in config.split("<module")])
        #         csv_results[-1].append('Yes')
        #         csv_results[-1].append(config_str)
        #         print(">>>>config:", config.split("<module"))
        #         # json_object = json.loads(config)
        #     else:
        #         csv_results[-1].append('No')

        # for config in configuration_list:
        #     print(">>>config: ",config)
        #     csv_results[-1].append("******\n".join(configuration_list))

        # for e_asw in answer_list:
        #     print(">>>e_asw: ",e_asw)
        # break

    util.save_csv(util.data_root + "gpt_direct_answer/csv/gpt_answergooglejavastyle_checkstyle_nocheckstyleRule_example8.csv",csv_results,["url","rule_name","description","gpt_answer","gpt_configuration"])
    '''
    '''>>>>>>answer:  4 To analyze the given Google Java Style Guide section and parse it using the provided grammar, let's break down each sentence and apply the rules accordingly.

### Google Java Style Guide Section:
3 Source file structure
- A source file consists of, in order:
  - License or copyright information, if present
  - Package statement
  - Import statements
  - Exactly one top-level class
- Exactly one blank line separates each section that is present.

### Analysis and Parsing:

1. **Sentence: "A source file consists of, in order:"**
   - This sentence introduces a list of elements that must appear in a specific order. It implies a mandatory rule about the structure of a source file.

2. **Sentence: "License or copyright information, if present"**
   - This is an optional element, as indicated by "if present." It is not mandatory for every source file.

3. **Sentence: "Package statement"**
   - This is a mandatory element in a Java source file.

4. **Sentence: "Import statements"**
   - This is a mandatory element, though the number of import statements can vary.

5. **Sentence: "Exactly one top-level class"**
   - This is a mandatory rule specifying that there must be exactly one top-level class in the source file.

6. **Sentence: "Exactly one blank line separates each section that is present."**
   - This is a mandatory rule about formatting, specifying that sections must be separated by exactly one blank line.

### Final RuleSet Representation:

```plaintext
Mandatory: Order of [LicenseOrCopyrightInformation], [PackageStatement], [ImportStatements], [TopLevelClass] is [LicenseOrCopyrightInformation], [PackageStatement], [ImportStatements], [TopLevelClass]
And
Optional: [LicenseOrCopyrightInformation] is [Present]
;
Mandatory: Number of [TopLevelClass] = 1
;
Mandatory: Number of [BlankLine] between [Section] = 1
```

### Explanation:
- **Order Rule**: The order of elements in a source file is specified, with the license or copyright information being optional.
- **Top-Level Class Rule**: There must be exactly one top-level class in the source file.
- **Blank Line Rule**: There must be exactly one blank line separating each section that is present.

This representation captures the mandatory and optional nature of the rules, as well as the specific order and formatting requirements outlined in the style guide.
    '''