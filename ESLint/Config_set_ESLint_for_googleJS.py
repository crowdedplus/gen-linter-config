import copy
import os, json, inspect, sys
import re
import shutil

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandparentdir = os.path.dirname(parentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, grandparentdir)
import util, util_js

from openai import OpenAI
from retry import retry
from gpt_wrapper import GPTAgent


def preprocess_promt(DSL_Syntax: str, style="RuleSet of Google JavaScript Style Guide", DSLruleset=None, tool="ESLint",
                     toolruleset=None, grammar="Grammar", example=""):
    '''# For each mapping, extract all Java Terms enclosed in "[]", determine whether lacks option name, option rules from its corresponding RuleName that corresponding to the extracted Java Terms enclosed with "[]" of StyleSEM rule.
'''
    prompt = '''Extract each rule from the following {{Style}} where starting with "Mandatory" or "Optional".
Identify if each rule in RuleSet of {{Style}} has basically semantically equivalent rules from Basic Rule or Option Rule of {{tool}} based on the following step 1 -- step 9. 

Do not modify the rule type ('Mandatory' or 'Optional') of the extracted Option/Basic Rule to align with the rule type of the corresponding rule in {{Style}}. 
The rule type of the matching Option/Basic Rule must remain consistent with its original type as defined in the Option/Basic Rule. 

1. From the Basic Rule of the following {{tool}}, excerpt possible matching rule with the rule of {{Style}}. Do not alter the basic rule type ('Mandatory' or 'Optional') when excerpt possible matching rule.
2. From the Option Rule of the following {{tool}}, from same rule types of option rules, excerpt possible related option name and Option Rule with the semantics and objects and rule type ('Mandatory' or 'Optional') that the rule of {{Style}} checks. The rule type ('Mandatory' or 'Optional') of the matching Option Rule is preserved.
3. Extract all Java Terms enclosed in "[]" of the rule {{Style}} .
4. Determine whether exists option name, option rules from its corresponding RuleName that can reflect to the extracted Java Terms enclosed with "[]" of StyleSEM rule. 
5. If the data type of option name is not regular expression, extract its value range and data type.
6. From its value range, data type and option rule, set specific option values based on data type and option rule, ensuring alignning with the rule of {{Style}}. otherwise, set the option values as "regular expression".
6. If the data type of option name is regular expression, set its value is regular expression.
7. Give the corresponding RuleName for the matched basic rules and option rules. 
8. Only keep each rule type of basic rule and option rules  is same as the rule type of the rule of RuleSet of {{Style}}
9. Ensure that the specified option values are supported by the valid range for the corresponding option

Note: Do not miss any rule in RuleSet of {{Style}}. And for each rule, individually provide detailed analysis for each step, do not miss any step!
Ensure that the specified option values are supported by the valid range for the corresponding option

{{Style}} expressed in {{grammar}}. 
{{tool}} consists of RuleName, Basic Rule expressed in {{grammar}}, and Option Rule expressed in {{grammar}}. 

*********************

{{Style}}:
{{DSLruleset}}

*********************

{{tool}}: #Each Option Rule are formatted as follows:
OptionName, Data Type, Value Range
different rules expressed in {{grammar}} for different values.

{{toolruleset}}

{{grammar}}:
{{Syntax}}

{{Example}}

*********************

Response Format: 
Note first give analysis of each step for each rule of {{Style}}!!! and then give the answer!!!
###Analalysis:###
1. **Rule:**
step 1: XXX step 2: XXX step 3: XXX step 4: XXX step 5: XXX step 6: XXX step 7: XXX step 8: XXX step 9: XXX
...
###Mappings:###
Note before ">>>" is rule of {{Style}}, after ">>>" is the corresponding rule from {{tool}}
1. excerpt first rule expressed in {{grammar}} from {{Style}}  ">>>" corresponding RuleName, Basic Rule and Option Rule from {{tool}}
2. excerpt second rule expressed in {{grammar}} from {{Style}}  ">>>" corresponding RuleName, Basic Rule and Option Rule from {{tool}}
give corresponding RuleName, Basic Rule and Option Rule from {{tool}} as following format:
if matching rule of Basic Rule and Option Rule from {{tool}} that have same semantics with rule of {{Style}} excerpted from {{Style}}, give 
    RuleName1: <Give corresponding RuleName from {{tool}}> 
    Basic Rule: <Excerpt matching rule from Basic Rule of {{tool}}>
    Option Rule: If there is corresponding option rule
    option 1: corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
       suboption 1.1: corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
       suboption 1.2: corresponding OptionName; Option Value; option rule expressed in given {{grammar}}
       ... 
    ...
    option k:  corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
    ...
    
    RuleName2: <Give corresponding RuleName from {{tool}}> 
    ...

For example, 
1. Mandatory: [Line] containing [goog.module declaration] not have [80-column limit]
   >>> 
   RuleName: max-len
   Basic Rule: Mandatory: [Line Length] is [Maximum] [Unicode Characters]
   Option Rule: 
     option 1: code; 80; Mandatory: [Line Length] is {{code}} [Unicode Characters]
     option 4: ignorePattern; regular expression; Optional: [Line Length] not for {{ignorePattern}}

2. Mandatory: No [DefaultExports] is [Used]
   >>> 
   RuleName: no-restricted-exports
   Basic Rule: Mandatory: No [specified names] in [exports]
   Option Rule: 
     option 2: restrictDefaultExports; object; 
       suboption 2.1: direct; true; Mandatory: No [export default] declarations

3. Mandatory: No [GoogRequire] for [AnotherESModule]
   >>> 
   RuleName: no-restricted-syntax
   Basic Rule: Mandatory: No [specified syntax] in [JavaScript code]
   Option Rule: 
     option 1: No Option Name; [{'selector': 'CallExpression[callee.object.name="goog"][callee.property.name="require"]', 'message': 'Do not goog.require another ES module'}]; Mandatory: No [syntax] specified by {{option 1}} in [JavaScript code]

4. Mandatory: [BlankLine] between [ConsecutiveMethods] in [Class, ObjectLiteral]
>>> 
   RuleName: lines-between-class-members 
   Basic Rule: Mandatory: [Empty Line] between [Class Members]  
   Option Rule: 
     option 1: No Option Name; object; 
        suboption 1.1: enforce; array of objects; [{"blankLine": 'always',"prev": "method", "next": "method"}];  Mandatory: [Empty Line] between "method" of [Class Members] and "method" of [Class Members]
            suboption 1.1.1: blankLine; "always"; [Blank Line] between {{prev}} and {{next}} statements
            suboption 1.2.1: prev; "method"; the type of preceding statement is method
            suboption 1.3.1: next; "method"; the type of the following statement is method      

5. Mandatory: [EmptyLine] between [goog.provide] and [goog.require]  
 >>>  
 RuleName: padding-line-between-statements 
 Basic Rule: Mandatory: [Blank Line] between [Statement] and [Statement] is [Required] or [Disallowed]
 Option Rule: None because prev and next options of padding-line-between-statements do not support goog.provide and goog.require

6. Mandatory: [Contents] of [SwitchBlock] is [Indented+2]  
   >>>  
   RuleName: indent  
   Basic Rule: Mandatory: Consistent [Indentation]  
   Option Rule:  
   option 1: No Option Name; 2; Mandatory: [Indentation] is {{option 1}} [Space]  
   option 3: SwitchCase; 1; Mandatory: [Indentation] of [Case Clauses] is {{SwitchCase}} multiplied by {{option 1}}

Otherwise, give None.
'''
    '''
4. Mandatory: [BlankLine] between [ConsecutiveMethods] in [Class, ObjectLiteral]
>>> 
   RuleName: lines-between-class-members 
   Basic Rule: Mandatory: [Empty Line] between [Class Members]  
   Option Rule: 
     option 1: No Option Name; object; 
        enforce; array of objects; [{"blankLine": 'always',"prev": "method", "next": "method"}];  Mandatory: [Empty Line] between "method" of [Class Members] and "method" of [Class Members]
'''
    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{DSLruleset}}", DSLruleset)
    prompt = prompt.replace("{{tool}}", tool)

    prompt = prompt.replace("```plaintext", "")

    prompt = prompt.replace("```", "")

    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def preprocess_promt_simple(DSL_Syntax: str, style="RuleSet of Google JavaScript Style Guide", DSLruleset=None,
                            tool="ESLint",
                            toolruleset=None, grammar="Grammar", example=""):
    '''# For each mapping, extract all Java Terms enclosed in "[]", determine whether lacks option name, option rules from its corresponding RuleName that corresponding to the extracted Java Terms enclosed with "[]" of StyleSEM rule.
'''
    prompt = '''Extract each rule from the following {{Style}} where starting with "Mandatory" or "Optional".
Identify if each rule in RuleSet of {{Style}} has semantically equivalent rules from Basic Rule or Option Rule of {{tool}} based on the following step 1 -- step 6. 

Do not modify the rule type ('Mandatory' or 'Optional') of the extracted Option/Basic Rule to align with the rule type of the corresponding rule in {{Style}}. 
The rule type of the matching Option/Basic Rule must remain consistent with its original type as defined in the Option/Basic Rule. 

1. From the Basic Rule of the following {{tool}}, excerpt possible matching rule with the rule of {{Style}}. Do not alter the basic rule type ('Mandatory' or 'Optional') when excerpt possible matching rule.
2. From the Option Rule of the following {{tool}}, excerpt possible related option name and Option Rule with the semantics and objects that the rule of {{Style}} checks. The rule type ('Mandatory' or 'Optional') of the matching Option Rule is preserved.
3. Extract all Java Terms enclosed in "[]" of the rule {{Style}} .
4. Determine whether exists option name, option rules from its corresponding RuleName that can reflect to the extracted Java Terms enclosed with "[]" of StyleSEM rule. 
5. If the data type of option name is not regular expression, set specific option values based on data type and option rule, ensuring alignning with the rule of {{Style}}. otherwise, set the option values as "regular expression".
6. Give the corresponding RuleName for the matched basic rules and option rules. 

Note: Do not miss any in RuleSet of {{Style}}. And for each rule, individually provide detailed analysis for each step, do not miss any step!

{{Style}} expressed in {{grammar}}. 
{{tool}} consists of RuleName, Basic Rule expressed in {{grammar}}, and Option Rule expressed in {{grammar}}. 

*********************

{{Style}}:
{{DSLruleset}}

*********************

{{tool}}: #Each Option Rule are formatted as follows:
OptionName, Data Type, Value Range
different rules expressed in {{grammar}} for different values.

{{toolruleset}}

{{grammar}}:
{{Syntax}}

{{Example}}

*********************

Response Format: 
Note first give analysis of each step for each rule of {{Style}}!!! and then give the answer!!!
###Analalysis:###
...
###Mappings:###
Note before ">>>" is rule of {{Style}}, after ">>>" is the corresponding rule from {{tool}}
1. excerpt first rule expressed in {{grammar}} from {{Style}}  ">>>" corresponding RuleName, Basic Rule and Option Rule from {{tool}}
2. excerpt second rule expressed in {{grammar}} from {{Style}}  ">>>" corresponding RuleName, Basic Rule and Option Rule from {{tool}}
give corresponding RuleName, Basic Rule and Option Rule from {{tool}} as following format:
if matching rule of Basic Rule and Option Rule from {{tool}} that have same semantics with rule of {{Style}} excerpted from {{Style}}, give 
    RuleName1: <Give corresponding RuleName from {{tool}}> 
    Basic Rule: <Excerpt matching rule from Basic Rule of {{tool}}>
    Option Rule: 
    option 1: corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
       suboption 1.1: corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
       suboption 1.2: corresponding OptionName; Option Value; option rule expressed in given {{grammar}}
       ... 
    ...
    option k:  corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 
    ...
    RuleName2: <Give corresponding RuleName from {{tool}}> 
    ...

For example, 
1. Mandatory: [Line] containing [goog.module declaration] not have [80-column limit]
   >>> 
   RuleName: max-len
   Basic Rule: Mandatory: [Line Length] is [Maximum] [Unicode Characters]
   Option Rule: 
     option 1: code; 80; Mandatory: [Line Length] is {{code}} [Unicode Characters]
     option 4: ignorePattern; regular expression; Optional: [Line Length] not for {{ignorePattern}}

2. Mandatory: No [DefaultExports] is [Used]
   >>> 
   RuleName: no-restricted-exports
   Basic Rule: Mandatory: No [specified names] in [exports]
   Option Rule: 
     option 2: restrictDefaultExports; object; 
       suboption 2.1: direct; true; Mandatory: No [export default] declarations

3. Mandatory: No [GoogRequire] for [AnotherESModule]
   >>> 
   RuleName: no-restricted-syntax
   Basic Rule: Mandatory: No [specified syntax] in [JavaScript code]
   Option Rule: 
     option 1: No Option Name; [{'selector': 'CallExpression[callee.object.name="goog"][callee.property.name="require"]', 'message': 'Do not goog.require another ES module'}]; Mandatory: No [syntax] specified by {{option 1}} in [JavaScript code]

Otherwise, give None.
'''
    prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Style}}", style)
    prompt = prompt.replace("{{DSLruleset}}", DSLruleset)
    prompt = prompt.replace("{{tool}}", tool)

    prompt = prompt.replace("```plaintext", "")

    prompt = prompt.replace("```", "")

    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def extract_delete_config_promt(text: str, tool=""):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Excerpt Mappings from the following text without altering their content in any way. Only perform the extraction.
