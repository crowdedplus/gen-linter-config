import copy
import os, json, inspect, sys
import re
import shutil

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
grandparentdir = os.path.dirname(parentdir)
sys.path.insert(0, parentdir)
sys.path.insert(0, grandparentdir)
import util, util_java

from openai import OpenAI
from retry import retry
from gpt_wrapper import GPTAgent


# 构建用于生成Checkstyle配置的核心提示词
def preprocess_promt(DSL_Syntax: str, style="RuleSet of Google Java Style Guide", DSLruleset=None, tool="Checkstyle",
                     toolruleset=None, grammar="Grammar", example=""):

    prompt = '''Extract each rule from the following {{Style}} where starting with "Mandatory" or "Optional".
Identify if each rule in RuleSet of {{Style}} has semantically equivalent rules from Basic Rule or Option Rule of {{tool}} based on the following step 1 -- step 5. 
Strictly following details in step 2. **ensuring The rule type of excerpted matching option rule ("Optional" or "Mandatory") must be same as the rule type ("Optional" or "Mandatory") in the Option Rule from the following {{tool}}**.

1. From the Basic Rule of the following {{tool}}, excerpt matching rule with the rule of {{Style}}. 
2. From the Option Rule of the following {{tool}}, excerpt matching option name and Option Rule, **ensuring The rule type of excerpted matching option rule ("Optional" or "Mandatory") must be same as the rule type ("Optional" or "Mandatory") in the Option Rule from the following {{tool}}**.
    - Under no circumstances should the rule type of the Option Rule ("Optional" or "Mandatory") be changed.
    - If the Option Rule cannot match without changing the rule type, output "No Match" instead of altering the rule type.
3. If the data type of option name is not regular expression, set specific option values  based on data type, ensuring alignning with the rule of {{Style}}. otherwise, set the option values as "regular expression".
4. Identify corresponding RuleName to matched basic rules and option rules. 
5. The rule type of excerpted matching option rule ("Optional" or "Mandatory") must be same as the rule type ("Optional" or "Mandatory") in the Option Rule from the following {{tool}}. 
For example, if the rule type of one "tokens" option of NeedBraces of {{tool}} is "Mandatory", the rule type of excerpted matching option rule must be Mandatory".
**If there are no direct matching rules, the mappings should be None.**
Note set specific option values should not be enclosed with '{}' or '[]', just a string is ok.

A rule in RuleSet of {{Style}} may correspond to multiple RuleNames of {tool}!

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
    ...
    option k:  corresponding OptionName; Option Value; option rule expressed in given {{grammar}} 

    RuleName2: <Give corresponding RuleName from {{tool}}> 
    ...

For example, 
1. Optional: [ColumnLimit] is [100] not for [PackageStatement]
   >>> 
   RuleName: LineLength
   Basic Rule: Mandatory: No [Line] longer than [max]
   Option Rule: 
   option 2: ignorePattern; `^package\\s+.*;`; Optional: [LineLength] not for {{ignorePattern}}
   option 3: max; `100`; Mandatory: No [Line] longer than {{max}}

2. Mandatory: [Annotations] of [Class] after [DocumentationBlock]
    >>> 
   RuleName: AnnotationLocation
   Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule: 
   option 1: tokens; `CLASS_DEF`; Check [annotation location] for {{tokens}}

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


# 基础映射提取
def extract_config_promt(text: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Excerpt Mappings from the following text without altering their content in any way. Only perform the extraction.

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

# 非空映射提取
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

# 合并映射更新
def extract_merge_mappings_promt(text: str, answer_map: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''For the following Mappings, before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. 
You based on the following New ToolSEM rule mapping, replace ToolSEM rule with new ToolSEM rule in Mappings. \

Mappings:
{{answer_map}}

New ToolSEM rule mapping:
{{Input}}

Response Format: No explanation. 

**Mapping:**
1. StyleSEM rule
>>>
new ToolSEM rule 1
new ToolSEM rule 2

2. ...

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
   Mandatory: [empty line separator] before [fields, constructors, methods, nested classes, static initializers, instance initializers]

2. Optional: [BlankLine] between [two consecutive fields] : not have [other code] between [two consecutive fields]
   >>> 
   Optional: [no empty line] between [fields]

3. Optional: [MultipleConsecutiveBlankLines] are permitted
   >>> 
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


# 验证映射的语义是否一致（如规则类型和语义是否匹配）。
def validation_config_superset_semantics(mapping: str, style="RuleSet of Google Java Style Guide", DSL_Syntax="",
                               tool="Checkstyle",
                               toolruleset=None, grammar="Grammar", example=""):

    prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:

For each mapping, do the following steps: Step 1 ~ Step 2.

Step 1: Compare the rule type :

 - If the rule types are the same (both "Optional" or both "Mandatory"), proceed to Step 2.
 - If the rule types are different, the mapping result is No.

Step 2: Compare Semantics:
 - If their semantics are identical, the mapping result is Yes. 
 - Or if the semantics of one rule are a subset of or superset within the semantics of the other, the mapping result is Yes.
 - Otherwise, If the semantics are not identical and no subset of or superset relationship exists, the mapping result is No.

Note for Comparison:
1. When comparing, consider the definitions of JavaTerms and account for synonym relationships where applicable. 


{{Mapping}}


Response Format:
Analysis: ... 
Mapping 1: Yes or No

Analysis: ... 
Mapping 2: Yes or No
'''

    prompt = prompt.replace("{{tool}}", tool)
    prompt = prompt.replace("{{style}}", style)
    prompt = prompt.replace("{{Mapping}}", mapping)
    prompt = prompt.replace("{{toolruleset}}", toolruleset)
    prompt = prompt.replace("{{Syntax}}", DSL_Syntax)
    prompt = prompt.replace("{{grammar}}", grammar)

    return prompt

