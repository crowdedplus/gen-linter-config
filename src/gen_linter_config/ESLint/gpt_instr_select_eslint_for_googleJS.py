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
import util_js
from openai import OpenAI
from retry import retry
from gpt_wrapper import GPTAgent



# rule=rule_description, DSL_Syntax=dsl
def preprocess_promt(DSL_Syntax: str, style="RuleSet of Google Java Style Guide", DSLruleset=None, tool = "Checkstyle",toolruleset=None,grammar="Grammar", example=""):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    #Given {{Style}}, select the corresponding rules from {{tool}}.
    prompt = '''Select the possible corresponding RuleNames from {{tool}} for each DSL rule from {{Style}}. There may have several possible corresponding RuleNames for a DSL rule from {{Style}}. Think step by step for each DSL rule from {{Style}}.

{{Style}}:
{{DSLruleset}}

************
{{tool}}:
{{toolruleset}}

************
{{grammar}}:
{{Syntax}}

************
Response Format:  Give analysis process.
Mapping of {{Style}} to {{tool}}:
first rule representation from {{Style}} : if exists, only give possible RuleNames of {{tool}} as a list: [corresponding RuleName1, ..., RuleNamek ]. Otherwise, gives None
second rule representation from {{Style}} : ...
...

************
{{Example}}
'''
    # '''

    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{DSLruleset}}", DSLruleset)
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def get_all_gpt_res_for_java_checkstyle(rule_list,DSL_Syntax=None, style="RuleSet of Google Java Style Guide",tool="Checkstyle",
                                        toolruleset=None, grammar="Grammar", example="", model="gpt-4o"):

    '''
    1. parse each rule of style guide as a string
    2. parse all rules of style tool as a string
    3. get and save GPT results
    '''

    agent = GPTAgent()

    # rule_list = util.load_json(util.data_root +"rule/google_java_style/","google_java_style")
    data_dir = util.data_root + "rule/google/"

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
    # checkstyle_str = "\n".join(check_style_rule_list)

    for ind, rule_description in enumerate(rule_list[:]):#new-cap prefer-promise-reject-errors 100
        # if ind not in [58]:#2 8 14 26 51 54[32, 45, 48, 67, 74,  100, 114, 119, 120, 121, 122, 126, 127, 128, 133, 174]:#51,  86, 133,140, , 175
        #     continue
        # if "[LocalVariableDeclaration] have [SingleVariable]" not in rule_description:
        #     continue
        # if ind in [5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48,50,58,64,72,75]:#[40,50,58,75]:#[5,7,8,11,16,19,23,27,29,32,33,36,39,42,45,47,48,64,72]:#[5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48,50,58,64,72,75]:#[50,58,64,72,75]:#58 5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48  5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48,
        #     continue
        # if ind not in [41]:  # [40,50,58,75]:#[5,7,8,11,16,19,23,27,29,32,33,36,39,42,45,47,48,64,72]:#[5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48,50,58,64,72,75]:#[50,58,64,72,75]:#58 5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48  5,7,8,11,16,19,23,27,29,32,33,36,39,40,42,45,47,48,
        #     continue
        # if ind < 50:
        #     continue
        # if ind not in [64]:
        #     continue
        #     break
        # rule_description = "\n".join([rule_name, description])
        # print("")
        print(">>>>>>rule: ", rule_description)
        if rule_description:
            # break
            prompt = preprocess_promt(DSL_Syntax=dsl, style=style, DSLruleset=rule_description,
                                 tool=tool, toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=example)

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