For the following mappings, for each mapping, 
according to the Tool Information, check whether the set option values are outside the valid option value range, if yes, delete the mapping.

Note: For each mapping, if its rule have multiple corresponding RuleNames, you repeat each rule for each corresponding rule name.

Mappings:
{{Input}}

Tool Information:
{{tool}}

Response Format: No explanation. If a mapping does not exist, delete the mapping give "None". If there is no corresponding mapping, The answer is No.
Analysis: Give detailed analysis
**Answer:** Respond Yes or No whether there are are mappings.
**Mapping:** 
1. XXX
>>>
..
'''
    '''...
For example, 
1. Mandatory: Number of [BlankLine] between [Sections] = 1 
   >>> 
   RuleName: padding-line-between-statements
   Option Rule: 
     option 1: No Option Name; object; {"blankLine": "always", "prev": "section", "next": "section"}
       suboption 1.1: blankLine; "always"; Mandatory: [Blank Line] between "section" and "section"
       suboption 1.2: prev; "section"; Defines the type of the preceding statement
       suboption 1.3: next; "section"; Defines the type of the following statement

2. Optional: Number of [BlankLine] before [FileImplementation] is [1, 2] 
   >>> 
   RuleName: padding-line-between-statements
   Option Rule: 
     option 1: No Option Name; object; {"blankLine": "any", "prev": "*", "next": "FileImplementation"}
       suboption 1.1: blankLine; "any"; Optional: [Blank Line] before "FileImplementation"
       suboption 1.2: prev; "*"; Defines the type of the preceding statement
       suboption 1.3: next; "FileImplementation"; Defines the type of the following statement

3. Optional: [ColumnLimit] of [goog.provide, goog.require] is not [80]
   >>> 
   RuleName: max-len
   Basic Rule: Mandatory: [Line Length] is [Maximum] [Unicode Characters]
   Option Rule: 
     option 1: code; 80; Optional: [Line Length] is not {{code}} [Unicode Characters]

According to Tool Information, Since "section" of prev option names are not in value range of prev, "FileImplementation" of next option names are not in value range of next, so we delete these mappings.
We delete the two mappings, there are only one mapping, the response are as follows: 

**Answer:** Yes
**Mapping:** 
1. Optional: [ColumnLimit] of [goog.provide, goog.require] is not [80]
   >>> 
   RuleName: max-len
   Basic Rule: Mandatory: [Line Length] is [Maximum] [Unicode Characters]
   Option Rule: 
     option 1: code; 80; Optional: [Line Length] is not {{code}} [Unicode Characters]'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Input}}", text)
    prompt = prompt.replace("{{tool}}", tool)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt

def extract_config_promt(text: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Excerpt Mappings from the following text without altering their content in any way. Only perform the extraction.
Note: For each mapping, if its rule have multiple corresponding RuleNames, you repeat each rule for each corresponding rule name.
Delete mappings where the set option values are outside the valid option value range.
             
Text:
{{Input}}

Response Format: No explanation. If a mapping does not exist, delete the mapping give "None". If there is no corresponding mapping, The answer is No.
**Answer:** Respond Yes or No whether there are are mappings.
**Mapping:** 
1. XXX
>>>
..

...
For example, 
if Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] have two corresponding rulenames,
1. Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] 
   >>>
   RuleName: SummaryJavadoc
   Basic Rule:
   Mandatory: [Javadoc summary sentence] not have [forbidden phrases]

   If no option rule, respond with "Option Rule: None", else:
   Option Rule:
   forbiddenSummaryFragments option: Pattern; regular expression;
   forbiddenSummaryFragments >>> Mandatory: {{forbiddenSummaryFragments}} not in [Javadoc summary sentence]

   RuleName: AnotherRuleName
   Basic Rule:
   Mandatory: XXXXX

   If no option rule, respond with "Option Rule: None"
   Option Rule: None


You should respond like the following  
**Answer:** Yes
**Mapping:** 
1. Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] 
   >>> 
   RuleName: SummaryJavadoc
   Basic Rule:
   Mandatory: [Javadoc summary sentence] not have [forbidden phrases]

   Option Rule:
   forbiddenSummaryFragments option: Pattern; regular expression;
   forbiddenSummaryFragments >>> Mandatory: {{forbiddenSummaryFragments}} not in [Javadoc summary sentence]

2. Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] 
   >>> 
   RuleName: AnotherRuleName
   Basic Rule:
   Mandatory: XXXXX
'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Input}}", text)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def extract_non_empty_config_promt(text: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Extract all Mappings whose RuleName exists from the following Mappings. \
Note change extracted Mapping numbers to consecutive!

Mappings:
{{Input}}

Response Format: No explanation. If a mapping whose RuleName is not existed, delete the mapping.
**Answer:** Respond Yes or No whether there are mappings whose RuleName exists
**Mapping:**
...
For example, 
for the following mappings
1. Optional: [BlankLine] if [ImprovesReadability]**
   >>> 
   None
2. Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] 
   >>> 
   RuleName: SummaryJavadoc
   Basic Rule:
   Mandatory: [Javadoc summary sentence] not have [forbidden phrases]

   Option Rule:
   forbiddenSummaryFragments option: Pattern; regular expression;
   forbiddenSummaryFragments >>> Mandatory: {{forbiddenSummaryFragments}} not in [Javadoc summary sentence]

You should respond like:
**Answer:** Yes
**Mapping:** 
1. Mandatory: [SummaryFragment] does not begin with [SpecificPhrase] and is not [CompleteImperativeSentence] 
   >>> 
   RuleName: SummaryJavadoc
   Basic Rule:
   Mandatory: [Javadoc summary sentence] not have [forbidden phrases]

   Option Rule:
   forbiddenSummaryFragments option: Pattern; regular expression;
   forbiddenSummaryFragments >>> Mandatory: {{forbiddenSummaryFragments}} not in [Javadoc summary sentence]
'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Input}}", text)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def extract_merge_mappings_promt(text: str, answer_map: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''For the following Mappings, before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. 
For each mapping, You based on the following New ToolSEM rule mapping, replace ToolSEM rule with only rule name and new ToolSEM rule in Mappings. \

Mappings:
{{answer_map}}

New ToolSEM rule mapping:
{{Input}}

Response Format: No explanation. 

**Mapping:**
1. StyleSEM rule
>>>
Rule Name
new ToolSEM rule 1

2. StyleSEM rule
>>>
Rule Name
new ToolSEM rule 2

...

For example, 
for the following new ToolSEM rule mappings

1. **XXX**
   >>> 
   **Mandatory: [empty line separator] before [fields, constructors, methods, nested classes, static initializers, instance initializers]**

   **Explanation:**
   - **Basic Rule:** Requires an empty line separator before various class members such as fields, constructors, methods, etc.
   - **Option Rule:** Specifies the tokens (FIELD_DEF, CTOR_DEF, etc.) for which the empty line separator is mandatory.
   - **Rule Type:** Since both the basic rule and the option rule are "Mandatory," the new ToolSEM rule is also "Mandatory."
   - **New ToolSEM Rule:** The rule mandates an empty line separator before specified class members, ensuring clarity and separation in code structure.

2. **XXX**
   >>> 
   **Optional: [no empty line] between [fields]**

   **Explanation:**
   - **Option Rule:** Allows no empty line between fields, implying that fields can be consecutive without separation.
   - **Rule Type:** The rule type is "Optional" as specified in the option rule.
   - **New ToolSEM Rule:** This rule permits fields to be listed consecutively without requiring an empty line between them, allowing for more compact code formatting if desired.

You should respond like:
**Mapping:** 
1. Mandatory: [BlankLine] between [ConsecutiveMembers] or [Initializers] of [Class] : [fields, constructors, methods, nested classes, static initializers, and instance initializers]
   >>> 
   RuleName: XXX
   Mandatory: [empty line separator] before [fields, constructors, methods, nested classes, static initializers, instance initializers]

2. Optional: [BlankLine] between [two consecutive fields] : not have [other code] between [two consecutive fields]
   >>> 
   RuleName: XXX
   Optional: [no empty line] between [fields]

3. Optional: [MultipleConsecutiveBlankLines] are permitted
   >>> 
   RuleName: XXX
   Optional: [multiple empty lines] between [class members]
 '''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{Input}}", text)
    prompt = prompt.replace("{{answer_map}}", answer_map)

    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def validation_config_superset_semantics(mapping: str, style="RuleSet of Google Java Style Guide", DSL_Syntax="",
                                         tool="Checkstyle",
                                         toolruleset=None, grammar="Grammar", example=""):
 #    ''' - When comparing, consider the definitions of JavaScriptTerms and account for synonym relationships where applicable.
 # - Condition 1: If their semantics and object scope enclosed with "[]" are identical, the mapping result is Yes. Otherwise, proceed to the next substep - .
 # - Condition 2: Or the description of ToolSEM explicitly and obviously describe StyleSEM, the mapping result is Yes. Otherwise, proceed to the next substep -
 # - Condition 3: Or If semantics and object scope enclosed with "[]" of ToolSEM is more narrower than the semantics and object scope of StyleSteM, the mapping result is Yes.
 # - Otherwise, the mapping result is No.'''
    prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:

For each mapping, do the following steps: Step 1 ~ Step 2.

Step 1: Compare the rule type :

 - If the rule types are the same (both "Optional" or both "Mandatory"), proceed to Step 2.
 - If the rule types are different, the mapping result must be No.

Step 2: Compare Semantics: Think step by step, not only comparing object scope, but also comparing the actions or restrictions applied to the objects!
 - Think step by step, not only comparing object scope, but also comparing the constraints or behavior semantics applied to the objects!
 - When comparing, consider the domain knowledge and recognize synonym relationships between JavaScriptTerms where applicable. 
 - Similar object scope, such as adjectives like 'Legacy' or 'Complex', are superficial and should be ignored, as they do not change the underlying meaning, making them synonyms.
 - Condition 1: If their object scope, and the constraints or behavior semantics applied to the objects are both identical, the mapping result is Yes. Otherwise, proceed to Condition 2 .
 - Condition 2: Or From ToolSEM, if removing some objects enclosed with "[]" in ToolSEM, their object scope, And the constraints or behavior semantics applied to the objects are both identical, the mapping result is Yes. Otherwise, proceed to Condition 3.
 - Condition 3: Or If the object scope specified by ToolSEM is narrower than that of StyleSEM, And their constraints or behavior semantics applied to the objects are identical, the mapping result is Yes. 
 - If all three conditions are not satisfied, the mapping result must be No. 

Note for Comparison:
1. When comparing, consider the definitions of JavaScriptTerms and account for SYNONYM relationships where applicable. 

{{Mapping}}

Response Format:
Analysis: ... 
Mapping 1: Yes or No

Analysis: ... 
Mapping 2: Yes or No

For example, for comparing semantics: 

1. Mandatory: [Symbols] imported via [NamedImport] is [SameName]  
   >>>  
   RuleName: no-useless-rename  
   Mandatory: No [Renaming] of [import], [export], and [destructured assignments] to the same [name]
example 1: **Step 2: Compare Semantics:**
  - StyleSEM: [Symbols] imported via [NamedImport] is [SameName]  
  - ToolSEM: No [Renaming] of [import], [export], and [destructured assignments] to the same [name]
  - StyleSEM focuses on on preserving the same names during imports, whereas ToolSEM prohibits renaming with same name during imports
  - Semantics of StyleSEM and ToolSEM are totally different semantics. 
  - so, condition 1 and condition 2 and condition 3 all not satisfy.
  - so, the mapping result is No.
  
2. Mandatory: [Indent Level] applies to [Code, Comments] throughout [Block]
   >>>  
   RuleName: ident
   Mandatory: Consistent [Indentation] including [comments]

example 2:  **Step 2: Semantics Comparison:**
   - StyleSEM: [Indent Level] applies to [Code, Comments] throughout [Block]
   - ToolSEM: Consistent [Indentation] including [comments]
   - **StyleSEM:** Applies to both **Code** and **Comments** within a **Block**.
   - **ToolSEM:** Mentions **Indentation** including **comments**, implicitly covering **Code** as well since indentation typically applies to code blocks.
   - **Constraints/Behavior Semantics:**
      - Both rules enforce **consistent indentation** for the specified objects.
   - **Condition 1:** The object scope (**Code** and **Comments**) and the action (**consistent indentation**) are identical in both rules.
   - so, the Condition 1 is satisfied,Mapping result: Yes


3. Mandatory: No [DefaultExports] is [Used]
   >>>  
   RuleName: no-restricted-exports
   Mandatory: No [specified names] and [export default] declarations in [exports]

example 3: Step 2: Compare Semantics:
  - StyleSEM: No [DefaultExports] is [Used]
  - ToolSEM: No [specified names] and [export default] declarations in [exports]
  - **Condition 1:** The object scopes are not identical (`[DefaultExports]` vs. `[specified names]` and `[export default] declarations`), so this condition is not met.  
  - **Condition 2:**  
  - **ToolSEM after removing `[specified names]`:** Prohibits only `[export default]` declarations in `[exports]`.  
  - **Comparison with StyleSEM:** Now, both StyleSEM and the modified ToolSEM prohibit default exports.  
  - **Assessment:** The object scope and behavior semantic are identical after removal. → **Condition 2 satisfied.**
  - so the mapping result is Yes

4. Mandatory: if [FunctionArguments] exceed [80ColumnLimit] then [FunctionArguments] must be [LineWrapped] in [ReadableWay]
   >>>  
   RuleName: max-len
   Mandatory: [Line Length] is 80 [Unicode Characters]
example 4: **Semantics Comparison:**   
   - StyleSEM: if [FunctionArguments] exceed [80ColumnLimit] then [FunctionArguments] must be [LineWrapped] in [ReadableWay]
   - ToolSEM: [Line Length] is 80 [Unicode Characters]
    - **Condition 1:**  
    - **StyleSEM:** Targets `[FunctionArguments]` exceeding `[80ColumnLimit]` and requires them to be `[LineWrapped]` in a `[ReadableWay]`.  
    - **ToolSEM:** Enforces a `[Line Length]` of `80 [Unicode Characters]`.  
    - The object scopes differ: StyleSEM specifically addresses function arguments, while ToolSEM applies to all lines.  
    - **Condition 1:** Not satisfied.
  - **Condition 2:**  
    - Removing objects in ToolSEM leaves `[Line Length] is 80 [Unicode Characters]`, which still does not match the specific focus on `[FunctionArguments]` in StyleSEM.  
    - **Condition 2:** Not satisfied.
  - **Condition 3:**  
    - ToolSEM's scope (`[Line Length]`) is broader, not narrower, than StyleSEM's focus on `[FunctionArguments]`.  
    - **Condition 3:** Not satisfied.
   - Therefore, the mapping result is No.

5. Mandatory: [ModuleImportName] is [LowerCamelCase]
   >>>  
   RuleName: camel-case
   Mandatory: [ImportVariableName] is [CamelCase]
example 5: **Step 2: Compare Semantics:**
  - StyleSEM: [ModuleImportName] is [LowerCamelCase]
  - ToolSEM: [ImportVariableName] is [CamelCase]
  - **Object Scope Comparison:**
   - **StyleSEM:** `[ModuleImportName]` refers to the name used when importing a module.
   - **ToolSEM:** `[ImportVariableName]` also refers to the name used for the import variable.
   - These terms are synonymous, indicating the same object scope.
  - **Naming Convention Comparison:**
   - **StyleSEM:** Specifies `[LowerCamelCase]`, where the first letter is lowercase (e.g., `myModule`).
   - **ToolSEM:** Specifies `[CamelCase]`, which typically starts with an uppercase letter (e.g., `MyModule`).
   - The naming conventions are different; one starts with a lowercase letter while the other starts with an uppercase letter.
 - Since the **object scope** is identical but the **naming conventions** differ, the semantics are not fully aligned.
 - Therefore, the mapping result is No.
'''
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{style}}", style)
    prompt = prompt.replace("{{Mapping}}", mapping)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def validation_config_superset_objects(mapping: str, style="RuleSet of Google Java Style Guide", DSL_Syntax="",
                                       tool="Checkstyle",
                                       toolruleset=None, grammar="Grammar", example=""):
    prompt = r'''each mapping format: 
StyleSEM
>>>
ToolSEM

0. Independently extract a JavaTerm enclosed with "[]" from both StyleSEM and ToolSEM that represents the context of subjects each rule checks (e.g., "of [XXX]", "for [XXX]").
1. Only Check if the extracted JavaTerm of StyleSEM rule checks is narrower than the extracted JavaTerm of ToolSEM rule checks. If StyleSEM is more narrower, the answer of the mapping is No! Otherwise, the answer of the mapping is Yes! 
2. 在比较时，需结合注意JavaTerms enclosed with "[]" 之间的定义和同义词

任务要求：
对每个 Mapping，只需要抽取一个JavaTerms 范围关系进行比较。
不需要比较 其他JavaTerms和 JavaTerms外的其他规则，仅基于范围关系作出判断。

{{Mapping}}

Response Format:
Explanation: ... 
Mapping 1: Respond with Yes or No 

Explanation: ... 
Mapping 2: Respond with Yes or No

...

For example, for the following Mapping, 
1. Mandatory: No [TabCharacter] for [Indentation]  
   >>>  
Mandatory: No [tab character] in [each line of source code]

2. Mandatory: Number of [TopLevelClass] in [SourceFile] = 1  
   >>>  
Mandatory: [source file] contains exactly 1 [top-level class, interface, enum, or annotation] 

Explanation:
    - StyleSEM 的 [TabCharacter] 仅针对 [Indentation]，而 ToolSEM 的 [tab character] 涉及 [each line of source code]。
    - [Indentation] 是 [each line of source code] 的子集，范围更小。
    - 因此，StyleSEM 的范围更具体，The Answer is No。
Mapping 1: No

Explanation: 
    - StyleSEM 的 [TopLevelClass] 仅指类，而 ToolSEM 的 [top-level class, interface, enum, or annotation] 包括类、接口、枚举和注解。
    - [TopLevelClass] 是 ToolSEM 定义的 [top-level class, interface, enum, or annotation] 的子集，范围更小。
    - 因此，StyleSEM 的范围更具体，The Answer is No。
Mapping 2: No'''
    r'''2. Optional: [ColumnLimit] is [100] not for [ImportStatement]  
   >>>  
   Optional: No [Line] longer than [100], except for lines matching [^import\s+.*;] 
   3. Optional: [ColumnLimit] is [100] not for [PackageStatement]  
    >>>  
Optional: No [Line] longer than [100] except for lines matching [^package\s+.*;]'''

    r'''Mapping 3: Yes Explanation: The StyleSEM rule indicates that the [ColumnLimit] is [100] but does not apply to [PackageStatement], while the ToolSEM rule specifies that no [Line] should be longer than [100], except for lines matching the pattern [^package\s+.*;]. Both rules effectively exempt PackageStatement from the column limit, making their subjects equivalent in scope. Hence, the answer is Yes, as the subject of the StyleSEM rule is not narrower than that of the ToolSEM rule.'''
    '''3. Mandatory: No [LineBreaks] is [LineWrapping]  
   >>>  
   Mandatory: No [line wrap] for [IMPORT] and [PACKAGE_DEF] statements
   {{grammar}}
{{Syntax}}'''
    '''Mapping 2: No Explanation: The StyleSEM rule mandates that no [BlockTags] have [EmptyDescription], which applies to all block tags. The ToolSEM rule specifies that a [block tag] must be followed by a [description] for specific tags: {PARAM_LITERAL, RETURN_LITERAL, THROWS_LITERAL, DEPRECATED_LITERAL}. Since the ToolSEM rule is limited to these specific tags, the subject of the StyleSEM rule is broader, covering all block tags. Therefore, the mapping does not hold, and the answer is No.'''
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{style}}", style)
    prompt = prompt.replace("{{Mapping}}", mapping)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def merge_basic_option_rules(answer_map):
    prompt = '''For the following ToolSEM rules, 

For each ToolSEM rule consisting of Rule Names and the **Basic Rule** and the **Option Rules** with specific option values, let's break down and combine setting option values of each ToolSEM rule to derive only one new ToolSEM rule begin with "Mandatory:" or "Optional:" using given grammar.
Do not forget using the specific option values to express new ToolSEM rule.