# 验证映射的对象范围（如Java术语的范围是否一致）。
def validation_config_superset_objects(mapping: str, style="RuleSet of Google Java Style Guide", DSL_Syntax="",
                               tool="Checkstyle",
                               toolruleset=None, grammar="Grammar", example=""):

    prompt = '''each mapping format: 
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
    '''2. Optional: [ColumnLimit] is [100] not for [ImportStatement]  
   >>>  
   Optional: No [Line] longer than [100], except for lines matching [^import\s+.*;] 
   3. Optional: [ColumnLimit] is [100] not for [PackageStatement]  
    >>>  
Optional: No [Line] longer than [100] except for lines matching [^package\s+.*;]'''

    '''Mapping 3: Yes Explanation: The StyleSEM rule indicates that the [ColumnLimit] is [100] but does not apply to [PackageStatement], while the ToolSEM rule specifies that no [Line] should be longer than [100], except for lines matching the pattern [^package\s+.*;]. Both rules effectively exempt PackageStatement from the column limit, making their subjects equivalent in scope. Hence, the answer is Yes, as the subject of the StyleSEM rule is not narrower than that of the ToolSEM rule.'''
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

#  将Basic Rule和Option Rules合并为单一的ToolSEM规则
def merge_basic_option_rules(answer_map):
    prompt = '''For the following ToolSEM rules, 

For each ToolSEM rule consisting of the **Basic Rule** and the **Option Rules**, let's break down and combine setting option values of each ToolSEM rule to derive only one new ToolSEM rule begin with "Mandatory:" or "Optional:" using given grammar.


**Note: For the rule type of new ToolSEM rule, extract rule types of Option Rules and Basic Rule**
**if rule types of Option Rules and Basic Rule have at least one "Optional", the rule type of new ToolSEM rule must be "Optional". Otherwise, it is "Mandatory".**

Ensure new ToolSEM rule is clearer and aligns more accurately with rule details of old ToolSEM rule! Avoid ambiguous wording.

new ToolSEM rule should not be impacted by StyleSEM!!!

{{answer_map}}    

Grammar:
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

Term   ::= '[' JavaTerm ']' #Note: JavaTerm represents terminology of Java programming language; 
        | Modifier* Term 
        | Term 'of' Term 

Modifier   ::= Word (e.g., 'some' | 'each' | 'all' | 'first' | 'last' | '...') 

Word   ::= [a-zA-Z]+ 

JavaTerm   ::= [.]+ 

Note: JavaTerm represents terminology of Java programming language; 
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

2. ....
    '''
    prompt = prompt.replace("{{answer_map}}", answer_map)

    return prompt

# 映射结果提取器，根据分析结果提取有效映射
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

# 正确映射提取器，仅提取结果为"Yes"的有效映射
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

# 配置格式生成器，生成Checkstyle配置的XML格式。将映射转换为XML代码。
def gen_config_format(mapping="", tool="Checkstyle", format=""):
    prompt = '''Based on the following Mapping, generate {{tool}} configuration in {{format}} format based on the following step 1 ~ step 3.

