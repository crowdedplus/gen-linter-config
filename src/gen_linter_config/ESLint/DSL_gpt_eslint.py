import os,sys,inspect,copy
import re,json
import shutil

from gen_linter_config import util,util_java

from openai import OpenAI
from retry import retry
from gen_linter_config import GPTAgent
# rule=rule_description, DSL_Syntax=dsl
def preprocess_promt(rule: str, DSL_Syntax: str, style="ESLint Rule",grammar="Grammar",example=""):

    prompt='''Analyze the following {{Style}} and parse the description and options as rules using given {{grammar}} based on the step1 - step5. please delete unexisted OptionName. 

1. Analyze whether each sentence of descriptions of {{Style}} implies a rule or not. If the sentence is Ambiguous and code examples, do not classify it as a rule. 
2. For each sentence classified as rule, parse each rule using the given {{grammar}} based on the meaning of the description, pay attention to map to suitable formal Java term and select appropriate real operator characters to make its semantics clear and correct.
3. Analyze all options (option name, option description, option data type and data value range instead of default value. If value range can enumerate, list all its values.  For each option, 
4. Parse each option's description using the given {{grammar}} by understanding the complete semantics of the option description:
    4.1 Analyze the option name, data type and value range.
    4.2 Analyze the meanings of the option name based on the option description.
    4.3 If the option's data type is a single-element enumerable data type (like boolean, enum) instead of list, array, set ..., parse all different values into different rules the given {{grammar}} based on the semantics of the different option values.
    4.4 Otherwise, if the option's value is a set, parse the option as a single rule using the given {{grammar}} by understanding the complete semantics of the option description, with the option name enclosed in {{}}.
    4.5 For regular expression options, if option name contains "exception" or "ignore" its rule type is "Optional";  Otherwise, go to 4.4.
    4.6 Otherwise, use "Mandatory" as the rule type of regular expression options.
    4.7 Particularly, "message" option whose data type is string and its parsed rule should start with "Mandatory"
5. Parse a rule using the given {{grammar}} by understanding the complete semantics of the description, ensuring follow given {{grammar}}, ensuring correctness of semantics and pay attention to map to suitable formal Java term and select appropriate real operator characters.

***Note*** Generally, 'Mandatory' means rule must be satisfied, 'Optional' means rule may be satisfied or not be satisfied, or not applied the rule 
For example, exceptions or ignore XX, the rule type of rule is "Optional". 
Generally, For regular expression options, if option name contains "exception" or "ignore" its rule type is "Optional";  Otherwise, use "Mandatory" as the rule type of regular expression options.


{{Style}}:
{{Description}}

{{grammar}}:
{{Syntax}}

Response Format: 

**Detailed Analysis:** Think Step by Step
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
        option 1: optionname if no optionname, give "No Option Name"; datatype; value range
            if the option is not an object and enumerable like bool, parse all values are different rules using given {{grammar}}: 
                value 1 >>> parse value1 as rule using given {{grammar}} by analyzing its semantics 
                ...
                value n >>> parse valuen as rule as different rule using given {{grammar}} by analyzing its semantics
            if the option is not an object and open-ended like int, only parse the value are one rule, like
                int  >>> only parse it as general rules using giving {{grammar}} by analyzing its semantics
            if the option is an object:
                object: optionname;datatype: 
                    suboption 1.1 : optionname if no optionname, give "No Option Name"; datatype; value range
                        value1 >>> parse it as rule using given {{grammar}} by analyzing its semantics  
                        ...
                    suboption 1.2 : optionname if no optionname, give "No Option Name"; datatype; value range
                        ...
        ...
        
        option k: optionname if no optionname, give "No Option Name"; datatype; value range
        ...
        
{{Example}}
'''
#     prompt = '''Analyze the following {{Style}} and parse the description and options as rules using given {{grammar}}. Please think step by step. please delete unexisted OptionName.
#
# 1. Parse descriptions of {{Style}} using given {{grammar}} based on the following steps.
#     1.1 Analyze whether each sentence is a rule and then classify it as mandatory or optional. If the rule is subjective, do not classify it as a rule.
#     1.2 Parse the rule using given {{grammar}} by understanding its semantics, pay attention to map to suitable formal JavaScript term and select appropriate operator characters to make its semantics clear and correct.
#
# 2. Parse all options of {{Style}} using given {{grammar}} based on the following steps.
#     2.1 Extract all options. please provide the option name and data type (#Note do not extract default value). For each option,
#     2.2 Parse option using given {{grammar}} by understanding its semantics, pay attention to map to suitable formal JavaScript term and select appropriate operator characters to make its semantics clear and correct.
#
# {{Style}}:
# {{Description}}
#
# {{grammar}}:
# {{Syntax}}
#
# Response Format:
# Please Give Explanation!
# If there is no option, you only give basic rule
#     Final RuleSet Representation:
#     Basic Rule:
#     ...
#
# Otherwise,
#     Final RuleSet Representation:
#     Basic Rule:
#     ...
#
#     Option Rule:
#         first option: optionname if no optionname, give "no option name"; datatype;
#             if the option is not an object and enumerable like bool, parse all values are different rules using given {{grammar}}:
#                 value1 >>> parse value1 as rule using given {{grammar}} by analyzing its semantics
#                 ...
#                 valuen >>> parse valuen as rule as different rule using given {{grammar}} by analyzing its semantics
#             if the option is not an object and open-ended like int, only parse the value are one rule
#                 int  >>> only parse it as general rules using giving {{grammar}} by analyzing its semantics
#             if the option is an object:
#                 object: optionname;datatype:
#                 first suboption: optionname if no optionname, give "no option name"; datatype;
#                     value1 >>> parse it as rule using given {{grammar}} by analyzing its semantics
#                     ...
#
#         ...
#
# {{Example}}
# '''
    # '''

    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{Description}}", rule)
    prompt = prompt.replace("{{grammar}}", grammar)
    # prompt = prompt.replace("{{option values}}", util_java.options)

    return prompt


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
def get_all_gpt_res_for_java_checkstyle(rule_list,dsl, examples=None,style="Google Java Style Guide",model="gpt-4o"):
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
        # checkstyle_str = "\n".join(check_style_rule_list)

    for ind, rule_description in enumerate(rule_list[:]):
        # if ""
        # if "Indentation" not in rule_description:
        #     continue
        # if ind!=180:#169 109, 2, 180, 3, 71, 134  164 EmptyLineSeparator 118voidStarImport 146 58 IllegalTokenText  FileTabCharacter
        # if ind not in [58,2,3, 71,95,109,134,164,169,180]:#95:
        #     continue
        # if ind in [58,2,3, 71,95,109,134,164,169,180]:#95:
        #     continue
        # if not ("indentation" not in rule_description and "lines-between-class-members" not in rule_description):
        #     continue
        # if "default-case" not in rule_description or "default-case-last" in rule_description: #no-restricted-properties block-scoped-var #default-case-last indent indentation valid-jsdoc prefer-rest-params
        #     continue
        if "valid-jsdoc" not in rule_description: #padding-line-between-statements
            continue
        # if ind not in [70]:
        #     continue
        # if ind not in [134]:#95:
        #     continue
        # if ind not in [3, 10,183]:#95:
        #     continue
        # if ind!=180:#95:
        #     continue
        # if ind > 10:
        #     # continue
        #     break
        # rule_description = "\n".join([rule_name, description])
        # print("")
        # if "LineLength" not in rule_description and "NoLineWrap" not in rule_description: #
        #     continue
        # if "MissingJavadocMethod" not in rule_description:#NoLineWrap
        #     continue
        # if "ConstructorsDeclarationGrouping" not in rule_description:#JavadocParagraph CustomImportOrder JavadocParagraph SingleLineJavadoc
        #     continue
        print(">>>>>>rule: ", ind,rule_description)

        # continue
        # break
        prompt= preprocess_promt(rule=rule_description,example=examples,DSL_Syntax=dsl, style=style)
        print(">>>>>prompt: ",ind,prompt)
        answer = agent.get_response(prompt, model=model,temperature=0)
        print(">>>>>>answer: ", ind,answer)
        extract_dsl_prompt = Extract_DSL_Repr(answer)
        answer = agent.get_response(extract_dsl_prompt, model=model, temperature=0)
        print(">>>>>>final answer: ", ind,answer)

        # util.save_json(util.data_root + gpt_answer_dir, str(ind), {ind: answer})
        util.save_json(gpt_answer_dir, str(ind), {ind: answer})

        # break