**Note: For the rule type of new ToolSEM rule, extract rule types of Option Rules and Basic Rule**
**if rule types of Option Rules and Basic Rule have at least one "Optional", the rule type of new ToolSEM rule must be "Optional". Otherwise, it is "Mandatory".**

Ensure new ToolSEM rule is clearer and aligns more accurately with rule details of old ToolSEM rule! Avoid ambiguous wording.

new ToolSEM rule should not be impacted by StyleSEM!!!

{{answer_map}}    

Grammar:
RuleSet   ::= Rule1 ['And' | 'Or' | ';' Rule2]*  # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.

Rule   ::= ['Optional:' | 'Mandatory:'] [Constraint] # 'Mandatory' means constraint must be satisfied, 'Optional' means constraint may be satisfied or not be satisfied, or not applied the constraint 

Constraint   ::= TermList [Operator TermList]+ # TermList [Operator TermList]+ means the relationship of multiple TermList should satisfy
             | 'No' TermList [Operator TermList]+ # 'No' TermList means Prohibits TermList [Operator TermList]+;
             | 'Order of' TermList ['is'| 'is not'] TermList # 'Order of' means order of TermList is TermList
             | 'Order' ['is'| 'is not'] TermList # 'Order' means order rule is TermList
             | 'Number of' TermList [Operator TermList]* #'Number' means numberConstraint
             | TermList ['before'|'after'|'between'|'not before'|'not after'|'not between'|Operator TermList]* | 描述实体的结构组成，表示一个实体中 必须\建议 （禁止）包含另一个实体（表示对实体的内部需求）描述实体的结构组成，表示一个实体中 必须\建议 （禁止）包含另一个实体（表示对实体的内部需求）
             | TermList ['have'|'not have' TermList]* | 包含关系 描述实体的结构组成，表示一个实体中 必须\建议 （禁止）包含另一个实体（表示对实体的内部需求）描述实体的结构组成，表示一个实体中 必须\建议 （禁止）包含另一个实体（表示对实体的内部需求）
             | TermList ['is'|'is not' TermList]* | 属性限定关系 "描述对实体的属性的值的要求，表示如果某种代码实体的属性有多个选项时， 在使用属性的选项时 必须\建议 使用某种特定的选项 属性包括：命名风格、字符编码方式、文件编码方式、缩进方式、行尾空白类型、注释格式、特殊字符使用方式（如非 ASCII 字符）、缩写规范等。"
             | 'if' Rule1 'then' Rule2 # means Implied Relation Rule2 must be adhered to under the premise of Rule1 

Operator   ::= [.]+ (e.g., 'is' | 'is not' | 'have' | 'after' |  '=' | 'Add ' | '...' ) 

TermList   ::= Term [', '|' and '|' or ' Term]* 

Term   ::= '[' JavaScriptTerm ']' #Note: JavaTerm represents terminology of Java programming language; 
        | Modifier* Term 
        | Term 'of' Term 

Modifier   ::= Word (e.g., 'some' | 'each' | 'all' | 'first' | 'last' | '...') 

Word   ::= [a-zA-Z]+ 

JavaScriptTerm   ::= [.]+ 

Note: JavaScriptTerm represents terminology of JavaScript programming language; 
'.' means to match any single character except for newline;
'...' indicates that more words can be included if needed; 
'*' means zero or more repetitions;
'+' means one or more repetitions.


Response Format:
**Mappings:**
1. old ToolSEM rule
   >>>
   New ToolSEM rule starting with "Mandatory" or "Optional"

Explanation: ...

2. old ToolSEM rule
   >>>
   New ToolSEM rule starting with "Mandatory" or "Optional"

Explanation: ...

3. ...
    '''
    prompt = prompt.replace("{{answer_map}}", answer_map)

    return prompt


def extract_merge_mapping_result(mapping="", correct_information=""):
    '''3. from Analysis of Mappings, extract whether there is a situation violate the ToolSEM rule, but does not violate the StyleSEM rule.
    3.1 If 存在这样的情况或对象, 则Answer is "No".
    3.2 否则 进行step 4.
4. from Analysis of Mappings, extract the scope relationship between  StyleSEM rule and ToolSEM rule.
    4.1 If the scope of the StyleSEM rule is narrower than the scope of the ToolSEM rule, your Answer is "No".
    4.2 Otherwise, Answer is "Yes".''''''3. from Analysis of Mappings, extract the scope relationship between  StyleSEM rule and ToolSEM rule.
    3.1 If the scope of the StyleSEM rule is narrower than the scope of the ToolSEM rule, your Answer is "No".
    3.2 Otherwise, Answer is "Yes".'''
    prompt = '''Determine Results of each Mapping from the following Mappings and the Analysis of the following Mappings \

For each Mapping, determine answer is "Yes" or "No" based on the step 1 ~ step 3.

1. If rule types of  StyleSEM (Set A) and ToolSEM (Set B) is different like one is "Mandatory", the other is "Optional". The Answer is "No". Otherwise, proceed to Step 2.
2. From the Analysis of Mappings, extract semantic similarity between StyleSEM (Set A) and ToolSEM (Set B). If semantic of StyleSEM (Set A) and ToolSEM (Set B) is similar, proceed to Step 3. Otherwise, Answer is "No".
3. From the Analysis of Mappings, extract if subjects of StyleSEM rule checks is narrower than subjects of ToolSEM rule checks. If is not narrower, the Answer is "Yes", otherwise, the Answer is "No".



Mapping:
{{mapping}}

Analysis of Mappings:
{{correct_information}}

Response Format: 
Mapping 1: Yes or No. Analysis: detailed analysis for step 1 ~ step 4
Mapping 2: ...
'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{mapping}}", mapping)
    prompt = prompt.replace("{{correct_information}}", correct_information)
    prompt = prompt.replace("{{res}}", res)

    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def extract_correct_mapping(mapping="", correct_information=""):
    res = "Yes"

    '''for the following mapping, we give the results of each mapping 在下面的Result of Mappings, 你只提取Mappings whose results are "{{res}}"'''
    '''Only Extract Mappings whose results are "{{res}}" based on the Relationship of Mappings. '''
    prompt = '''
For the following Mapping, we provide the results of each mapping. Extract only the mappings from the following "Mapping" with results "{{res}}" based on the "Results of Mappings" below.
Do not need to give basic rules.

Mapping:
{{mapping}}

Results of Mappings:
{{correct_information}}

Response Format: No explanation. If no mappings whose results is "{{res}}", directly give "NONE". Otherwise, only keep mappings whose results is "{{res}}".
Answer: Respond Yes or No whether there are are mappings whose results are "{{res}}".
**Mapping:**
1. Rule 1 of Google Java Style Guide 
>>>>
    RuleName1: <give the RuleName>
    option 1: <give the option name, option value and option rule>
    option 2: <give the option name, option value and option rule>
    ...
    option k: ..

    RuleName2: <give the RuleName>
    option 1: <give the option name, option value and option rule>
    option 2: <give the option name, option value and option rule>
    ...
    option k: ..

...

2. Rule k of Google Java Style Guide
>>>>
    RuleName1: <give the RuleName>
    option 1: <give the option name, option value and option rule>
    option 2: <give the option name, option value and option rule>
    ...
    option k: ..

For example, 
For the following Mapping and Relationship of Mapping,
**Mapping:**
1. Mandatory: [ClassName] is [UpperCamelCase]
   >>> 
   RuleName: TypeName
   Basic Rule: Mandatory: [type names] conform to [specified pattern]
   Option Rule:
   option 1: format; "^[A-Z][a-zA-Z0-9]*$"; Mandatory: [type names] match {{format}}
   option 2: tokens; "CLASS_DEF"; Mandatory: [type names] of {{tokens}} conform to [specified pattern]

   RuleName: XXXX
   Option Rule:
   option 1: XXXX

2. Optional: [ClassName] is [NounPhrase]
   >>> 
   RuleName: TypeName
   Basic Rule: Optional: [type names] conform to [specified pattern]
   Option Rule:
   option 1: format; "^[A-Z][a-zA-Z0-9]*$"; Optional: [type names] match {{format}}
   option 2: tokens; "CLASS_DEF"; Optional: [type names] of {{tokens}} conform to [specified pattern]
Let's analyze each mapping according to the provided rules and determine the relationship between the StyleSEM and ToolSEM rules.

**Mapping 1:**
- **StyleSEM:** Mandatory: [ClassName] is [UpperCamelCase]
- **ToolSEM:** RuleName: TypeName; Basic Rule: Mandatory: [type names] conform to [specified pattern]; Option Rule: format; "^[A-Z][a-zA-Z0-9]*$"; Mandatory: [type names] match {{format}}

Analysis: The StyleSEM rule specifies that class names must be in UpperCamelCase, which aligns with the ToolSEM rule that requires type names to match a specific pattern starting with an uppercase letter. Both rules essentially enforce the same naming convention for class names.

Mapping 1: Yes

---

**Mapping 2:**
- **StyleSEM:** Optional: [ClassName] is [NounPhrase]
- **ToolSEM:** RuleName: TypeName; Basic Rule: Optional: [type names] conform to [specified pattern]

Analysis: The StyleSEM rule suggests that class names should be noun phrases, which is a semantic guideline rather than a strict pattern. The ToolSEM rule provides an optional pattern for type names but does not specifically enforce the use of noun phrases.

Mapping 2: No

You should repsond lik this:
Answer: Yes
**Mapping:**
1. Mandatory: [ClassName] is [UpperCamelCase]
   >>> 
   RuleName: TypeName
   Option Rule:
   option 1: format; "^[A-Z][a-zA-Z0-9]*$"; Mandatory: [type names] match {{format}}
   option 2: tokens; "CLASS_DEF"; Mandatory: [type names] of {{tokens}} conform to [specified pattern]

   RuleName: XXXX
   Option Rule:
   option 1: XXXX
'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{mapping}}", mapping)
    prompt = prompt.replace("{{correct_information}}", correct_information)
    prompt = prompt.replace("{{res}}", res)

    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def gen_config_format(mapping="", tool="ESLint", format="JSON"):
    prompt = '''Based on the following Mapping, generate {{tool}} configuration in {{format}} format based on the following step 1 ~ step 3.

before ">>>" is rule of {{style}}, after ">>>" is the corresponding rule from {{tool}} consisting of basic rule consisting of RuleName, Option rule consisting of option k: option names, option values and option rules starting with "Mandatory:" or "Optional".

1. Only List all rule names, option names and option values which corresponding to {{format}} configuration with module name, option name and option value from all mappings. Skip all rules like option rules or basic rules
2. Extract all same rule names or module names to merge,
    - if same rule names that do not have same option name or without option names, merge these same rule names into one configuration.
    - if there are same option names, if the option values do not conflict, merge them into one configuration. Note values of regular expression or sequence-like data type can be merged.
    - Otherwise, same module names should be individual configurations.
3. For the final Configuration, must add "error" to the first value of each rule name, like  'rulename': ['error', ...]
4. If there are option name and option value, the option name is the key, the option value is value,  like  'rulename': ['error', "option name": option value]
5. If there are option name and option value is object, the option name is the key, the option value is a dict,  like  'rulename': ['error', "option name": {option value}]
6. If there are no option name and option value is not object, you can directly write the option value,  like  'rulename': ['error', option value]
7. If there are no option name and option value is object, you can direct write the option value,  like  'rulename': ['error', {option value} ]