before ">>>" is rule of {{style}}, after ">>>" is the corresponding rule from {{tool}} consisting of basic rule consisting of RuleName, Option rule consisting of option k: option names, option values and option rules starting with "Mandatory:" or "Optional".

1. Only List all rule names, option names and option values which corresponding to {{format}} configuration with module name, option name and option value from all mappings. Skip all rules like option rules or basic rules
2. Extract all same rule names or module names to merge,
    - if same rule names that do not have same option name or without option names, merge these same rule names into one configuration.
    - if there are same option names, if the option values do not conflict, merge them into one configuration. Note values of regular expression or sequence-like data type can be merged.
    - Otherwise, same module names should be individual configurations.

Mapping:
{{mapping}}

Response Format: If there is no mapping, directly give "NONE"

Analysis: Give explanation

Answer: Respond Yes or No about whether there are configurations.

Configuration:
<module name='RuleName1'>
<property name='OptionName1' value='value1'/>  
... 
<property name='OptionNamek' value='valuek'/>"
</module>
<module name='RuleName2'>
... 

For example, for the following mapping,
**Mapping:**
1. Mandatory: [TypeVariable] is [CapitalLetter]
   >>> 
   RuleName: InterfaceTypeParameterName
   Option Rule:
   option 1: format; "^[A-Z]$"; Mandatory: [interface type parameter names] match {{format}}
   
   RuleName: ClassTypeParameterName

2. Optional: [TypeVariable] is [CapitalLetter] + [Numeral]
   >>> 
   RuleName: InterfaceTypeParameterName
   Option Rule:
   option 1: format; "^[A-Z][0-9]$"; Optional: [interface type parameter names] match {{format}}

   RuleName: ClassTypeParameterName
   Option Rule:
   option 1: format; "^[A-Z][a-zA-Z0-9]*T$"; Mandatory: [interface type parameter names] match {{format}}

Analysis: All rule names, option names and option values are as following:
RuleName: InterfaceTypeParameterName
option 1: format; "^[A-Z]$";
   
RuleName: ClassTypeParameterName

RuleName: InterfaceTypeParameterName
option 1: format; "^[A-Z][0-9]$";

RuleName: ClassTypeParameterName
option 1: format; "^[A-Z][a-zA-Z0-9]*T$"; 


Since the there are three mappings whose rulename and option name are same (InterfaceTypeParameterName, format), the data type of format is regular expression, so we can merge the option value one configuration.
And there are same rules ClassTypeParameterName, one with option names, the other without option names, we remove the ClassTypeParameterName without option names.

Answer: Yes

Configuration:  
```xml
<module name='InterfaceTypeParameterName'>
    <property name='format' value='^[A-Z]|^[A-Z][0-9]$'/>
</module>
<module name='ClassTypeParameterName'>
    <property name='format' value='^[A-Z][a-zA-Z0-9]*T$'/>
</module>
```
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

# 特定格式配置提取
def extract_specific_config_promt(text: str, format: str):
    # then determine formal term of Java for objects of style and determine the appropriate operators between terms. Pay attention to
    prompt = '''Extract {{format}} configurations from the following Configuration. Respond based on the Response Format. \

Configuration:
{{Input}}

Response Format: No explanation. If there is no specific configuration, directly give "None".
Answer: Respond with Yes or No about whether there are configurations.
Configuration: Respond with {{format}} configurations
...
'''
    prompt = prompt.replace("{{format}}", format)
    prompt = prompt.replace("{{Input}}", text)
    return prompt