if __name__ == "__main__":
    my_dir_name="GenDSL_JS_ESLint_no_except_new/"
    gpt_answer_dir=util.data_root + my_dir_name+"ESLint_DSL/"

    jdata = util.load_json(util.data_root + "benchmark/benchmark_javascript/",
                           "eslint_url_sum_desc_opt_old")
    all_rules = [[v[0], k, v[1] + "\n" + v[2], v[3]] for k, v in jdata.items()]
    # print(">>>>rule: ",all_rules[0][-2],"********\n",all_rules[0][-1])
    rule_list = []
    for html, name, des, opt in all_rules:
        rule_list.append("Rulename: "+name+"\n"+"\nDescription: \n"+des+"\nOptions Description: "+opt)
    a = '''For Example,  
Description: Enforce consistent indentation


There are several common guidelines which require specific indentation of nested blocks and statements, like:


```json
function hello(indentSize, type) {
    if (indentSize === 4 && type !== 'tab') {
        console.log('Each next indentation will increase on 4 spaces');
    }
}
```

These are the most common scenarios recommended in different style guides:


- Two spaces, not longer and no tabs: Google, npm, Node.js, Idiomatic, Felix

- Tabs: jQuery

- Four spaces: Crockford
This rule enforces a consistent indentation style. The default style is `4 spaces`.
Options Description: This rule has a mixed option:

For example, for 2-space indentation:


```json
{
    "indent": ["error", 2]
}
```

Or for tabbed indentation:


```json
{
    "indent": ["error", "tab"]
}
```

Examples of incorrect code for this rule with the default options:


```json
/*eslint indent: "error"*/

if (a) {
  b=c;
  function foo(d) {
    e=f;
  }
}
```

Examples of correct code for this rule with the default options:


```json
/*eslint indent: "error"*/

if (a) {
    b=c;
    function foo(d) {
        e=f;
    }
}
```

This rule has an object option:


- `"ignoredNodes"` can be used to disable indentation checking for any AST node. This accepts an array of selectors . If an AST node is matched by any of the selectors, the indentation of tokens which are direct children of that node will be ignored. This can be used as an escape hatch to relax the rule if you disagree with the indentation that it enforces for a particular syntactic pattern.

- `"SwitchCase"` (default: 0) enforces indentation level for `case` clauses in `switch` statements

- `"VariableDeclarator"` (default: 1) enforces indentation level for `var` declarators; can also take an object to define separate rules for `var`, `let` and `const` declarations. It can also be `"first"`, indicating all the declarators should be aligned with the first declarator.

- `"outerIIFEBody"` (default: 1) enforces indentation level for file-level IIFEs. This can also be set to `"off"` to disable checking for file-level IIFEs.

- `"MemberExpression"` (default: 1) enforces indentation level for multi-line property chains. This can also be set to `"off"` to disable checking for MemberExpression indentation.

- `"FunctionDeclaration"` takes an object to define rules for function declarations.


- `parameters` (default: 1) enforces indentation level for parameters in a function declaration. This can either be a number indicating indentation level, or the string `"first"` indicating that all parameters of the declaration must be aligned with the first parameter. This can also be set to `"off"` to disable checking for FunctionDeclaration parameters.

- `body` (default: 1) enforces indentation level for the body of a function declaration.


- `"FunctionExpression"` takes an object to define rules for function expressions.


- `parameters` (default: 1) enforces indentation level for parameters in a function expression. This can either be a number indicating indentation level, or the string `"first"` indicating that all parameters of the expression must be aligned with the first parameter. This can also be set to `"off"` to disable checking for FunctionExpression parameters.

- `body` (default: 1) enforces indentation level for the body of a function expression.


- `"StaticBlock"` takes an object to define rules for class static blocks.


- `body` (default: 1) enforces indentation level for the body of a class static block.


- `"CallExpression"` takes an object to define rules for function call expressions.


- `arguments` (default: 1) enforces indentation level for arguments in a call expression. This can either be a number indicating indentation level, or the string `"first"` indicating that all arguments of the expression must be aligned with the first argument. This can also be set to `"off"` to disable checking for CallExpression arguments.


- `"ArrayExpression"` (default: 1) enforces indentation level for elements in arrays. It can also be set to the string `"first"`, indicating that all the elements in the array should be aligned with the first element. This can also be set to `"off"` to disable checking for array elements.

- `"ObjectExpression"` (default: 1) enforces indentation level for properties in objects. It can be set to the string `"first"`, indicating that all properties in the object should be aligned with the first property. This can also be set to `"off"` to disable checking for object properties.

- `"ImportDeclaration"` (default: 1) enforces indentation level for import statements. It can be set to the string `"first"`, indicating that all imported members from a module should be aligned with the first member in the list. This can also be set to `"off"` to disable checking for imported module members.

- `"flatTernaryExpressions": true` (`false` by default) requires no indentation for ternary expressions which are nested in other ternary expressions.

- `"offsetTernaryExpressions": true` (`false` by default) requires indentation for values of ternary expressions.

- `"ignoreComments"` (default: false) can be used when comments do not need to be aligned with nodes on the previous or next line.

Level of indentation denotes the multiple of the indent specified. 

You respond like: 

Final RuleSet Representation:
Basic Rule:
Mandatory: [Indentation] is consistent
Except [Comment]
And
Mandatory: [ModuleName] is [CamelCase]

Option Rule:
first option: No OptionName; string or int;
    int >>> Mandatory: [Indentation] is {{int}} [Space]
    "tab" >>> Mandatory: [Indentation] is {{tab}}

second option: ignoredNodes; Array of selectors;
    Array of selectors >>> Optional: [Indentation] not for {{ignoredNodes}}

third option: SwitchCase; int;
    int >>> Mandatory: [Indentation] of [Case Clauses] is {{SwitchCase}} * [indention] of {{firstOption}}

fourth option: VariableDeclarator; int, or object for var, let and const declarations, or "first";
    int >>> Mandatory: [Indentation] of [variable declarators] is {{VariableDeclarator}} * [indention] of {{firstOption}}
    object for var, let and const declarations: no option name; 
        first suboption: var; int
            int >>> Mandatory: [Indentation] of [Variable Declaration] is {{var}} * [indention] of {{firstOption}}
        second suboption: let; int
            int >>> Mandatory: [Indentation] of [Block-scoped Variable Declaration] is {{let}} * [indention] of {{firstOption}}
        third suboption: const; int
            int >>> Mandatory: [Indentation] of [Block-scoped Constant Declaration] is {{const}} * [indention] of {{firstOption}}
    "first" >>> Mandatory: [Indentation] of [Variable Declarators] = [first declarator] of [Variable Declarators]

fifth option: ignoreComments; boolean;
    true >>> Optional: [Indentation] not for [comments] 
    false >>> Mandatory: [Indentation] for [comments] 
    
sixth option: ignorePattern; regular expression; 
    regular expression >>> Optional: [line length] not for {{ignorePattern}}
    '''
    examples='''For Example, 
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
Checks for braces around code blocks.
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
    tokens >>> Mandatory: [block] of {{tokens}} have [Brace]
    
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
'''#ignorePattern option: Pattern; regular expression;
    #ignorePattern >>> Optional: [block] have [Brace] Except {{ignorePattern}}
    # examples=''
    examples = '''For Example, 
For Example,  
Description: Enforce consistent indentation


There are several common guidelines which require specific indentation of nested blocks and statements, like:


```json
function hello(indentSize, type) {
    if (indentSize === 4 && type !== 'tab') {
        console.log('Each next indentation will increase on 4 spaces');
    }
}
```

These are the most common scenarios recommended in different style guides:


- Two spaces, not longer and no tabs: Google, npm, Node.js, Idiomatic, Felix

- Tabs: jQuery

- Four spaces: Crockford
This rule enforces a consistent indentation style. The default style is `4 spaces`.
Options Description: This rule has a mixed option:

For example, for 2-space indentation:


```json
{
    "indent": ["error", 2]
}
```

Or for tabbed indentation:


```json
{
    "indent": ["error", "tab"]
}
```

Examples of incorrect code for this rule with the default options:


```json
/*eslint indent: "error"*/

if (a) {
  b=c;
  function foo(d) {
    e=f;
  }
}
```

Examples of correct code for this rule with the default options:


```json
/*eslint indent: "error"*/

if (a) {
    b=c;
    function foo(d) {
        e=f;
    }
}
```

This rule has an object option:


- `"ignoredNodes"` can be used to disable indentation checking for any AST node. This accepts an array of selectors . If an AST node is matched by any of the selectors, the indentation of tokens which are direct children of that node will be ignored. This can be used as an escape hatch to relax the rule if you disagree with the indentation that it enforces for a particular syntactic pattern.

- `"SwitchCase"` (default: 0) enforces indentation level for `case` clauses in `switch` statements

- `"VariableDeclarator"` (default: 1) enforces indentation level for `var` declarators; can also take an object to define separate rules for `var`, `let` and `const` declarations. It can also be `"first"`, indicating all the declarators should be aligned with the first declarator.

- `"outerIIFEBody"` (default: 1) enforces indentation level for file-level IIFEs. This can also be set to `"off"` to disable checking for file-level IIFEs.

- `"MemberExpression"` (default: 1) enforces indentation level for multi-line property chains. This can also be set to `"off"` to disable checking for MemberExpression indentation.

- `"FunctionDeclaration"` takes an object to define rules for function declarations.


- `parameters` (default: 1) enforces indentation level for parameters in a function declaration. This can either be a number indicating indentation level, or the string `"first"` indicating that all parameters of the declaration must be aligned with the first parameter. This can also be set to `"off"` to disable checking for FunctionDeclaration parameters.

- `body` (default: 1) enforces indentation level for the body of a function declaration.


- `"FunctionExpression"` takes an object to define rules for function expressions.


- `parameters` (default: 1) enforces indentation level for parameters in a function expression. This can either be a number indicating indentation level, or the string `"first"` indicating that all parameters of the expression must be aligned with the first parameter. This can also be set to `"off"` to disable checking for FunctionExpression parameters.

- `body` (default: 1) enforces indentation level for the body of a function expression.


- `"StaticBlock"` takes an object to define rules for class static blocks.


- `body` (default: 1) enforces indentation level for the body of a class static block.


- `"CallExpression"` takes an object to define rules for function call expressions.


- `arguments` (default: 1) enforces indentation level for arguments in a call expression. This can either be a number indicating indentation level, or the string `"first"` indicating that all arguments of the expression must be aligned with the first argument. This can also be set to `"off"` to disable checking for CallExpression arguments.


- `"ArrayExpression"` (default: 1) enforces indentation level for elements in arrays. It can also be set to the string `"first"`, indicating that all the elements in the array should be aligned with the first element. This can also be set to `"off"` to disable checking for array elements.

- `"ObjectExpression"` (default: 1) enforces indentation level for properties in objects. It can be set to the string `"first"`, indicating that all properties in the object should be aligned with the first property. This can also be set to `"off"` to disable checking for object properties.

- `"ImportDeclaration"` (default: 1) enforces indentation level for import statements. It can be set to the string `"first"`, indicating that all imported members from a module should be aligned with the first member in the list. This can also be set to `"off"` to disable checking for imported module members.

- `"flatTernaryExpressions": true` (`false` by default) requires no indentation for ternary expressions which are nested in other ternary expressions.

- `"offsetTernaryExpressions": true` (`false` by default) requires indentation for values of ternary expressions.

- `"ignoreComments"` (default: false) can be used when comments do not need to be aligned with nodes on the previous or next line.

Level of indentation denotes the multiple of the indent specified. 


You respond like: 
Final RuleSet Representation:
Basic Rule:
Mandatory: Consistent [Indentation]
;
Mandatory: [ModuleName] is [CamelCase]
And
Mandatory: [ModuleName] is not [LowCamelCase]


Option Rule:
option 1: No OptionName; int or string; 1,2, ..., or  "tab"
    int >>> Mandatory: [Indentation] is int {{option 1}} [Space]
    or
    "tab" >>> Mandatory: [Indentation] is [tabbed indentation]
    
Note: the data type of ignoreComments option is boolean, is a single-element enumerable data type, we parse all different values into different rule using given grammar 
option 2: ignoreComments; boolean; true or false
    true >>> Optional: [Indentation] not for [comments] 
    false >>> Mandatory: [Indentation] for [comments] 
    
option 3: No Option Name; obj; {"suboption name": XX, ....}
    suboption 2.1: ignoredNodes; Array of selectors; ["XX", ..., "XX"]
        Array of selectors >>> Optional: [Indentation] not for {{ignoredNodes}}

    suboption 2.2: SwitchCase; int; 1,2, ...
        int >>> Mandatory: [Indentation] of [Case Clauses] is {{SwitchCase}} multiplied by {{option 1}}

    suboption 2.3: VariableDeclarator; int, or object for var, let and const declarations, or "first"; 1,2, ..., or { "var":XX, "let":XX, "const":XX }, or 'first'
        int type value >>> Mandatory: [Indentation] of [variable declarators] is {{VariableDeclarator}} multiplied by {{option 1}}
        or 
        object for var, let and const declarations; :
            subsuboption 2.3.1: var; int; 1,2,... 
                int >>>  Mandatory: [Indentation] of [Variable Declaration] is {{VariableDeclarator}} multiplied by {{option 1}}
            subsuboption 2.3.2: let; int; 1,2,...
                int >>>  Mandatory: [Indentation] of [Block-scoped Variable Declaration] is {{VariableDeclarator}} multiplied by {{option 1}}
            subsuboption 2.3.3: const; int; 1,2,...
                int >>>  Mandatory: [Indentation] of [Block-scoped Constant Declaration] is {{VariableDeclarator}} multiplied by {{option 1}} 
        or
        "first" >>> Mandatory: [Indentation] of [Variable Declarators] = [Indentation] of [first declarator] of [Variable Declarators]

option 6: ignorePattern; regular expression; {"ignorePattern": XXX, }
    regular expression >>> Optional: [line length] not for {{ignorePattern}}
    
For the option description of lines-between-class-members rule: 
First option can be string "always" or "never" or an object with a property named enforce:
"always"(default) require an empty line after class members
"never" disallows an empty line after class members
Object: An object with a property named enforce. The enforce property should be an array of objects, each specifying the configuration for enforcing empty lines between specific pairs of class members.
enforce: You can supply any number of configurations. If a member pair matches multiple configurations, the last matched configuration will be used. If a member pair does not match any configurations, it will be ignored. Each object should have the following properties:
blankLine: Can be set to either "always" or "never", indicating whether a blank line should be required or disallowed between the specified members.
prev: Specifies the type of the preceding class member. It can be "method" for class methods, "field" for class fields, or "*" for any class member.
next: Specifies the type of the following class member. It follows the same options as prev.

You should respond like: 
option 1: No OptionName; string or object; "always" or "never" or "enforce": [{"blankLine": XX, "prev": XX, "next": XX}, ...]
    "always" >>> Mandatory: An [Empty Line] after class members 
    or 
    "never" >>> Mandatory: No [Empty Line] after class members 
    or
    object; No OptionName; {"suboption name": XXX, ...}
        suboption 1.1 enforce; array of objects; {"enforce": [ {"subsuboption": XX, ...}, ...]} >>> Mandatory: [Empty Line] between {{enforce}} class members 
            subsuboption 1.1.1: blankLine; string ; "always" or "never" 
                "always" >>>  Mandatory: [Empty Line] between {{prev}} class members and {{next}} class members
                "never" >>>  Mandatory: No [Empty Line] between {{prev}} class members and {{next}} class members
            subsuboption 1.1.2: prev; string; "method" or "field" or "*"
                if blankLine is "always": 
                    "method" >>>  Mandatory:[Empty Line] between "method" class members and {{next}} class members
                    "field" >>>  Mandatory:[Empty Line] between "field" class members and {{next}} class members
                    "*" >>>  Mandatory:[Empty Line] between any class members and {{next}} class members
                elif blankLine is "never": 
                    "method" >>>  Mandatory: No [Empty Line] between "method" class members and {{next}} class members
                    "field" >>>  Mandatory: No [Empty Line] between "field" class members and {{next}} class members
                    "*" >>>  Mandatory: No [Empty Line] between any class members and {{next}} class members
            subsuboption 1.1.3: next; string; "var", "return", "*", "block", "block-like", "break", "case", "cjs-export", "cjs-import", "class", "const", "continue", "debugger", "default", "directive", "do", "empty", "export", "expression", "for", "function", "if", "iife", "import", "let", "multiline-block-like", "multiline-const", "multiline-expression", "multiline-let", "multiline-var", "return", "singleline-const", "singleline-let", "singleline-var", "switch", "throw", "try", "var", "while", "with"
                if blankLine is "always": 
                    "method" >>> Mandatory: [Empty Line] between {{prev}} class members and "method" class members
                    "field" >>> Mandatory: [Empty Line] between {{prev}} class members and "field" class members
                    "*" >>>  [Empty Line] between {{prev}} class members and any class members
                elif blankLine is "never": 
                    "method" >>> Mandatory: No [Empty Line] between {{prev}} class members and "method" class members
                    "field" >>> Mandatory: No [Empty Line] between {{prev}} class members and "field" class members
                    "*" >>> Mandatory: No [Empty Line] between {{prev}} class members and any class members
        '''

    dsl = util_js.dsl
    get_all_gpt_res_for_java_checkstyle(rule_list,dsl,  examples=examples,style="ESLint Rule",model="gpt-4o-2024-08-06")

    complete_info_checkstyle_to_dsl = []
    for ind in range(len(os.listdir(gpt_answer_dir))):
        gpt_dsl_rule_list = util.load_json(gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(util.data_root + gpt_answer_dir, str(ind))
        # gpt_dsl_rule_list_original_answer = util.load_json(gpt_answer_dir, str(ind))

        text = gpt_dsl_rule_list[str(ind)]
        # print(text)
        ruleone = copy.deepcopy(all_rules[ind])
        # ruleone.insert(3, gpt_dsl_rule_list_original_answer[str(ind)])
        ruleone.insert(4, text)
        # print(">>>: ", check_style_rule_list[ind][:2] + [text])
        complete_info_checkstyle_to_dsl.append(all_rules[ind][:2] + [text])
        # rule_list_add_gpt_result.append(ruleone)
        # rule_list_add_gpt_result[ind+1].insert
    util.save_json(util.data_root + my_dir_name, "DSL_ESLint_all",
                   complete_info_checkstyle_to_dsl)
    # all_checkstyle_dsls = util.load_json(util.data_root + dir_name, "DSL_checkstyle_all")

    '''
    
    checkstyle_options_classify=[]
    for i in range(len(os.listdir(gpt_answer_dir))):
        data = util.load_json(gpt_answer_dir,str(i))
        checkstyle_options_classify.append(data)
    util.save_json(util.data_root+"gpt_dsl_answer/","checkstyle_to_DSL_improve_dslgrammar",checkstyle_options_classify)
    '''
    '''
    all_checkstyle_dsls = []
    all_rules = util.load_json(util.data_root + "style_tool_rules/",
                               "checkstyle_name_completedes_options_3_process")
    # gpt_answer_dir=util.data_root + "gpt_dsl_answer/gpt_check_style_to_DSL_Description_Option_3_check_nooption_improve_dslgrammar2/"

    for ind in range(len(os.listdir(gpt_answer_dir))):
        gpt_dsl_rule_list = util.load_json(gpt_answer_dir, str(ind))
        text = gpt_dsl_rule_list[str(ind)]
        print(text)
        all_checkstyle_dsls.append(all_rules[ind][:2] + [text])
    util.save_json(util.data_root + "gpt_dsl_answer/", "checkstyle_to_DSL_improve_dslgrammar",
                   all_checkstyle_dsls)
    '''
    # '''
    # rule_list_add_gpt_result[ind+1].insert
    # util.save_json(util.data_root + "gpt_dsl_answer/", "check_style_url_rulename_dsl", complete_info_checkstyle_to_dsl)
    # util.save_json(util.data_root + "GoogleJavaStyle/javastyle_myanalyze copy.csv", str(ind), {ind: answer})
    # util.save_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze copy_add_GPT_DSL.csv",rule_list_add_gpt_result)
    # util.save_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze copy_add_GPT_DSL_add_original_answer.csv",rule_list_add_gpt_result)
    # util.save_csv(util.data_root + "CheckStyle/CheckStyle_options_3_Simple_DSL_syntax_SplitSentence_example4_1_remove_repeat_option_add_GPT_answer.csv",rule_list_add_gpt_result)
    # util.save_csv(util.data_root + "CheckStyle/CheckStyle_options_3_Simple_DSL_syntax_SplitSentence_example4_3_add_GPT_answer.csv",rule_list_add_gpt_result)
    # '''

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