Mapping:
{{mapping}}

Response Format: If there is no mapping, directly give "NONE"

Analysis: Give explanation

Answer: Respond Yes or No about whether there are configurations.

Configuration:
{
'rulename1': ['error', if no option name option value or {"option name": option value} or {"option name" : { "suboption name" : "suboption value", ..., }} or if no option name { "suboption name" : "suboption value", ..., }] , 
'rulename2': ['error', ...] ,
...
}

For example, for the following mapping,
**Mapping:**
1. Mandatory: [JSDoc] have [Classes, Fields, Methods]  
   >>>  
   RuleName: require-jsdoc   
   Option Rule:  
   option 1: require; object; {"ClassDeclaration": true, "MethodDefinition": true}  
   - suboption 1.3: ClassDeclaration; true >>> Mandatory: [JSDoc Comment] for [ClassDeclaration]  
   - suboption 1.2: MethodDefinition; true >>> Mandatory: [JSDoc Comment] for [MethodDefinition]  

2. Mandatory: Order of [Lines] is [AlphabeticalUppercaseFirst] >>>  
   RuleName: sort-keys  
   Option Rule:  
   option 1: No Option Name; "asc"; Mandatory: Order of [Properties] is [Ascending]  
   option 2: caseSensitive; true; Mandatory: Order of [Properties] is [Case-Sensitive]  
 
3. Optional: if [someObjectOrPrimitive] == [null] then [someObjectOrPrimitive] is [null] or [undefined]
   >>> 
   RuleName: eqeqeq
   Option Rule: 
     option 2: null; ignore; Optional: [===] or [!==] not applied to [null]
Analysis: All rule names, option names and option values are as following:
RuleName: require-jsdoc
option 1: require; {"ClassDeclaration": true, "MethodDefinition": true};
    - suboption 1.3: ClassDeclaration; true  
    - suboption 1.2: MethodDefinition; true

RuleName: sort-keys
option 1: No Option Name; "asc";
option 2: caseSensitive; true;

RuleName: require-jsdoc
option 1: require; {"FunctionExpression": false};
    - suboption 1.5: FunctionExpression; false  

Since there are two mappings whose rulenames are same but option name are not same (require-jsdoc), so we can merge them into one (require-jsdoc).

Answer: Yes

Configuration:  
{ 'require-jsdoc': ['error', "require": { "ClassDeclaration": true, "MethodDefinition": true, "FunctionExpression": false }],
'sort-keys': ['error', "asc", "caseSensitive": true],
'eqeqeq': ['error',"null": "ignore"]
}
'''
    # '''
    # example=''''''
    # prompt = prompt.replace("{{Example}}", example)
    prompt = prompt.replace("{{mapping}}", mapping)
    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{format}}", format)

    # prompt = prompt.replace("{{correct_information}}", correct_information)
    # prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    # prompt = prompt.replace("{{Description}}", rule)
    # prompt = prompt.replace("{{grammar}}", grammar)

    return prompt