# 处理每个规则：调用GPT、提取配置、验证语义、生成XML。包含多个步骤（如添加token选项、合并规则）。
def get_all_gpt_res_for_java_checkstyle(gpt_answer_dir, rule_list, DSL_Syntax=None,
                                        style="RuleSet of Google Java Style Guide",
                                        tool="Checkstyle",
                                        toolruleset=None, grammar="Grammar", example="", model="gpt-4o"):
    agent = GPTAgent()

    for ind, rule_description in enumerate(rule_list[:]):
        # if ind <= 18:
        #     continue

        # if ind in [6,8,11,42,49,50,51,52,55,56,57,66]:# 4,11 6,7,36, 52,53 14,48 [4,11,17,26,32,34,41,42,43,44,47]:# 4,11 6,7,36, 52,53 14,48 [3,5,7,9,14,16,17,27,29,32,34,41,51,52,53]:#6,7,36, 52,53 ,4,14,29,34,51,52,54,62,65,
        #     continue
        # if ind not in [44]:# 43, 4,11 6,7,36, 52,53 14,48
        #     continue
        if rule_description:
            # print(">>>>>rule_description: ",ind, rule_description)
            # continue
            toolruleset_des = toolruleset[ind]

            if "No Possible Configuration Rules" in toolruleset_des:
                answer = ""
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind),
                               {ind: answer})
                continue

            flag =1
            # break
            prompt_gen_config = preprocess_promt(DSL_Syntax=dsl, style=style,
                                                 DSLruleset=rule_description,
                                                 tool=tool, toolruleset=toolruleset_des, grammar="Grammar", example="")
            print(">>>>>>prompt: ", prompt_gen_config)
            # continue
            # if not os.path.exists(gpt_original_dir+str(ind)+".json"):
            if flag or not os.path.exists(gpt_answer_dir + "gen_config/" + str(ind) + ".json"):

                # prompt = preprocess_promt(rule=rule_description, example=examples, DSL_Syntax=dsl, style=style)
                print(">>>>>prompt_EachMap_Config: ", ind, prompt_gen_config)
                # continue
                answer = agent.get_response(prompt_gen_config, model=model)#,temperature=0.7
                util.save_json(gpt_answer_dir + "gen_config/", str(ind), {ind: answer})

                print(">>>>>>answer_EachMap_Config: ", ind, answer)
                prompt = extract_config_promt(text=answer)
                answer_map = agent.get_response(prompt, model=model)
                print(">>>>>>answer_EachMap_Config: ", ind, answer_map)
                if "Yes" not in answer_map:
                    print(">>>>>Empty Config")
                    util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: ""})
                    continue
                # prompt_add_tokens = '''For the above mapping, before ">>>" is StyleSEM rule, after ">>>" is corresponding ToolSEM rule. \nIf Option rules of RuleName of Checkstyle does not have "tokens" option name, you do nothing. Otherwise, you determine Whether each StyleSEM rule needs "tokens" option of tool to specify objects that each StyleSEM rule checks. If yes, add the "tokens" option name, set the option value and option rule as one map.'''
                # prompt_ans_contains_tokens
                # answer_map = agent.get_response(prompt, model=model)
                '''Determine whether each StyleSEM rule requires a "tokens" option from its corresponding RuleName to specify the scope that StyleSEM rule checks. If required, add the "tokens" option, set its value based on the appropriate data type, value range, and option rule, and ensure alignment with the corresponding scope that StyleSEM rule checks.'''
                prompt_add_tokens = '''before ">>>" is StyleSEM rule, 
Determine Whether each StyleSEM rule needs "tokens" option from its corresponding RuleName to limit the range that each StyleSEM rule checks. If yes, add the "tokens" option name, set the corresponding option value based on its data type and value range and option rule as one map to align StyleSEM rule.
If corresponding Checkstyle RuleName does not have "tokens" option, do not construct "tokens" option.'''
                prompt_add_tokens = '''before ">>>" is StyleSEM rule, 
Determine whether each StyleSEM rule requires a "tokens" option from its corresponding RuleName to specify the scope that StyleSEM rule checks. 
If required, add the "tokens" option, set its value based on the appropriate data type, value range, and option rule, ensuring strict alignment with the corresponding JavaTerms enclosed with "[]" that StyleSEM rule checks. 
Note set specific option values should not be enclosed with '{}'.
If corresponding Checkstyle RuleName does not have "tokens" option, do not construct "tokens" option.'''

                # answer_add_tokens = agent.get_response(prompt_add_tokens, model=model, previous_msg=[prompt_gen_config,"Checkstyle: "+toolruleset_des+"\n"+ answer_map])
                answer_add_tokens = agent.get_response(prompt_add_tokens, model=model,
                                                       previous_msg=[prompt_gen_config, answer_map])

                print(">>>>>>answer_add_tokens: ", ind, answer_add_tokens)
                prompt = extract_config_promt(text=answer_add_tokens)
                answer_map = agent.get_response(prompt, model=model)
                print(">>>>>>answer_EachMap_Config: ", ind, answer_map)
                util.save_json(gpt_answer_dir + "gen_config_preprocess_map/", str(ind), {ind: answer_map})
            else:
                print(">>>>>prompt_EachMap_Config: ", ind, prompt_gen_config)
                answer = util.load_json(gpt_answer_dir + "gen_config/", str(ind))[str(ind)]
                print(">>>>>>answer_EachMap_Config: ", ind, answer)
                if os.path.exists(gpt_answer_dir + "gen_config_preprocess_map/"+str(ind)+".json"):
                    answer_map = util.load_json(gpt_answer_dir + "gen_config_preprocess_map/", str(ind))[str(ind)]
                    print(">>>>>>answer mapping: ", ind, answer_map)
                else:
                    answer_map = ""

            if "Yes" not in answer_map:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: ""})
                continue
            flag = 1
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
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: ""})
                continue
            # continue
            flag = 1
            if "regular expression" in answer_map.lower():
                # if flag or not os.path.exists(
                #         gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression" + str(
                #                 ind) + ".json"):
                if flag:
                    prompt_set_value = f'''For each mapping, if it contains "regular expression", set specific regular expression of option names to match rule

        {answer_map}'''
                    set_value_answer = agent.get_response(prompt_set_value,
                                                          model="gpt-4o")  # ,, model="o1-mini" previous_msg=validation_previous_msg ,temperature=0.7 , previous_msg=[all_prompt_regEx_set, validation_answer_1]

                    print(">>>>>>set_value_answer: ", set_value_answer)
                    prompt_map_replace_value = f'''Based on the following Analysis, Replace "regular expression" with setting regular expression values for the following mapping. And then give new Mappings.
1. Extract specific regular expression values for "regular expression" value from the following Analysis.
2. Replace "regular expression" value with corresponding specific regular expression values within the following mapping.

Analysis:
{set_value_answer}

Mapping:
{answer_map}
        '''
                    print(">>>>>>prompt_map_replace_value: ", prompt_map_replace_value)
                    answer_map_with_value = agent.get_response(prompt_map_replace_value,
                                                               model=model)  # ,previous_msg=["",set_value_answer_extract],, model="o1-mini" previous_msg=validation_previous_msg ,temperature=0.7 , previous_msg=[all_prompt_regEx_set, validation_answer_1]

                    print(">>>>>>answer_map_with_value: ", answer_map_with_value)
                    answer_map_with_value_simp = extract_config_promt(text=answer_map_with_value)

                    answer_map = agent.get_response(answer_map_with_value_simp, model=model)
                    print(">>>>>>answer_map with regular expression value: ", answer_map)
                    util.save_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                                   str(ind),
                                   {ind: answer_map})
                else:
                    answer_map = \
                    util.load_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_regular_expression/",
                                   str(ind))[str(ind)]
                    print(">>>>>>answer_map with regular expression value: ", answer_map)


            # continue
            flag = 1
            if flag or not os.path.exists(
                    gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge_process/" + str(ind) + ".json"):
                tool_map_prompt = f'''For the following mappings,before ">>>" is StyleSEM rule, after ">>>" is ToolSEM rule. You only excerpt toolSEM rule consisting of Rulename, Basic rule and Option rules.

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
                merg_prompt = merge_basic_option_rules(ans_map_tool)
                print(">>>>>>merg_prompt: ", ind, merg_prompt)
                one_ques = '''1. Mandatory: [Javadoc] is present for [PublicClass]  
   >>>  
   RuleName: MissingJavadocType  
   Basic Rule: Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [Scope] is not [missing]  
   Option Rule:  
   option 1: scope; "public"; Mandatory: [Javadoc comments] for [class, enum, interface, annotation interface definitions] in [public Scope] is not [missing]  
   option 2: tokens; "CLASS_DEF"; Mandatory: [Javadoc comments] for {{tokens}} in [Scope] is not [missing]  
'''
                one_response = '''
1. **Mandatory: [Javadoc] is present for [PublicClass]**
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
                util.load_json(gpt_answer_dir + "gen_specific_config_preprocess_no_empty_map_merge_process/", str(ind))[
                    str(ind)]
                print(">>>>>>answer merge_basic_opt_rules: ", ind, merge_ans_map_concise)

            flag = 1
            if flag or not os.path.exists(gpt_answer_dir + "validation_config_semantic/" + str(ind) + ".json"):  # 1:#
                agent = GPTAgent()
                validation_previous_msg = util_java.validation_previous_msg
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
                util.save_json(gpt_answer_dir + "validation_config_semantic/", str(ind), {ind: validation_answer})
            else:
                validation_prompt = validation_config_superset_semantics(mapping=merge_ans_map_concise,
                                                               style="RuleSet of Google Java Style Guide",
                                                               DSL_Syntax=dsl, tool="Checkstyle",
                                                               toolruleset=toolruleset_des, grammar="Grammar")
                print(">>>>>>validation_prompt: ", ind, validation_prompt)
                validation_answer = util.load_json(gpt_answer_dir + "validation_config_semantic/", str(ind))[str(ind)]
                print(">>>>>>validation answer: ", ind, validation_answer)
            # continue

            flag=1
            # flag = 0
            if flag or not os.path.exists(gpt_answer_dir + "validation_config_process/" + str(ind) + ".json"):  # 1:#
                prompt_correct_map = extract_correct_mapping(mapping=answer_map, correct_information=validation_answer)
                print(">>>>>>extract correct mapping: ", ind, prompt_correct_map)
                correct_map_answer = agent.get_response(prompt_correct_map, model=model)
                print(">>>>>>correct mapping answer: ", ind, correct_map_answer)
                util.save_json(gpt_answer_dir + "validation_config_process/", str(ind), {ind: correct_map_answer})
            else:
                prompt_correct_map = extract_correct_mapping(mapping=answer_map, correct_information=validation_answer)
                print(">>>>>>extract correct mapping: ", ind, prompt_correct_map)
                correct_map_answer = util.load_json(gpt_answer_dir + "validation_config_process/", str(ind))[str(ind)]
                print(">>>>>>correct mapping answer: ", ind, correct_map_answer)




            if "Yes" not in correct_map_answer:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: ""})
                continue
            # continue
            flag = 1
            if flag or not os.path.exists(gpt_answer_dir + "gen_specific_config/" + str(ind) + ".json"):  # 1:#
                prompt_gen_config = gen_config_format(mapping=correct_map_answer, tool="Checkstyle", format="XML")

                config_answer = agent.get_response(prompt_gen_config, model=model)
                print(">>>>>>answer specific configuration: ", ind, config_answer)
                util.save_json(gpt_answer_dir + "gen_specific_config/", str(ind), {ind: config_answer})
            else:
                config_answer = util.load_json(gpt_answer_dir + "gen_specific_config/", str(ind))[str(ind)]
                print(">>>>>>answer specific configuration: ", ind, config_answer)
            if "Yes" not in config_answer:
                print(">>>>>Empty Config")
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: ""})
                continue
            # continue

            # flag = 1
            if flag or not os.path.exists(
                    gpt_answer_dir + "gen_specific_config_preprocess/" + str(ind) + ".json"):  # 1:#
                prompt_extract_config = extract_specific_config_promt(text=config_answer, format="XML")
                config_answer = agent.get_response(prompt_extract_config, model=model)
                print(">>>>>>answer specific configuration final: ", ind, config_answer)
                if "Yes" not in config_answer:
                    config_answer = ""
                print(">>>>>>answer specific configuration final: ", ind, config_answer)
                util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: config_answer})
            else:
                config_answer = util.load_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind))[str(ind)]
                # if "none" in config_answer.lower():
                #     config_answer = ""
                # util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind), {ind: config_answer})
                print(">>>>>>answer specific configuration final: ", ind, config_answer)

        else:
            answer = ""
            util.save_json(gpt_answer_dir + "gen_specific_config_preprocess/", str(ind),
                           {ind: answer})