def preprocess_checkstyle_dsl(gpt_preprocess_answer_dir_standard_example):
    checkstyle_rules = []
    for ind in range(len(os.listdir(gpt_preprocess_answer_dir_standard_example))):
        gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        text = gpt_dsl_rule_list[str(ind)]

        def extract_basic_rule(tex):
            # print(">>>>a checkstyle rule: ",tex)
            if "Basic Rule" in tex:
                ind = tex.index("Basic Rule") if "Basic Rule" in tex else tex.index("plaintext")
                pre = tex[ind:].strip()
            else:
                pre=tex.split("plaintext")[1]
                pre = "Basic Rule: "+pre
            # print("pre: ",pre)
            basic_rule = []
            for e in pre.split("\n"):
                # print(">>e: ",e)
                if e:
                    basic_rule.append(e)
                else:
                    break
            return "\n".join(basic_rule)

        basic_rule = extract_basic_rule(text)

        checkstyle_rules.append(basic_rule)

        # print("google java style: ", text)
        # break
    return "\n".join(checkstyle_rules)


def extract_basic_rule(tex):
    # print(">>>>a checkstyle rule: ",tex)
    if "Basic Rule" in tex:
        ind = tex.index("Basic Rule") if "Basic Rule" in tex else tex.index("plaintext")
        pre = tex[ind:].strip()
    else:
        pre = tex.split("plaintext")[1]
        pre = "Basic Rule: " + pre
    # print("pre: ",pre)
    basic_rule = []
    for e in pre.split("\n"):
        # print(">>e: ",e)
        if "Option Rule:" in e:
            break
        else:
            basic_rule.append(e)
    # print(">>>>","\n".join(basic_rule))
    return "\n".join(basic_rule)
def preprocess_checkstyle_dsl_all_results(gpt_checkstyle_dsls_dir,file_name):
    checkstyle_rules = []
    # print(">>>>>>",gpt_checkstyle_dsls[0])
    gpt_checkstyle_dsls = util.load_json(gpt_checkstyle_dsls_dir, file_name)

    for ind,(url,rule_name,text) in enumerate(gpt_checkstyle_dsls):
        # gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        # text = gpt_dsl_rule_list[str(ind)]



        basic_rule = extract_basic_rule(text)

        checkstyle_rules.append(rule_name+": "+basic_rule)

        # print("google java style: ", text)
        # break
    return "\n".join(checkstyle_rules)
def get_all_javastyle_dsl(gpt_preprocess_answer_dir_standard_example):
    google_java_dsl_rules = []

    def preprocess_javastyle_dsl(text):
        # print(">>>javastyle text: ",text)
        ind = text.index("Description is:")
        return text[ind + len("Description is:"):].strip()
    # print(">>>>>gpt_preprocess_answer_dir_standard_example: ",gpt_preprocess_answer_dir_standard_example,len(os.listdir(gpt_preprocess_answer_dir_standard_example)))
    # check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/","checkstyle_name_completedes_options_3_process")
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    for ind,w in enumerate(os.listdir(gpt_preprocess_answer_dir_standard_example)):
        if w.startswith("."):
            continue
        # print(">>>>w: ",w)
        gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example, w[:-5])
        # '''
        text = gpt_dsl_rule_list[w[:-5]]
        # print(">>>>>JavaStyle: ", text)
        checkstype_dsl = preprocess_javastyle_dsl(text)
        # if "NO RULE"
        # print(">>>>>checkstype_dsl: ", checkstype_dsl)
        if "NO RULE" in checkstype_dsl:
            google_java_dsl_rules.append("")
            continue
        google_java_dsl_rules.append(checkstype_dsl)
        # '''
    return google_java_dsl_rules

def get_all_javastyle_dsl_json_file(gpt_preprocess_answer_dir_standard_example,file_name):
    gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example,file_name)
    print(">>>>: ",gpt_dsl_rule_list[0])
    google_java_dsl_rules = []

    def preprocess_javastyle_dsl(text):
        # print(">>>javastyle text: ",text)
        if "Description is:" in text:
            ind = text.index("Description is:")
            return text[ind + len("Description is:"):].strip()
        elif "Description:" in text:
            ind = text.index("Description:")
            return text[ind + len("Description:"):].strip()
        else:
            return text.strip()

    # print(">>>>>gpt_preprocess_answer_dir_standard_example: ",gpt_preprocess_answer_dir_standard_example,len(os.listdir(gpt_preprocess_answer_dir_standard_example)))
    # check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/","checkstyle_name_completedes_options_3_process")
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    # print(">>>gpt_dsl_rule_list: ",gpt_dsl_rule_list[0])
    for ind,(url,rule_name,*_remain,text) in enumerate(gpt_dsl_rule_list):

        # if ind not in [32,45,48,51,67,74,86,100,114,119,120,121,122,126,127,128,133,140,174,175]:
        #     continue
        # text = gpt_dsl_rule_list[w[:-5]]
        # print(">>>>>JavaStyle: ", text)
        checkstype_dsl = preprocess_javastyle_dsl(text)
        # if "NO RULE"
        # print(">>>>>checkstype_dsl: ", checkstype_dsl)
        if "NO RULE" in checkstype_dsl:
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