def extract_specific_config_promt(text: str, format: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Only excerpt {{format}} configurations from the following Results, do not change the content! Respond based on the Response Format. \
If there are same rulenames, remove other same rulenames and only keep the first.

Results:
{{Input}}

Response Format: No explanation. If there is no specific configuration, directly give "None".
Answer: Respond with Yes or No about whether there are configurations.
Configuration: Respond with {{format}} configurations.
...
'''
    prompt = prompt.replace("{{format}}", format)
    prompt = prompt.replace("{{Input}}", text)
    return prompt


def get_all_gpt_res_for_java_checkstyle(gpt_answer_dir, rule_list, DSL_Syntax=None,
                                        style="RuleSet of Google JavaScript Style Guide",
                                        tool="ESLint",
                                        toolruleset=None, grammar="Grammar", example="", model="gpt-4o"):
    agent = GPTAgent()

    for ind, rule_description in enumerate(rule_list[:]):
        # if ind < 5: #>=
        #     continue

        # if ind in [6,8,11,42,49,50,51,52,55,56,57,66]:# 4,11 6,7,36, 52,53 14,48 [4,11,17,26,32,34,41,42,43,44,47]:# 4,11 6,7,36, 52,53 14,48 [3,5,7,9,14,16,17,27,29,32,34,41,51,52,53]:#6,7,36, 52,53 ,4,14,29,34,51,52,54,62,65,
        #     continue
        # '''
        # if ind not in [3,7,11,12,16,17,19,21,22,26,28,30,32,36,38,39,41,43,44,47,51,52,53,56,58,59,61,64,66,68,69,72,73,74,76,77,80,81,82]:# 43, 4,11 6,7,36, 52,53 14,48
        #     continue

        # '''
        # if ind not in [32,36,38,43]:  #17,26, 7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [3,33,36,37,39,41,43,44,47,48,49,52,53,55]:  # 7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [37,39,43, 44, 45, 47,48,49]+[47,49]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [3,16,19,33, 2,12,15,19,28,29]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue

        # if ind not in [12,15,16,19,28,29,33]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [60,61,62,63,65,66,68,69,73,74,76,77,80,81,84,88,90,92]:  #41,42,51,53,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [7,12,16,17,28,36,40,41,44,46,48,49]:  #41,42,51,53,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue

        # if ind not in [140,141,143,145,146,148]:  #41,42,51,53,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [95]:  #41,42,51,53,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        #
        # if ind not in [2,12,15,19,28,29,47,49]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [42]:  # 7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [43, 44]:  # 7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [120]:#[33,44,45,72,77,94,104,117,118]: json format fix #[60,61,62,63,66,68,69,73,74,76,77]
        #     continue
        # if ind not in [3,7,11,12,36,38,39,44,47,49]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        # # if ind not in [3,36,38,49]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [51,52,58,59,60,61,63,70,72,73,74,77,80,81,82,83]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        # # if ind not in [3,36,38,49]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [59,61,63,74,81]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        # if ind not in [3,12,17,22,32,36]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind<=36:
        #     continue
        # if ind not in [3,12,17,22,32,36,44,46,48,51,53,57,58,63,64,69,72,73,74,77,80,82,83,85,88,89]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [126,143]:#这个是merge 错误[84,92,94,95]:#[104,105,111,119,127,143,146]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [143]:  # 这个是merge 错误[84,92,94,95]:#[104,105,111,119,127,143,146]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [3, 12, 17, 22, 32, 36, 44, 46, 48, 51, 53, 57, 58, 63, 64, 68, 69, 72, 73, 74, 77, 80, 81, 82,
        #                83, 85, 88, 89, 91, 92, 94, 95, 104, 105, 106, 118, 119, 123, 126, 127, 128, 129, 133, 143, 146,
        #                147]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind in [3, 12, 29, 32, 52, 60, 63, 64, 69, 70, 77,80, 81, 85, 87, 88, 89, 91,
        #                94, 95, 97, 98, 101, 104, 117,119, 125,127, 128, 129, 133, 134,
        #                 146,147,148]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [5,11,17,22,30,38,44,47,49,53,58,64,69,77,
        #                80,81,87,88,89,94,97,98,101,103,104,117,119,125,
        #                127,128,129,133,134,146,]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue

        # if ind not in [47,97,98]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [38,64,94]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind in [11,44,104,119,125,129,133]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [3,5,28,29,33,38,44,49,56,63,64,69,72,73,
        #            74,77,80,82,88,90,91,93,94,95,96,101,103,104,
        #            109,120,125,129,133,141,143,145,146]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind in [33,38,44,49,56,63,64,69,72,73,
        #            74,77,80,82,88,90,91,93,94,95,96,101,103,104,
        #            109,120,125,129,133,141,143,145]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [ 33, 38, 44, 49, 56, 63, 64, 69, 72, 73,
        #            74, 77, 80, 82, 88 ]:  # 3, 5,  41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        if ind not in [5,16,29,30,38,40,41,43,49,51,60,63,72,73,77,80,82,87,88,90,92,96,98,103,106,
                       109,111,112,125,126,127,129,131,133,134,144]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
            continue

        if ind in [103,106,109,
                       111,112,125,126,127,129,131,133,134,144]:  # 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
            continue
        # if ind not in [134]:  # 96 add other 多余的option rule 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [126]:  # 96 add other 多余的option rule 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [111]:  # 96 add other 多余的option rule 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [106]:  # 96 add other 多余的option rule 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind not in [96]:  # 96 add other 多余的option rule 41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue


        # 146,
        # semantic error, 没有严格按照步骤走 134
        # set option name, rule 错误 133 [ParameterTypes, ReturnTypes] have [@param, @return] or [InlineAnnotations]
        '''
        108 代码metrics bug
        84
        
        80 dsl 生成 》》》 arrow-parens; arrow-body-style
        81 应该是对的，查下怎么回事呢
        119 format error
        97 format error "eqeqeq": ["error", "smart", "ignore"]
        117 错误把ToolSEM的rule放入到StyleSEM rule Mandatory: No [@private] for [ModuleLocalName] that [not exported] And Mandatory: No [Underscore] at end of [ModuleLocalName] that [not exported]---》No [Dangling Underscores] in [Identifiers]
        
        set option name, rule 错误 
        11 Optional: [ImportStatement] not for [80ColumnLimit]   no instantiate regular expression
        44  [BlankLine] between [ConsecutiveMethods] in [Class, ObjectLiteral]  
        
        133 [ParameterTypes, ReturnTypes] have [@param, @return] or [InlineAnnotations]
        option 3: requireReturn; true; Mandatory: [Return Tag] even if [No Return Statement]
        option 4: requireReturnType; true; Mandatory: [Return Type] in [Return Tags]
        129 Mandatory: [TypeAnnotation] have [@param, @return, @this, @type] 
        option 1: prefer; object; {"arg": "param", "argument": "param", "class": "constructor", "return": "returns", "virtual": "abstract"}  
        125 Mandatory: [Classes, Interfaces, Records] have [Description] valid-jsdoc
        104 set多余的option rule rule type error; Mandatory: No [Modification] to [BuiltinObject] by [Other];suboption 1.1: exceptions; array; Optional: [Extending] of {{exceptions}} [Builtin Objects] 
        
        
        # semantic error, 
        47  Optional: [FunctionArguments] is [SameLine] as [FunctionName]  rule type实际不一样但是认为是Yes
        64 Optional: [Methods] on [ObjectLiterals] can have [MethodShorthand] +  Mandatory: [MethodShorthand] replaces [Colon] + [Function] or [ArrowFunctionLiteral]
        
        Optional: [TemplateLiteral] is preferred over [ComplexStringConcatenation] if [MultipleStringLiterals] are involved 
        # prefer-template  Mandatory: [Template Literals] instead of [String Concatenation]; No [Usage] of ['+'] with [Strings]  
         89 同义词 [LineContinuation] in [String] vs [Multiline Strings]
         Mandatory: No [LineContinuation] in [OrdinaryStringLiteral, TemplateStringLiteral]
           >>> 
           RuleName: no-multi-str
           Mandatory: No [Multiline Strings]
        没有严格按照步骤走 134 comma-spacing indent remove objects in StyleSEM
        128 Mandatory: [PropertyType] have [Documentation] >>>> RuleName: require-jsdoc Mandatory: [JSDoc Comments] for [specified nodes]
        '''
        # 36, 44, 46, 48, 51, 53, 57, 58, 63, 64, 68, 69, 72, 73, 74, 77, 80, 81, 82,
        # 83, 85, 88, 89, 91, 92, 94, 95, 104, 105, 106, 118, 119, 123, 126, 127, 128, 129, 133, 143, 146,
        # 147]
        # if ind not in [48,51]:  #41,42,  7, 22, 4444, 12,19,   43, 4,11 6,7,36, 52,53 14,48
        #     continue
        # if ind >= 45:
        #     continue
        # if ind <=125:
        #     continue

        if rule_description:
            # print(">>>>>rule_description: ",ind, rule_description)
            # continue
            toolruleset_des = toolruleset[ind]

            if "No Possible Configuration Rules" in toolruleset_des:
                answer = ""
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind),
                               {ind: answer})
                continue

            flag = 1
            # break
            # prompt_gen_config = preprocess_promt(DSL_Syntax=dsl, style=style,
            #                                      DSLruleset=rule_description,
            #                                      tool=tool, toolruleset=toolruleset_des, grammar="Grammar", example="")
            prompt_gen_config = preprocess_promt(DSL_Syntax=dsl, style=style,
                                                 DSLruleset=rule_description,
                                                 tool=tool, toolruleset=toolruleset_des, grammar="Grammar", example="")

            # print(">>>>>>prompt: ", prompt_gen_config)
            # continue
            # if not os.path.exists(gpt_original_dir+str(ind)+".json"):
            if flag or not os.path.exists(gpt_answer_dir + "gen_config/" + str(ind) + ".json"):

                # prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
                print(">>>>>prompt_EachMap_Config: ", ind, prompt_gen_config)
                # continue
                answer = agent.get_response(prompt_gen_config, model=model,temperature=0.2)  # ,temperature=0.7
                # answer = agent.get_response(prompt_gen_config, model="o1-mini")#,temperature=0.7

                util.save_json(gpt_answer_dir + "gen_config/", str(ind), {ind: answer})

                print(">>>>>>answer_EachMap_Config: ", ind, answer)
                prompt = extract_config_promt(text=answer)
                answer_map = agent.get_response(prompt, model=model)
                print(">>>>>>answer_EachMap_Config: ", ind, answer_map)
                if "Yes" not in answer_map:
                    print(">>>>>Empty Config")
                    util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: ""})
                    continue

                # prompt_validate = '''Check whether each mapping lack setting objects''' if an option rule involves more than one option names, analyze relationships between option values of these option names, and then modify these option values to align the semantics of the StyleSEM rule.

                prompt_other_option = f'''For the following mappings, before ">>>" is StyleSEM rule, after ">>>" is corresponding Tool rules,
For each StyleSEM rule, you check whether corresponding Tool rules need to add other option rule from the Tool Rule Name based on the following steps.
Do not add basic rules and option rule whose rule type is not same as the rule type of the StyleSEM rule !

0. If its option rule is empty, do nothing and skip next steps.
1. If suboption or subsuboption names are extracted, you must add its parent options like option and suboption names and rules. 
2. If extracted option rules starting with "Mandatory" or "Optional" contain other options enclosed in "{'{{}}'}" braces, you also must add these other option names and the corresponding option rules. 
3. According to option data type and value range, Set valid option values for added option rules.
4. If an option rule involves multiple option names, analyze the relationships between their option values. Infer the appropriate value for each option by considering their combined semantics.


Give the analysis and the final correct mappings!

Mapping:
{answer_map}

Referenced tool information:
{toolruleset_des}

Response Format:
Analysis: ....
Final correct mappings: ...
For example, for the following mapping,
1. Mandatory: [Contents] of [SwitchBlock] is [Indented+2]
   >>> 
   RuleName: indent
   Basic Rule: Mandatory: Consistent [Indentation]
   Option Rule: 
   suboption 2.2: SwitchCase; 2; Mandatory: [Indentation] of [Case Clauses] is {{SwitchCase}} multiplied by {{option 1}}

You should respond like: 
1. suboption SwitchCase have parent option, so we add parent option of option 2.
2. the option rule of suboption SwitchCase contains other options "option 1", so we add the "option 1".
3. set the values "option 1" as 2.
4. the option rule of suboption SwitchCase involved two options, since the [Indentation] of [Case Clauses] = {{SwitchCase}} multiplied by {{option 1}}, so we modify the option value of SwitchCase as 1 because 2 = 1 (SwitchCase) multiplied by 2 (option 1)

The final correct mappings is:
1. Mandatory: [Contents] of [SwitchBlock] is [Indented+2]
   >>> 
   RuleName: indent
   Basic Rule: Mandatory: Consistent [Indentation]
   Option Rule: 
   option 1: No Option name; 2; Mandatory: [Indentation] is 2 [Spaces]
   option 2: No Option Name; obj; 
       suboption 2.2: SwitchCase; 1; Mandatory: [Indentation] of [Case Clauses] is 2 multiplied by  1
'''
                print(">>>>>>prompt_other_option: ", ind, prompt_other_option)

                answer_other_opt = agent.get_response(prompt_other_option, model=model)  # ,
                # answer_other_opt = agent.get_response(prompt_other_option, model=model) # ,

                # previous_msg=[prompt_gen_config, answer_map ]
                print(">>>>>>answer_other_opt: ", ind, answer_other_opt)
                prompt = extract_config_promt(text=answer_other_opt)
                answer_map = agent.get_response(prompt, model=model)
                delete_invalid_mappings='''Delete mappings where the set option values are outside the valid option value range.
                '''
                # prompt = extract_delete_config_promt(text=answer_map, tool=toolruleset_des)
                # print(">>>>>>delete config: ", ind, prompt)
                #
                # answer_map = agent.get_response(prompt, model=model)

                print(">>>>>>answer_EachMap_Config: ", ind, answer_map)
                util.save_json(gpt_answer_dir + "gen_config_preprocess_map/", str(ind), {ind: answer_map})
            else:
                print(">>>>>prompt_EachMap_Config: ", ind, prompt_gen_config)
                answer = util.load_json(gpt_answer_dir + "gen_config/", str(ind))[str(ind)]
                print(">>>>>>answer_EachMap_Config: ", ind, answer)
                if os.path.exists(gpt_answer_dir + "gen_config_preprocess_map/" + str(ind) + ".json"):
                    answer_map = util.load_json(gpt_answer_dir + "gen_config_preprocess_map/", str(ind))[str(ind)]
                    print(">>>>>>answer mapping: ", ind, answer_map)
                else:
                    answer_map = ""

            if "Yes" not in answer_map:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: ""})
                continue
            # continue

            # flag = 1
            if flag or not os.path.exists(
                    gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map/" + str(ind) + ".json"):
                # prompt = extract_config_promt(text=answer)
                prompt = extract_non_empty_config_promt(text=answer_map)
                answer_map = agent.get_response(prompt, model=model)
                print(">>>>>>answer answer_map_no_empty: ", ind, answer_map)
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map/", str(ind),
                               {ind: answer_map})
            else:
                answer_map = util.load_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map/", str(ind))[
                    str(ind)]
                print(">>>>>>answer answer_map_no_empty: ", ind, answer_map)
            if "Yes" not in answer_map:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: ""})
                continue
            # continue
            # flag = 0
            flag = 1

            if "regular expression" in answer_map.lower():
                # if flag or not os.path.exists(
                #         gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression" + str(
                #                 ind) + ".json"):
                if flag:
                    prompt_set_value = f'''For each mapping, if any option name value is "regular expression", only set specific regular expression value of option names to match rule
 Must set specific regular expression values!

        {answer_map}'''
                    print(">>>>>>set_value_answer: ", prompt_set_value)
                    set_value_answer = agent.get_response(prompt_set_value,
                                                          model=model)  # ,, model="o1-mini" previous_msg=validation_previous_msg ,temperature=0.7 , previous_msg=[all_prompt_regEx_set, validation_answer_1]

                    print(">>>>>>set_value_answer: ", set_value_answer)
                    prompt_map_replace_value = f'''Based on the following Analysis, only Replace "regular expression" with setting regular expression values for the following mapping. And then give new Mappings.
1. Extract specific regular expression values for "regular expression" value from the following Analysis.
2. Replace "regular expression" value with corresponding specific regular expression values within the following mapping.
Must set specific specific regular expression values!

Finally give new Mappings with same number of mappings.

Analysis:
{set_value_answer}

Mapping:
{answer_map}
        '''
                    # print(">>>>>>prompt_map_replace_value: ", prompt_map_replace_value)
                    answer_map_with_value = agent.get_response(prompt_map_replace_value,
                                                               model=model)  # ,previous_msg=["",set_value_answer_extract],, model="o1-mini" previous_msg=validation_previous_msg ,temperature=0.7 , previous_msg=[all_prompt_regEx_set, validation_answer_1]

                    # print(">>>>>>answer_map_with_value: ", answer_map_with_value)
                    answer_map_with_value_simp = extract_config_promt(text=answer_map_with_value)

                    answer_map = agent.get_response(answer_map_with_value_simp, model=model)
                    prompt_add_tokens = '''For the above mappings, before ">>>" is StyleSEM rule,
For each mapping, extract all Java Terms enclosed in "[]", 
determine whether lacks option name, option rules from its options of the corresponding RuleName that corresponding to the extracted Java Terms enclosed with "[]" of StyleSEM rule.
If lacks, add the option name and option rule from its options of the corresponding RuleName, set its value based on the appropriate data type, value range, and option rule. 

Avoid constructing non-existent or unnecessary options for Tool RuleName!
If corresponding RuleName does not have missed option name, do not construct non-existent option!

Finally, Give the final new mappings.'''
                    # If corresponding ESLint RuleName does not have missed option name, do not construct non-existent option! Do not add non-existent option names in tool information!

                    # answer_add_tokens = agent.get_response(prompt_add_tokens, model=model, previous_msg=[prompt_gen_config,"Checkstyle: "+toolruleset_des+"\n"+ answer_map])
                    answer_add_tokens = agent.get_response(prompt_add_tokens, model=model,
                                                           previous_msg=[prompt_gen_config, answer_map])
                    print(">>>>>>answer_map with regular expression value: ", answer_add_tokens)
                    promt_answer_map = extract_config_promt(text=answer_add_tokens)
                    answer_map = agent.get_response(promt_answer_map, model=model)

                    util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                                   str(ind),
                                   {ind: answer_map})
                else:
                    answer_map = \
                        util.load_json(
                            gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                            str(ind))[str(ind)]
                    print(">>>>>>answer_map with regular expression value: ", answer_map)

            else:
                if flag or not os.path.exists(
                        gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/" + str(
                            ind) + ".json"):
                    prompt_add_tokens = r'''For the above mappings, before ">>>" is StyleSEM rule,
For each mapping, extract all Java Terms enclosed in "[]", 
determine whether lacks option name, option rules from its options of the corresponding RuleName that corresponding to the extracted Java Terms enclosed with "[]" of StyleSEM rule.
If lacks, add the option name and option rule from its options of the corresponding RuleName, set its value based on the appropriate data type, value range, and option rule. 
Do not add basic rules and option rule whose rule type is not same as the rule type of the StyleSEM rule !

Avoid constructing non-existent or unnecessary options for Tool RuleName!
If corresponding RuleName does not have missed option name, do not construct non-existent option!

Finally give final new Mappings.

For example, for the mapping:
1. Optional: [ColumnLimit] of [goog.provide, goog.require] is not [80]
   >>> 
   RuleName: max-len
   Option Rule: 
     option 1: code; 80; Mandatory: [Line Length] is 80 [Unicode Characters]

[goog.provide, goog.require] lacks corresponding option rule which can be set by "ignorePattern" name, whose regular expression value is "/goog\.(provide|require)\(\s*['"]([^'"]+)['"]\s*\)/g"
So we add option 4 "ignorePattern", the new mappings is as follows:

Mappings:
1. Optional: [ColumnLimit] of [goog.provide, goog.require] is not [80]
   >>> 
   RuleName: max-len
   Option Rule: 
     option 1: code; 80; Mandatory: [Line Length] is 80 [Unicode Characters]
     option 4: ignorePattern; "/goog\.(provide|require)\(\s*['"]([^'"]+)['"]\s*\)/g"; Optional: [Line Length] not for {{ignorePattern}} 
'''

                    # answer_add_tokens = agent.get_response(prompt_add_tokens, model=model, previous_msg=[prompt_gen_config,"Checkstyle: "+toolruleset_des+"\n"+ answer_map])
                    # print(">>>>>answer_map: ", answer_map)
                    answer_add_tokens = agent.get_response(prompt_add_tokens, model=model,
                                                           previous_msg=[prompt_gen_config, answer_map])
                    # print(">>>>>>answer_map with regular expression value: ", answer_add_tokens)
                    promt_answer_map = extract_config_promt(text=answer_add_tokens)
                    answer_map = agent.get_response(promt_answer_map, model=model)
                    print(">>>>>>answer_map with regular expression value: ", answer_map)

                    util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                                   str(ind),
                                   {ind: answer_map})
                else:
                    answer_map = \
                        util.load_json(
                            gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                            str(ind))[str(ind)]

            # continue
            flag = 1
            if flag or not os.path.exists(
                    gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge_process/" + str(ind) + ".json"):
                tool_map_prompt = f'''For the following mappings,before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. 
You only excerpt ToolSEM rule consisting of Rulename, Basic rule and Option rules.

Mappings:
{answer_map}

Response Format: Please do not give explanation.
1. RuleName: ...
   Basic Rule: ...
   Option Rule: 
     ...
2. ...
...
'''
                ans_map_tool = agent.get_response(tool_map_prompt, model=model)  #
                print(">>>>>>ans_map_tool: ", ind, ans_map_tool)
                # continue
                merg_prompt = merge_basic_option_rules(ans_map_tool)
                # print(">>>>>>merg_prompt: ", ind, merg_prompt)
                one_ques = '''1.   RuleName: MissingJavadocType  
   Basic Rule: Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [Scope] is not [missing]  
   Option Rule:  
   option 1: scope; "public"; Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [public Scope] is not [missing]  
   option 2: tokens; "CLASS_DEF"; Mandatory: [Javadoc comments] for {{tokens}} in [Scope] is not [missing]  
'''
                one_response = '''
1. RuleName: MissingJavadocType  
   Basic Rule: Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [Scope] is not [missing]  
   Option Rule:  
   option 1: scope; "public"; Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [public Scope] is not [missing]  
   option 2: tokens; "CLASS_DEF"; Mandatory: [Javadoc comments] for {{tokens}} in [Scope] is not [missing] 
   >>>
   Mandatory: [Javadoc comments] for [class definitions] in [public scope] is not [missing]

Explanation:

Given the **Basic Rule** and the **Option Rules**, let's break down and combine them to derive the new ToolSEM rule.

### Basic Rule:
- **Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [Scope] is not [missing]**
  - This rule requires Javadoc comments to be present for class, enum, interface, and annotation interface definitions in the specified **scope** (which could be any scope, e.g., public, private, etc.).

### Option Rules:
1. **Option 1: scope; "public"; Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [public Scope] is not [missing]**
   - This option restricts the rule to only **public** scope. It mandates that class, enum, interface, and annotation interface definitions in the public scope must have Javadoc comments, and those comments cannot be missing.

2. **Option 2: tokens; "CLASS_DEF"; Mandatory: [Javadoc comments] for {{tokens}} in [Scope] is not [missing]**
   - This option applies to a specific **token type**, in this case, `CLASS_DEF`, which refers to class definitions. It mandates that Javadoc comments cannot be missing for class definitions within the specified scope.

### Deriving the New Rule:
Combining the basic rule with the two option rules leads to more specific constraints.

1. **Basic Rule** (general case) states that Javadoc comments are mandatory for class, enum, interface, and annotation interface definitions in any scope.

2. **Option 1** restricts this to the **public scope**, so now the rule applies only to public class, enum, interface, and annotation interface definitions.

3. **Option 2** narrows this down further by focusing only on the **CLASS_DEF** token type, i.e., class definitions specifically, within the given scope.

### Determine the Rule type of New ToolSEM Rule:
**rule type of New ToolSEM Rule** Since all rule types of Basic Rule, Option 1,  and Option 2 rules are "Mandatory", the rule type of New ToolSEM Rule is "Mandatory".

### New ToolSEM Rule:
- **Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [Scope] is not [missing]**
  - This rule remains the same as the basic rule.

- **Option 1:** **scope; "public";**   
  - This enforces the rule only for public scope.

- **Option 2:** **tokens; "CLASS_DEF";**   
  - This applies the rule specifically to class definitions.

### Final New ToolSEM Rule:
- **Mandatory: [Javadoc comments] for [class definitions] in [public scope] is not [missing]**
  - This rule now specifies that **Javadoc comments** are mandatory for **class definitions** in the **public scope**, ensuring that no class definition in the public scope is missing Javadoc comments.

Thus, the new ToolSEM rule becomes:
- **Mandatory: [Javadoc comments] for [class definitions] in [public scope] is not [missing]**
'''
                merge_answer_map = agent.get_response(merg_prompt, model=model, temperature=0.3,
                                                      previous_msg=[one_ques, one_response])  #
                print(">>>>>>answer merge_basic_opt_rules: ", ind, merge_answer_map)
                # merge_answer_map_2 = agent.get_response(merg_prompt, model=model, temperature=0.3, previous_msg=[one_ques,one_response]) #
                # print(">>>>>>answer merge_basic_opt_rules_2: ", ind, merge_answer_map_2)
                # final_answer = agent.get_response("First response or Second response is better and clear and correct", model=model, previous_msg=["","First: \n"+merge_answer_map+"Second: \n"+merge_answer_map_2]) #
                # print(">>>>>>final_answer: ", ind, final_answer)

                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge/", str(ind),
                               {ind: merge_answer_map})
                prompt_extract_merge_map = extract_merge_mappings_promt(text=merge_answer_map, answer_map=answer_map)
                merge_ans_map_concise = agent.get_response(prompt_extract_merge_map, model=model)
                print(">>>>>>merge_ans_map_concise: ", ind, merge_ans_map_concise)
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge_process/", str(ind),
                               {ind: merge_ans_map_concise})
            else:
                merge_ans_map_concise = \
                    util.load_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge_process/",
                                   str(ind))[
                        str(ind)]
                print(">>>>>>answer merge_basic_opt_rules: ", ind, merge_ans_map_concise)
            # continue
            flag = 1
            if flag or not os.path.exists(
                    gpt_answer_dir + "validation_config_semantic_no_specific_split/" + str(ind) + ".json"):  # 1:#
                agent = GPTAgent()
                validation_prompt = validation_config_superset_semantics(mapping=merge_ans_map_concise,
                                                                         style="RuleSet of Google Java Style Guide",
                                                                         DSL_Syntax=dsl, tool="Checkstyle",
                                                                         toolruleset=toolruleset_des, grammar="Grammar")
                print(">>>>>>validation_prompt: ", ind, validation_prompt)
                validation_answer = agent.get_response(validation_prompt, model="o1-mini")

                # validation_answer = agent.get_response(validation_prompt, model=model, temperature=0)
                # validation_answer = GPTAgent.get_response(validation_prompt, model=model, temperature=0.7)

                # validation_answer = agent.get_response(validation_prompt, model="gpt-4o",
                #                                        temperature=0.7)  # o1-mini,previous_msg=validation_previous_msg ,temperature=0.7
                print(">>>>>>validation answer: ", ind, validation_answer)
                util.save_json(gpt_answer_dir + "validation_config_semantic_no_specific_split/", str(ind),
                               {ind: validation_answer})
            else:
                validation_prompt = validation_config_superset_semantics(mapping=merge_ans_map_concise,
                                                                         style="RuleSet of Google Java Style Guide",
                                                                         DSL_Syntax=dsl, tool="Checkstyle",
                                                                         toolruleset=toolruleset_des, grammar="Grammar")
                print(">>>>>>validation_prompt: ", ind, validation_prompt)
                validation_answer = \
                util.load_json(gpt_answer_dir + "validation_config_semantic_no_specific_split/", str(ind))[str(ind)]
                print(">>>>>>validation answer: ", ind, validation_answer)
            # continue

            # flag=1
            # flag = 0
            if flag or not os.path.exists(
                    gpt_answer_dir + "validation_config_no_specific_split_process/" + str(ind) + ".json"):  # 1:#
                prompt_correct_map = extract_correct_mapping(mapping=answer_map, correct_information=validation_answer)
                print(">>>>>>extract correct mapping: ", ind, prompt_correct_map)
                correct_map_answer = agent.get_response(prompt_correct_map, model=model)
                print(">>>>>>correct mapping answer: ", ind, correct_map_answer)
                util.save_json(gpt_answer_dir + "validation_config_no_specific_split_process/", str(ind),
                               {ind: correct_map_answer})
            else:
                prompt_correct_map = extract_correct_mapping(mapping=answer_map, correct_information=validation_answer)
                print(">>>>>>extract correct mapping: ", ind, prompt_correct_map)
                correct_map_answer = \
                util.load_json(gpt_answer_dir + "validation_config_no_specific_split_process/", str(ind))[str(ind)]
                print(">>>>>>correct mapping answer: ", ind, correct_map_answer)

            # continue

            if "Yes" not in correct_map_answer:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: ""})
                continue
            # continue

            # flag = 1
            if flag or not os.path.exists(gpt_answer_dir + "gen_specific_split_config/" + str(ind) + ".json"):  # 1:#
                prompt_gen_config = gen_config_format(mapping=correct_map_answer, tool="ESLint", format="JSON")

                config_answer = agent.get_response(prompt_gen_config, model=model)
                print(">>>>>>answer specific configuration: ", ind, config_answer)
                util.save_json(gpt_answer_dir + "gen_specific_split_config/", str(ind), {ind: config_answer})
            else:
                config_answer = util.load_json(gpt_answer_dir + "gen_specific_split_config/", str(ind))[str(ind)]
                print(">>>>>>answer specific configuration1: ", ind, config_answer)
            if "Yes" not in config_answer:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: ""})
                continue

            # flag = 0
            if flag or not os.path.exists(
                    gpt_answer_dir + "gen_specific_config_split_preprocess/" + str(ind) + ".json"):  # 1:#
                prompt_extract_config = extract_specific_config_promt(text=config_answer, format="JSON")
                print(">>>>>>prompt_extract_config final: ", ind, prompt_extract_config)

                config_answer = agent.get_response(prompt_extract_config, model=model)
                print(">>>>>>answer specific configuration final: ", ind, config_answer)
                if "Yes" not in config_answer:
                    config_answer = ""
                json_answer = util_js.process_ESLint_Json(config_answer)
                validJSON_flag = util_js.valid_json_flag(json_answer)
                if not validJSON_flag:
                    fix_format_error = '''The following format of JSON configuration is error! Fix the error and give the valid and well-formatted JSON structure while preserving the original data and its intended meaning. 

Please do not explain, only give the json in given response format.                    

JSON configuration:
{{json_answer}}

Response Format:
```json
{
"key-of rule name1" : [XXXX],
"key-of rule name2" : [XXXX]
...
}
```'''
                    fix_format_error = fix_format_error.replace("{{json_answer}}", json_answer)
                    print(">>>fix_format_error: ", fix_format_error)
                    config_answer = agent.get_response(fix_format_error, model=model)

                print(">>>>>>answer specific configuration final: ", ind, config_answer)
                util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind), {ind: config_answer})
            else:
                config_answer = util.load_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind))[
                    str(ind)]
                # if "none" in config_answer.lower():
                #     config_answer = ""
                # util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: config_answer})
                print(">>>>>>answer specific configuration final: ", ind, config_answer)

        else:
            answer = ""
            util.save_json(gpt_answer_dir + "gen_specific_config_split_preprocess/", str(ind),
                           {ind: answer})