# DSL规则加载器，加载并预处理Google Java风格的DSL规则
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


    dir_name="GenDSL_Java_CheckStyle_no_except_imprv_dsl/"#"GenDSL_Java_CheckStyle_no_except/"

    all_checkstyle_dsls = util.load_json(util.data_root + dir_name, "DSL_checkstyle_all")

    checkstyle_dsl_basic_rules = {rulename: tex for url, rulename, tex in all_checkstyle_dsls}
    checkstyle_dsl_basic_rules_rulename = {"RuleName: " + rulename: tex for url, rulename, tex in all_checkstyle_dsls}

    few_checkstyle_dsls = []
    gpt_answer_dir = util.data_root + dir_name + "Config_name_select_googlejava_to_checkstyle_one_review/"

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

    javastyle_dsls_results = get_all_javastyle_dsl_json_file(util.data_root + dir_name,
                                                             "javastyle_url_rulename_dsl_one_review")

    javastyle_dsls = [dsl for *r, dsl in javastyle_dsls_results]  # break

    # print("len javastyle_dsls: ", len(javastyle_dsls), javastyle_dsls[40])

    examples = ''''''

    gpt_answer_dir = util.data_root + dir_name + "Config_Gen_no_rulename_three_verify_once_again_imprv_chck_all copy gen_rerun_doule_check_rerun_imprv_simple_validation_three_aspects_simpl_4o_example_add_split2_once_again_no_objs_once_agin5_4_o1_once/" #"Config_Gen_no_rulename_three_verify_once_again_imprv_chck_all copy gen_rerun/"

    # '''
    # preprocess_promt(javastyle_dsls,DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
    #                  tool="Checkstyle", toolruleset=checkstyle_dsl_basic_rules, grammar="Grammar", example=examples)
    dsl = util_java.dsl

    get_all_gpt_res_for_java_checkstyle(gpt_answer_dir, javastyle_dsls, DSL_Syntax=dsl,
                                        toolruleset=few_checkstyle_dsls, grammar="Grammar", example=examples,
                                        model="gpt-4o-2024-08-06")


    def parse_result():
        all_rules = util.load_csv(util.data_root + "GoogleJavaStyle/javastyle_myanalyze.csv")
        bench_mark = util.load_json(util.data_root + "benchmark/", "java_benchmark_7")  # "benchmarknewnew3_8_11new3"
        csv_results = []
        gpt_checkstyle_dsls = all_checkstyle_dsls
        for ind in range(len(os.listdir(gpt_answer_dir + "gen_specific_config_preprocess/"))):
            # if ind not in [9]:
            #     continue
            # for file_name in os.listdir(gpt_answer_dir):
            #     ind=file_name[:-5]
            file_name = str(ind)
            # if os.path.exists(gpt_answer_dir+file_name+".json"):
            #     continue
            json_res = util.load_json(gpt_answer_dir + "gen_specific_config_preprocess/",
                                      file_name)
            res = json_res[file_name]
            # print(">>>res: ",res)
            res = util_java.process_checkstyle_xml(res)
            # print(">>>res: ",res)
            url, rule_name, dsl_answer = gpt_checkstyle_dsls[ind]
            insert_index = 3
            one_rule = copy.deepcopy(all_rules[ind + 1][:insert_index])
            url, rule_name, *a = one_rule
            one_rule = [url, rule_name.strip(), *a] if "\n" in rule_name else [url, "4.8.6.1 Block comment style",
                                                                               *a] if "4.8.6 Block comment style" == rule_name else [
                url, rule_name, *a]
            key = all_rules[ind + 1][1] + '\n' + all_rules[ind + 1][2]
            flag_key = None
            for key2 in bench_mark:
                if key[:20] == key2[:20]:
                    flag_key = key2
                    break
            rule_description = javastyle_dsls[ind]
            if rule_description:
                # break
                toolruleset_des = few_checkstyle_dsls[ind]
                prompt = preprocess_promt(DSL_Syntax=dsl, style="RuleSet of Google Java Style Guide",
                                          DSLruleset=rule_description,
                                          tool="Checkstyle", toolruleset=toolruleset_des, grammar="Grammar", example="")


            else:
                prompt = "No need"
            one_rule.insert(insert_index, "" if "module" not in res else res)
            if "module" in res:
                one_rule.insert(insert_index, "Yes")
            else:
                one_rule.insert(insert_index, "No")
            one_rule.insert(insert_index, bench_mark[flag_key] if flag_key else "")
            # one_rule.insert(3, bench_mark[flag_key] if flag_key else "None")
            # one_rule.insert(3, prompt)

            # one_rule.insert(3, res)
            # one_rule.insert(3, javastyle_dsls_results[ind][2])
            csv_results.append(one_rule)

        util.save_csv(
            gpt_answer_dir + "metrics_res/1210/GLJava_Checkstyle_configuration_1210.csv",
            # GLJava_Checkstyle_configuration_1031.csv
            csv_results, ["url", "rule_name", "description", "benchmark", "gpt_answer", "gpt_configuration"])

        # for each_rule in res.split("\n") :
        #     csv_results


    parse_result()