if __name__ == "__main__":
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    # checkstyle_gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/CheckStyle_options_3_Simple_DSL_syntax_SplitSentence_example4_1_remove_repeat_option_preprocess/"
    # checkstyle_gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/"
    # checkstyle_gpt_preprocess_answer_dir_standard_example_filename = "check_style_url_rulename_dsl"
    # "gpt_dsl_answer/", "check_style_url_rulename_dsl"
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/CheckStyle_options_3_Simple_DSL_syntax_SplitSentence_example4_3_preprocess/"
    # checkstyle_dsl_basic_rules=preprocess_checkstyle_dsl(checkstyle_gpt_preprocess_answer_dir_standard_example)
    # checkstyle_dsl_basic_rules=preprocess_checkstyle_dsl_all_results(checkstyle_gpt_preprocess_answer_dir_standard_example,checkstyle_gpt_preprocess_answer_dir_standard_example_filename)
    # print(">>>: ",basic_rules)                                              check_style_url_dsl_description_option_improve_dslgrammar
    # gpt_answer_dir=util.data_root + "gpt_dsl_answer_gleJs_Eslint/gle_js_style_imprv_dsl/"
    my_dir_name="GenDSL_JS_ESLint_no_except_new/"

    # util.data_root + my_dir_name, "DSL_ESLint_all"
    all_checkstyle_dsls = util.load_json(util.data_root + my_dir_name,"DSL_ESLint_all")
    import random
    random.Random(2024).shuffle(all_checkstyle_dsls)

    checkstyle_dsl_basic_rules="\n".join(["RuleName: "+rulename+"\n"+extract_basic_rule(tex) for url,rulename,tex in all_checkstyle_dsls])
    print("len checkstyle_dsl_basic_rules: ",len(checkstyle_dsl_basic_rules),checkstyle_dsl_basic_rules[0])

    '''
    java_style_gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    javastyle_dsls= get_all_javastyle_dsl(java_style_gpt_preprocess_answer_dir_standard_example)
    '''
    javastyle_dsls_results= get_all_javastyle_dsl_json_file(util.data_root + my_dir_name, "javascriptstyle_url_rulename_dsl")
    javastyle_dsls = [dsl for *r,dsl in javastyle_dsls_results]    # break
    print("len javastyle_dsls: ",len(javastyle_dsls),javastyle_dsls[0])

    examples = '''For Example, respond like:
Mapping of {{Style}} to {{tool}}:
"Mandatory: No [ObjectConstructor]" : ["no-new-object", "no-object-constructor"]"
Mandatory: [InternalWhitespace] is [SingleSpace] if [ReservedWord] except [Function], [Super] before [OpenParenthesis]" : ["keyword-spacing","space-before-function-paren"]
"Mandatory: No [BlockScopedFunctionDeclaration]" : ["no-loop-func","no-inner-declarations"]
'''

    gpt_answer_dir = util.data_root + "gpt_dsl_answer/instr_selection_googlejavastyle_to_checkstyle_basicrule/"
    gpt_answer_dir = util.data_root + "gpt_dsl_answer/instr_selection_googlejavastyle_to_checkstyle_basicrule_2/"
    gpt_answer_dir = util.data_root + "gpt_dsl_answer_gleJs_Eslint/instr_select_gleJS_to_ESlit_basicrule copy/"
    gpt_answer_dir = util.data_root + "gpt_dsl_answer_gleJs_Eslint_imprv/instr_select_gleJS_to_ESlit_basicrule/"
    gpt_answer_dir = util.data_root + my_dir_name+"Config_name_select_googleJS_to_ESLint_new/"

    # '''
    # preprocess_promt(javastyle_dsls,DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
    #                  tool="Checkstyle", toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=examples)
    # '''
    dsl=util_js.dsl
    get_all_gpt_res_for_java_checkstyle(javastyle_dsls,DSL_Syntax=dsl, style="RuleSet of Google JavaScript Style Guide",tool="Eslint",
                                        toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=examples, model="gpt-4o-2024-08-06")

    '''

    benchmark = util.load_json(util.data_root + "benchmark_javascript/", "google2eslint_js_benchmark_simple_v3")
    # javastyle__dsl_rule_list = util.load_json(util.data_root + "gpt_dsl_answer_gleJs_Eslint/", "javastyle_url_rulename_dsl_example8_miss_rules_no_repeat")
    javastyle__dsl_rule_list = get_all_javastyle_dsl_json_file(util.data_root + "gpt_dsl_answer_gleJs_Eslint_imprv/",
                                                             "javascriptstyle_url_rulename_dsl")
    javastyle_dsls = [dsl for *r, dsl in javastyle_dsls_results]  # break

    correct_count, wrong_count = 0, 0
    ind_list = []
    ind_count = 0
    for ind_1, file_name in enumerate(os.listdir(gpt_answer_dir)):
        file_name = file_name[:-5]
        print(">>>>come here: ",file_name)

        ind =  int(file_name)
        url, googlejavastyle_rulename, text = javastyle__dsl_rule_list[ind]
        # for ind, (url, rule_name, text) in enumerate(gpt_dsl_rule_list):

        # for file_name in os.listdir(gpt_answer_dir):
        #     ind=file_name[:-5]

        # file_name = file_name[:-5]
        if not os.path.exists(gpt_answer_dir+file_name+".json"):
            continue

        json_res = util.load_json(gpt_answer_dir, file_name)
        res = json_res[file_name]
        # print(">>>>>>",res)
        possible_checkstype_rules = []
        for key in benchmark:
            if googlejavastyle_rulename in key:
                # config_res_rulename=benchmark[key]['modulename'] if benchmark[key] else ""
                if benchmark[key]:
                    # print(">>>benchmark[key]: ",ind,benchmark[key])
                    config_res_rulename_list = [e for e in benchmark[key][0]]
                    for rule_name in config_res_rulename_list:
                        # print(">>>>>rule_name: ",key, rule_name)
                        if rule_name not in res:
                            print(">>>>googlejavastyle RuleName selection wrong: ", googlejavastyle_rulename, text)
                            print(">>>res: ", ind,rule_name,res,"\n",benchmark[key])
                            ind_list.append(ind)
                            wrong_count += 1
                            break
                    else:
                        correct_count += 1
                else:
                    if res == "":
                        correct_count += 1
                    else:
                        # print(">>>>res: ", res.split(":")[-1])
                        if "None" not in res.split(":")[-1]:
                            # print(">>>>res: ", res.split(":")[-1])
                            # wrong_count += 1
                            pass
                    # print(">>>>googlejavastyle RuleName selection should be empty: ", googlejavastyle_rulename, text)
                    # print(">>>res: ", res)
                # break
    print(">>>wrong: ", wrong_count, correct_count,ind_list)
    '''
    '''
    def parse_result():
        all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze copy.csv")
        bench_mark=util.load_json(util.data_root + "benchmark/","checkstyle2google_java_benchmark")
        csv_results=[]
        gpt_checkstyle_dsls = util.load_json(checkstyle_gpt_preprocess_answer_dir_standard_example, checkstyle_gpt_preprocess_answer_dir_standard_example_filename)
        for ind in range(len(os.listdir(gpt_answer_dir))):
        # for file_name in os.listdir(gpt_answer_dir):
        #     ind=file_name[:-5]
            file_name=str(ind)
            json_res = util.load_json(gpt_answer_dir,file_name)
            res = json_res[file_name]
            url,rule_name,dsl_answer=gpt_checkstyle_dsls[ind]
            one_rule=copy.deepcopy(all_rules[ind+1])
            key=all_rules[ind+1][1]+'\n'+all_rules[ind+1][2]
            flag_key=None
            for key2 in bench_mark:
                if key[:20] ==key2[:20]:
                    flag_key=key2
                    break
            one_rule.insert(3,bench_mark[flag_key] if flag_key else "None")
            one_rule.insert(3,res)
            one_rule.insert(3,javastyle_dsls_results[ind][2] )
            csv_results.append(one_rule)
        # util.save_csv(util.data_root + "instr_select_csv/instr_selection_basic_rules_3.csv", csv_results)
        util.save_csv(util.data_root + "instr_select_csv/instr_selection_basic_rules_3_add_benchmark.csv", csv_results)

        # for each_rule in res.split("\n") :
        #     csv_results


    # parse_result()




    '''
    # import json
    # def extract_results(gpt_answer_dir):
    #     agent = GPTAgent()
    #
    #     for name in os.listdir(gpt_answer_dir):
    #         rule = util.load_json(gpt_answer_dir,name[:-5])
    #         text=rule[name[:-5]]
    #         text=text[8:-6]
    #         print("rule: ",text)
    #         json_object = json.loads(text)
    # extract_results(gpt_answer_dir)
            # print(">>>>>>rule: ", rule_description)
            #
            # # break
            # prompt = preprocess_extract_res_promt(DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
            #                           DSLruleset=rule_description,
            #                           tool="Checkstyle", toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar",
            #                           example="")
            #
            # # prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
            # print(">>>>>prompt: ", prompt)
            # answer = agent.get_response(prompt, model=model)
            # print(">>>>>>answer: ", ind, answer)
            # # util.save_json(util.data_root + gpt_answer_dir, str(ind), {ind: answer})
            # util.save_json(gpt_answer_dir, str(ind), {ind: answer})


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
        try:
            json_object = json.loads(answer_list)
            print(answer_list)
            print(">>>>>>: ", json_object)
            y_or_n = json_object['Answer']
            csv_results[-1].append(y_or_n)
            configuration_list = json_object['Configuration']
            csv_results[-1].append("\n******\n".join(configuration_list))
        except:
            print(">>>>>>>exception")
            if "'Answer': 'Yes'" in answer_list:
                config=answer_list.split("'Configuration': [")[-1]
                config=config.split("']'")[0]
                config_str="\n******\n".join(["<module"+each_config for each_config in config.split("<module") ])
                csv_results[-1].append('Yes')
                csv_results[-1].append(config_str)
                # for each_config in config.split("<module"):
                #     new_config="<module"+each_config
                # print(">>>>config:",config.split("<module"))
                # json_object = json.loads(config)
            elif '"Answer": "Yes"' in answer_list:
                config = answer_list.split('"Configuration": [')[-1]
                config=config.split('"]"')[0]
                config_str = "\n******\n".join(["<module" + each_config for each_config in config.split("<module")])
                csv_results[-1].append('Yes')
                csv_results[-1].append(config_str)
                print(">>>>config:", config.split("<module"))
                # json_object = json.loads(config)
            else:
                csv_results[-1].append('No')

        # for config in configuration_list:
        #     print(">>>config: ",config)
        #     csv_results[-1].append("******\n".join(configuration_list))

        # for e_asw in answer_list:
        #     print(">>>e_asw: ",e_asw)
        # break

    util.save_csv(util.data_root + "gpt_direct_answer/csv/gpt_answergooglejavastyle_checkstyle_nocheckstyleRule.csv",csv_results,["url","rule_name","description","gpt_answer","gpt_configuration"])
    '''