def get_all_javastyle_dsl_json_file(gpt_preprocess_answer_dir_standard_example, file_name):
    gpt_dsl_rule_list = util.load_json(gpt_preprocess_answer_dir_standard_example, file_name)

    google_java_dsl_rules = []

    def preprocess_javastyle_dsl(text):
        # print(">>>javastyle text: ",text)
        if "Description is:" in text:
            ind = text.index("Description is:")
            return text[ind + len("Description is:"):].strip()
        if "Description:" in text:
            ind = text.index("Description:")
            return text[ind + len("Description:"):].strip()
        else:
            return text.strip()

    # print(">>>>>gpt_preprocess_answer_dir_standard_example: ",gpt_preprocess_answer_dir_standard_example,len(os.listdir(gpt_preprocess_answer_dir_standard_example)))
    # check_style_rule_list = util.load_json(util.data_root + "style_tool_rules/","checkstyle_name_completedes_options_3_process")
    # gpt_preprocess_answer_dir_standard_example = util.data_root + "gpt_dsl_answer/GoogleJavaStyle_Simple_DSL_syntax_SplitSentence_example4_preprocess/"
    for ind, (url, rule_name, *r_main, text) in enumerate(gpt_dsl_rule_list):

        # print(">>>>>JavaStyle: ", text)
        checkstype_dsl = preprocess_javastyle_dsl(text)
        # print(">>>>>checkstype_dsl: ", checkstype_dsl)
        if "NO RULE" in checkstype_dsl:
            google_java_dsl_rules.append([url, rule_name, ""])
            continue
        google_java_dsl_rules.append([url, rule_name, checkstype_dsl])
        # '''
    return google_java_dsl_rules



if __name__ == "__main__":

    dir_name="GenDSL_JS_ESLint_no_except_new/"

    all_checkstyle_dsls = util.load_json(util.data_root + dir_name,"DSL_ESLint_all")

    checkstyle_dsl_basic_rules = {rulename: tex for url, rulename, tex in all_checkstyle_dsls}
    checkstyle_dsl_basic_rules_rulename = {"RuleName: " + rulename: tex for url, rulename, tex in all_checkstyle_dsls}

    few_checkstyle_dsls = []
    gpt_answer_dir = util.data_root + dir_name+"Config_name_select_googleJS_to_ESLint_new/"

    for ind in range(len(os.listdir(gpt_answer_dir))):

        # for ind in range(len(os.listdir(gpt_answer_dir))):
        # if ind not in [2]:
        #     continue
        # for file_name in os.listdir(gpt_answer_dir):
        #     ind=file_name[:-5]
        file_name = str(ind)
        if not os.path.exists(gpt_answer_dir + file_name + ".json"):
            few_checkstyle_dsls.append('No Possible Configuration Rules')
            # print(">>>come here: ", len(few_checkstyle_dsls))
            continue
        json_res = util.load_json(gpt_answer_dir, file_name)
        res = json_res[file_name]
        # print(">>>>>>instr basic rule selection",res)
        possible_checkstype_rules = []
        for key in checkstyle_dsl_basic_rules:
            if key in res:
                if key + ": " + checkstyle_dsl_basic_rules[key] not in possible_checkstype_rules:
                    # print(">>>>>>key: ",key,checkstyle_dsl_basic_rules[key])
                    possible_checkstype_rules.append("\nRuleName: " + key + "\n" + checkstyle_dsl_basic_rules[key])
        # print(">>>extract instr selection: ","\n".join(possible_checkstype_rules))
        if possible_checkstype_rules:
            few_checkstyle_dsls.append("\n".join(possible_checkstype_rules))
        else:
            few_checkstyle_dsls.append("\n".join(['No Possible Configuration Rules']))
        # print(">>>one possible instr: ",few_checkstyle_dsls[ind])
        # break

    # javastyle_dsls_results = get_all_javastyle_dsl_json_file(util.data_root + dir_name,
    #                                                          "javastyle_url_rulename_dsl_one_review")
    #
    # javastyle_dsls = [dsl for *r, dsl in javastyle_dsls_results]  # break
    javastyle_dsls_results = get_all_javastyle_dsl_json_file(util.data_root + dir_name,
                                                             "javascriptstyle_url_rulename_dsl")
    javastyle_dsls = [dsl for *r, dsl in javastyle_dsls_results]  # break
    # print("len javastyle_dsls: ", len(javastyle_dsls), javastyle_dsls[0])

    # print("len javastyle_dsls: ", len(javastyle_dsls), javastyle_dsls[40])

    examples = ''''''

    gpt_answer_dir = util.data_root + dir_name + "Config_Gen_ESLint_for_GleJS_new_once_again_imprv_o1_3_once_again_part_run_o1mini_2_add_rulename_imprv_once_again/" #"Config_Gen_no_rulename_three_verify_once_again_imprv_chck_all copy gen_rerun/"
    gpt_answer_dir = util.data_root + dir_name + "Config_Gen_ESLint_for_GleJS_new_once_again_imprv_o1_3_once_again_part_run_o1mini_2_add_rulename_imprv_once_again2/" #"Config_Gen_no_rulename_three_verify_once_again_imprv_chck_all copy gen_rerun/"

    # "Config_Gen_ESLint_for_GleJS_new_once_again_imprv_o1_3_once_again_part_run_o1mini_2_add_rulename_imprv_once_again2"
    # '''
    # preprocess_promt(javastyle_dsls,DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
    #                  tool="Checkstyle", toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=examples)
    dsl = util_js.dsl

    get_all_gpt_res_for_java_checkstyle(gpt_answer_dir, javastyle_dsls, DSL_Syntax=dsl,
                                        toolruleset=few_checkstyle_dsls, grammar="Grammar", example=examples,
                                        model="gpt-4o-2024-08-06")


    def parse_result():
        # all_rules = util.load_csv(util.data_root + "benchmark/benchmark_javascript/google_js_rules_new2.csv")

        all_rules = util.load_csv(util.data_root + "benchmark/benchmark_javascript/google_js_rules_new3_file_implementation.csv")

        rule_list = ["\n".join([rule_name, description]) for ind, (rule_html, rule_name, description, *remain) in
                     enumerate(all_rules) if ind > 0]
        # all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze copy.csv")
        bench_mark = util.load_json(util.data_root + "benchmark/benchmark_javascript/", "google2eslint_js_benchmark_simple_v6")
        bench_mark = util.load_csv(util.data_root + "benchmark/benchmark_javascript/google2eslint_js_benchmark_v6.csv")

        csv_results = []
        insert_index = 3
        for ind in range(len(os.listdir(gpt_answer_dir+"gen_specific_config_split_preprocess/"))):
            # if ind >=2:
            #     continue
            # for file_name in os.listdir(gpt_answer_dir):
            #     ind=file_name[:-5]
            file_name = str(ind)
            json_res = util.load_json(gpt_answer_dir+"gen_specific_config_split_preprocess/", file_name)
            res = json_res[file_name]

            def process_ESLint_Json(res):
                index_xml = res.index("```json") if "```json" in res else None
                res = res[index_xml:] if index_xml else res
                res = res.replace("```json", "")
                res = res.replace("```", "")
                if "Configuration:" in res:
                    res = res.replace("Configuration:", "")
                return res.strip()
            res = process_ESLint_Json(res)
            res=res.replace(" false"," False")
            res=res.replace(" true"," True")


            # url, rule_name, dsl_answer = gpt_checkstyle_dsls[ind]
            one_rule = copy.deepcopy(bench_mark[ind + 1][1:3])
            # key = all_rules[ind + 1][1] + '\n' + all_rules[ind + 1][2]
            flag_key = None
            for key2 in bench_mark:
                if key[:20] == key2[:20]:
                    flag_key = key2
                    break
            one_rule.append(bench_mark[flag_key] if flag_key else "")
            if "error" in res:
                one_rule.append("Yes")
            else:
                one_rule.append("No")
            one_rule.append("" if "error" not in res else res)

            # one_rule.insert(3, bench_mark[flag_key] if flag_key else "None")
            # one_rule.insert(3, prompt)

            # one_rule.insert(3, res)
            # one_rule.insert(3, javastyle_dsls_results[ind][2])
            # csv_results.append(one_rule)
            # rule_description = javastyle_dsls[ind]
            # if rule_description:
            #     # break
            #     toolruleset_des = few_checkstyle_dsls[ind]
            #     prompt = preprocess_promt(DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
            #                               DSLruleset=rule_description,
            #                               tool="Checkstyle", toolruleset=toolruleset_des, grammar="Grammar", example="")
            #
            #
            # else:
            #     prompt = "No need"
            # one_rule.insert(3, bench_mark[flag_key] if flag_key else "None")
            # one_rule.insert(3, prompt)

            # one_rule.insert(3, res)
            # one_rule.insert(3, javastyle_dsls_results[ind][2])
            csv_results.append(one_rule)
        # util.save_csv(util.data_root + "instr_select_csv/instr_selection_basic_rules_3.csv", csv_results)
        # util.save_csv(util.data_root + "instr_select_csv/instr_selection_optionvalue_add_benchmark.csv", csv_results)
        # util.save_csv(
        #     gpt_answer_dir + "metrics_res/1210/GLJS_ESLint_configuration_1210.csv",
        #     csv_results,['rule_name','description','benchmark','gpt_answer','gpt_configuration'])
        util.save_csv(
            gpt_answer_dir + "metrics_res/0111_split/GLJS_ESLint_configuration_0111.csv",
            csv_results, ['rule_name', 'description', 'benchmark', 'gpt_answer', 'gpt_configuration'])

        # for each_rule in res.split("\n") :
        #     csv_results


    # parse_result()

    parse_result()
