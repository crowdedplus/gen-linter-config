import re


def answer_is_wrong(answer):
    if "wrong" in answer.split("\n")[-1].lower():
        return True
    # elif "wrong" in answer:
    #     return True
    return False


def process_checkstyle_xml(res):
    index_xml = res.index("```xml") if "```xml" in res else None
    res = res[index_xml:] if index_xml else res
    res = res.replace("```xml", "")
    res = res.replace("```", "")
    if "Configuration:" in res:
        res = res.replace("Configuration:", "")

    # '''
    a = '<module name="TreeWalker">'

    if f"{a}" in res:
        # print(">>>>come here:")
        # answer.replace(answer,)
        res = res.replace(f"{a}", "")
        res = res[::-1]
        res = re.sub('</module>'[::-1], '', res, count=1)
        res = res[::-1]
    b = '<module name="Checker">'
    if f"{b}" in res:
        print(">>>co")
        res = res.replace(f"{b}", "")
        res = res[::-1]
        # if res.count("<module")<res.count("</module"):
        res = re.sub('</module>'[::-1], '', res, count=1)
        res = res[::-1]
    return res.strip()


def gen_csv(save_dir, file_name):
    pass


# dsl = '''RuleSet ::= Rule1 [And | Or | ; Rule2]* # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.
# Rule ::= ['Optional:' | 'Mandatory:']  # 'Optional:' means the rule is optional, 'Mandatory:' means the rule is mandatory
#          Constraint [ExceptionRule]* # Constraint can be one of the following types of rules.
# Constraint ::= TermList [Operator TermList]+ # TermList [Operator TermList]+ means the relationship of multiple TermList should satisfy
#              | TermList # Only TermList means TermList is allowed / required; 'Optional:' TermList means TermList is allowed; 'Mandatory:' TermList means TermList is required
#              | 'No' TermList # 'No' TermList means Prohibits TermList or TermList is allowed; 'Mandatory:' 'No' TermList means Prohibits TermList; 'Optional:' 'No' TermList means TermList is allowed
#              | 'Order of' TermList ['is'|'is not'] TermList # 'Order of' means order rule of TermList is TermList
#              | 'Order' ['is'|'is not'] TermList # 'Order' means order rule is TermList
#              | 'Number of' TermList [Operator TermList]* #'Number' means numberConstraint
#              | 'if' Rule1 'then' Rule2 # means Implied Relation Rule2 must be adhered to under the premise of Rule1
# ExceptionRule ::= 'Except' [TermList | Rule] # Special cases where rules don't apply.
# Operator ::= 'is'| 'is not' | 'in' | 'not in' | 'at' | 'not at' | 'on' | 'not on' | 'for' | 'not for' | 'before' | 'not before' | 'after' | 'not after' | 'between' | 'not between' | 'have' | 'not have' | '>=' | '<=' | '=' | '!=' | 'Add' | 'Sub' | 'Multiply' | ... # Operator means the relationship between TermList; Operator consists of at most two words; ... means using other operators if needed;
# TermList ::= Term [, Term]*
# Modifier ::= 'some' | 'each' | 'all' | 'except' | 'first' | 'last' | ...  # ... means use other modifiers if needed.
# Term ::= '[' JavaTerm ']' | Modifier* Term | Term 'of' Term # Complex terms can use modifiers or nesting.
# (Note JavaTerm is terminology used in the Java, its format like [XXX],XXX is JavaTerm)
# '''
dsl = '''RuleSet ::= Rule1 ['And' | 'Or' | ';' Rule2]* # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.
Rule ::= ['Optional:' | 'Mandatory:']  # 'Optional:' means the rule is optional, 'Mandatory:' means the rule is mandatory
         Constraint [ExceptionRule]* # Constraint can be one of the following types of rules.
Constraint ::= TermList [Operator TermList]+ # TermList [Operator TermList]+ means the relationship of multiple TermList should satisfy
             | 'No' TermList [Operator TermList]+ # 'No' TermList means Prohibits TermList or TermList is allowed; 'Mandatory:' 'No' TermList means Prohibits TermList; 'Optional:' 'No' TermList means TermList is allowed
             | 'Order of' TermList ['is'|'is not'] TermList # 'Order of' means order rule of TermList is TermList
             | 'Order' ['is'|'is not'] TermList # 'Order' means order rule is TermList
             | 'Number of' TermList [Operator TermList]* #'Number' means numberConstraint
             | 'if' Rule1 'then' Rule2 # means Implied Relation Rule2 must be adhered to under the premise of Rule1
ExceptionRule ::= 'Except' [TermList | Rule] # Special cases where rules don't apply.
Operator ::= 'is'| 'is not' | 'in' | 'not in' | 'for' | 'not for' | 'at' | 'not at' | 'on' | 'not on' |'before' | 'not before' | 'after' | 'not after' | 'between' | 'not between' | 'have' | 'not have' | '>=' | '<=' | '=' | '!=' | 'Add' | 'Sub' | 'Multiply' | ... # Operator means the relationship between TermList; Operator consists of at most two words; ... means using other operators if needed;
TermList ::= Term [, Term]*
Modifier ::= 'some' | 'each' | 'all' | 'except' | 'first' | 'last' | ...  # ... means use other modifiers if needed.
Term ::= '[' JavaTerm ']' | Modifier* Term | Term 'of' Term # Complex terms can use modifiers or nesting.
(Note JavaTerm is terminology used in the Java, its format like [XXX],XXX is JavaTerm)
'''
dsl = '''RuleSet   ::= Rule1 ['And' | 'Or' | ';' Rule2]*  # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.

Rule   ::= ['Optional:' | 'Mandatory:'] [Constraint | Exception] # ExceptionRule represents exceptions where the rule does not apply.

Constraint   ::= TermList [Operator TermList]+ # TermList [Operator TermList]+ means the relationship of multiple TermList should satisfy
             | 'No' TermList [Operator TermList]+ # 'No' TermList means Prohibits TermList [Operator TermList]+;
             | 'Order of' TermList ['is'|'is not'] TermList # 'Order of' means order rule of TermList is TermList
             | 'Order' ['is'|'is not'] TermList # 'Order' means order rule is TermList
             | 'Number of' TermList [Operator TermList]* #'Number' means numberConstraint
             | 'if' Rule1 'then' Rule2 # means Implied Relation Rule2 must be adhered to under the premise of Rule1 

Exception   ::= [Constraint] # means Exceptions that the rule does not apply.

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
'''

dsl = '''RuleSet   ::= Rule1 ['And' | 'Or' | ';' Rule2]*  # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.

Rule   ::= ['Optional:' | 'Mandatory:'] [Constraint] # 'Mandatory' means constraint must be satisfied, 'Optional' means constraint may be satisfied or not be satisfied, or not applied the constraint 

Constraint   ::= TermList [Operator TermList]+ # TermList [Operator TermList]+ means the relationship of multiple TermList should satisfy
             | 'No' TermList [Operator TermList]+ # 'No' TermList means Prohibits TermList [Operator TermList]+;
             | 'Order of' TermList ['is'|'is not'] TermList # 'Order of' means order of TermList is TermList
             | 'Order' ['is'|'is not'] TermList # 'Order' means order rule is TermList
             | 'Number of' TermList [Operator TermList]* #'Number' means numberConstraint
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
'''

dsl = '''RuleSet   ::= Rule1 ['And' | 'Or' | ';' Rule2]*  # 'And' means Rule1 and Rule2 both must be satisfied. 'Or' means satisfaction of either Rule1 or Rule2. ';' means Rule1 and Rule2 belong to different groups. '*' after ']' means repetition.

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
'''

Language = "Java"
Tool = "CheckStyle"
# check_all_prompt=f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration.
#
# 1. Determine whether objects that the rule in Google {Language} Style checks is same as objects that the matching rule in {Tool} checks. Otherwise, the matching rule is wrong, stop thinking.
# 2. If yes, analyze whether semantic of the rule in Google {Language} Style is same as the semantic of matching rule in {Tool}. Otherwise, the matching rule is wrong
#
# Respond with "Wrong" or "Correct".
# '''
# check_all_prompt=f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration.
#
# 1. Determine whether objects that the rule in Google {Language} Style checks is same as or more general than objects that the matching rule in {Tool} checks. Otherwise, the matching rule is wrong, stop thinking.
# 2. If yes, analyze whether semantic of the rule in Google {Language} Style is same as or more general than the semantic of matching rule in {Tool}. Otherwise, the matching rule is wrong
#
# Respond with "Wrong" or "Correct".
# '''
validation_prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:

1. If StyleSEM检查的行为 和 ToolSEM rule 不是一个内容? If 是一个内容, 则进行第二步
2. Does JavaTerms enclosed with "[]" of StyleSEM rule more restrictive than JavaTerms enclosed with "[]" by 考虑被设置的option values of ToolSEM? If restrictive, 则是No. 否则Yes

**Mapping:**
1. Mandatory: No [LineWrap] of [ImportStatement] 
   >>> 
   Option Rule:
   option 1: tokens; "IMPORT, STATIC_IMPORT"; Mandatory: No [line wrap] of {{tokens}}

2. **Mandatory: No [WildcardImport]**
   >>> 
   Option Rule:
   option 1: allowClassImports; false; Mandatory: No [starred class imports]


3. Mandatory: No [StaticWildcardImport] 
   >>> 
   Basic Rule: Mandatory: No [static import statements]
   Option Rule:
   None

4. Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]  
   >>>  
   RuleName: SingleSpaceSeparator  
   Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

5. Mandatory: [TopLevelClass] is in [SourceFile] 
   >>> 
   RuleName: OneTopLevelClass
   Basic Rule: 
   Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

6. Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
   >>> 
   Option Rule:
   option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

7. Mandatory: [PackageStatement]**
   >>> 
   RuleName: PackageDeclaration
   Basic Rule: Mandatory: [class] have [package declaration]
   Option Rule: None 

Response Format:
Mapping 1: Yes或者No  Explanation: ...
Mapping 2: ...
...
'''
validation_asw = '''Mapping 1: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** The content is not the same. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses horizontal alignment in general.
- **Conclusion:** No

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

- **Step 1:** The content is not same. StyleSEM prohibits concise format of empty block, while ToolSEM prohibits empty block. 
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** The content is the same as both rules address the placement of top-level classes in source files.
- **Step 2:** The JavaTerms in StyleSEM ([TopLevelClass]) are more restrictive than those in ToolSEM ([top-level class, interface, enum, or annotation]). Therefore, StyleSEM is more restrictive.
- **Conclusion:** No'''
validation_prompt = '''Mapping 1: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** The content is not the same. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses horizontal alignment in general.
- **Conclusion:** No

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

- **Step 1:** The content is not same. StyleSEM prohibits concise format of empty block, while ToolSEM prohibits empty block. 
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** The content is the same as both rules address the placement of top-level classes in source files.
- **Step 2:** The JavaTerms in StyleSEM ([TopLevelClass]) are more restrictive than those in ToolSEM ([top-level class, interface, enum, or annotation]). Therefore, StyleSEM is more restrictive.
- **Conclusion:** No'''
validation_prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:

1. Check if the rule type of StyleSEM rule is same as the rule of type of ToolSEM rule? If same rule type, 则进行第二步. 否则No.
2. If StyleSEM检查的约束关系 和 ToolSEM rule 的约束关系是一致的? If 是是一致的, 则进行第三步
3. Does JavaTerms enclosed with "[]" of StyleSEM rule more restrictive than JavaTerms enclosed with "[]" and setted option values of ToolSEM? If restrictive, 则是No. 否则Yes

**Mapping:**
1. Mandatory: if Number of [statement] of [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] = 1 then [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
   >>> 
   Basic Rule: None
   Option Rule:
   option 1: allowSingleLineStatement; false; Mandatory: if Number of [statement] of [body] is 1 then [body] have [Brace]
   option 2: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_FOR, LITERAL_DO, LITERAL_WHILE"; Mandatory: [block] of {{tokens}} have [Brace]

2. Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]  
   >>>  
   RuleName: SingleSpaceSeparator  
   Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

3. Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
   >>> 
   Option Rule:
   option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

4. Mandatory: [TopLevelClass] is in [SourceFile] 
   >>> 
   RuleName: OneTopLevelClass
   Basic Rule: 
   Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

5. Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock] 
   >>> 
   RuleName: AnnotationLocation
   Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{tokens}} is after [documentation block] and before [target element]

6. **Mandatory: No increase in [IndentationLevel] for [Annotation]**
   >>> 
   Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{basicOffset}} when on [next line]

Response Format:
Mapping 1: Yes或者No  Explanation: ...
Mapping 2: ...
...
'''

validation_asw = '''Mapping 1: Yes  Explanation:
1. StyleSEM: Mandatory: if Number of [statement] of [body] of [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] = 1 then [IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement] have [Brace]
2. ToolSEM: Option Rule:
   option 1: allowSingleLineStatement; false; Mandatory: if Number of [statement] of [body] is 1 then [body] have [Brace]
   option 2: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_FOR, LITERAL_DO, LITERAL_WHILE"; Mandatory: [block] of {{tokens}} have [Brace]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of Annotation after documentation block.
- **Step 3:** The JavaTerms in StyleSEM ([IfStatement], [ElseStatement], [ForStatement], [DoStatement], [WhileStatement]) is not more restrictive than "LITERAL_IF, LITERAL_ELSE, LITERAL_FOR, LITERAL_DO, LITERAL_WHILE" in ToolSEM.
- **Conclusion:** Yes

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not the same. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses horizontal alignment in general.
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not same. StyleSEM checks the No concise format of empty block, while ToolSEM checks no empty block. 
- **Conclusion:** No

Mapping 4: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of top-level classes in source files.
- **Step 3:** The JavaTerms in StyleSEM ([TopLevelClass]) are more restrictive than those in ToolSEM ([top-level class, interface, enum, or annotation]). Therefore, StyleSEM is more restrictive.
- **Conclusion:** No

Mapping 5: Yes  Explanation:
1. StyleSEM: Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock]
2. ToolSEM: Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{tokens}} is after [documentation block] and before [target element]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of Annotation after documentation block.
- **Step 3:** The JavaTerms in StyleSEM ([Annotation] of [Field]) is not more restrictive than "VARIABLE_DEF" in ToolSEM. .
- **Conclusion:** Yes

Mapping 6: No  Explanation:
1. StyleSEM: Mandatory: No increase in [IndentationLevel] for [Annotation]
2. ToolSEM: Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{basicOffset}} when on [next line]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of IndentationLevel.
- **Step 3:** The JavaTerms in StyleSEM ([IndentationLevel] for [Annotation]) is more restrictive than ToolSEM for any Java Code.
- **Conclusion:** No
'''
validation_prompt = '''For the following Mapping, for each rule of before ">>>" as StyleSEM, after ">>>>" rule as ToolSEM determine:
ToolSEM rule = basic rule + all option rules,把option rule中{{XXX}}用option values进行替换!

1. Check if the rule type of StyleSEM rule is same as the rule of type of ToolSEM rule? If same rule type, 则进行第二步. 否则, Answer is No.
2. If StyleSEM Rule检查的约束关系 is more restrictive than ToolSEM rule 的约束关系? If 是more restrictive, 则Answer is No. 否则进行第三步
3. Does JavaTerms enclosed with "[]" of StyleSEM rule more restrictive than JavaTerms enclosed with "[]" and option values of option names of ToolSEM? If restrictive, 则是No. 否则Yes

**Mapping:**
1. Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]  
   >>>  
   RuleName: SingleSpaceSeparator  
   Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

2. Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
   >>> 
   Option Rule:
   option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{tokens}} is not [Empty]

3. Mandatory: [TopLevelClass] is in [SourceFile] 
   >>> 
   RuleName: OneTopLevelClass
   Basic Rule: 
   Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

4. Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock] 
   >>> 
   RuleName: AnnotationLocation
   Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{tokens}} is after [documentation block] and before [target element]

5. **Mandatory: No increase in [IndentationLevel] for [Annotation]**
   >>> 
   Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{basicOffset}} when on [next line]

Response Format:
Mapping 1: Yes或者No  Explanation: ...
Mapping 2: ...
...
'''
validation_asw = '''Mapping 1: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not the same. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses prohibit horizontal alignment.
- **Conclusion:** No

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY}} is not [Empty]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is more restrictive. StyleSEM checks the No concise empty block, while ToolSEM checks no empty block. 
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of top-level classes in source files.
- **Step 3:** The JavaTerms in StyleSEM ([TopLevelClass]) are more restrictive than those in ToolSEM ([top-level class, interface, enum, or annotation]). Therefore, StyleSEM is more restrictive.
- **Conclusion:** No

Mapping 4: Yes  Explanation:
1. StyleSEM: Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock]
2. ToolSEM: Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{VARIABLE_DEF}} is after [documentation block] and before [target element]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of Annotation after documentation block.
- **Step 3:** The JavaTerms in StyleSEM ([Annotation] of [Field]) is not more restrictive than "VARIABLE_DEF" in ToolSEM. .
- **Conclusion:** Yes

Mapping 5: No  Explanation:
1. StyleSEM: Mandatory: No increase in [IndentationLevel] for [Annotation]
2. ToolSEM: Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{0}} when on [next line]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of IndentationLevel.
- **Step 3:** The JavaTerms in StyleSEM ([IndentationLevel] for [Annotation]) is more restrictive than ToolSEM for any Java Code.
- **Conclusion:** No
'''
validation_asw = '''Mapping 1: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not the same. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses prohibit horizontal alignment.
- **Conclusion:** No

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY}} is not [Empty]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not same. StyleSEM checks the No concise empty block, while ToolSEM checks no empty block. 
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of top-level classes in source files.
- **Step 3:** the set of situations for the StyleSEM rule is not a superset of the ToolSEM set ([top-level class, interface, enum, or annotation]). Therefore, the answer is No.
- **Conclusion:** No

Mapping 4: Yes  Explanation:
1. StyleSEM: Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock]
2. ToolSEM: Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{VARIABLE_DEF}} is after [documentation block] and before [target element]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of Annotation after documentation block.
- **Step 3:** the set of situations for the StyleSEM rule ([Annotation] of [Field] is [After] [DocumentationBlock]) is a superset of [annotation] of "VARIABLE_DEF" is after [documentation block] and before [target element].
- **Conclusion:** Yes

Mapping 5: No  Explanation:
1. StyleSEM: Mandatory: No increase in [IndentationLevel] for [Annotation]
2. ToolSEM: Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{0}} when on [next line]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of IndentationLevel.
- **Step 3:** the set of situations for the StyleSEM rule ([IndentationLevel] for [Annotation]) is not a superset of ToolSEM rule.
- **Conclusion:** No
'''

validation_asw_satisfy = '''Mapping 1: No  Explanation:
1. StyleSEM: Mandatory: No [VariableNumberOfSpaces] to [AlignTokens] with [PreviousLines]
2. ToolSEM: Basic Rule: Mandatory: [horizontal alignment] is not [permitted]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not 相似. StyleSEM addresses variable spaces for alignment, while ToolSEM addresses prohibit horizontal alignment.
- **Conclusion:** No

Mapping 2: No  Explanation:
1. StyleSEM: Mandatory: No [ConciseEmptyBlock] in [MultiBlockStatement] of [IfElse] or [TryCatchFinally]
2. ToolSEM: Option Rule: option 1: tokens; "LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY"; Mandatory: [block] of {{LITERAL_IF, LITERAL_ELSE, LITERAL_TRY, LITERAL_CATCH, LITERAL_FINALLY}} is not [Empty]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is not 相似. StyleSEM checks the No concise empty block, while ToolSEM checks no empty block. 
- **Conclusion:** No

Mapping 3: No  Explanation:
1. StyleSEM: Mandatory: [TopLevelClass] is in [SourceFile]
2. ToolSEM: Basic Rule: Mandatory: [top-level class, interface, enum, or annotation] resides in [its own source file]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of top-level classes in source files.
- **Step 3:** the set of situations for the StyleSEM rule is not a superset of the ToolSEM set ([top-level class, interface, enum, or annotation]). Therefore, the answer is No.
- **Conclusion:** No

Mapping 4: Yes  Explanation:
1. StyleSEM: Mandatory: [Annotation] of [Field] is [After] [DocumentationBlock]
2. ToolSEM: Basic Rule: Mandatory: [annotation] is after [documentation block] and before [target element]
   Option Rule:
   option 1: tokens; "VARIABLE_DEF"; Mandatory: [annotation] of {{VARIABLE_DEF}} is after [documentation block] and before [target element]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of Annotation after documentation block.
- **Step 3:** the set of situations for the StyleSEM rule ([Annotation] of [Field] is [After] [DocumentationBlock]) is a superset of [annotation] of "VARIABLE_DEF" is after [documentation block] and before [target element].
- **Conclusion:** Yes

Mapping 5: No  Explanation:
1. StyleSEM: Mandatory: No increase in [IndentationLevel] for [Annotation]
2. ToolSEM: Basic Rule: Mandatory: [Indentation] is [correct] for [Java code]
   Option Rule:
   option 1: basicOffset; 0; Mandatory: [new indentation level] is indented by {{0}} when on [next line]

- **Step 1:** Rule types of StyleSEM rule is Mandatory, and ToolSEM rule is Mandatory, is same
- **Step 2:** The 约束关系 is the same as both rules address the placement of IndentationLevel.
- **Step 3:** the set of situations for the StyleSEM rule ([IndentationLevel] for [Annotation]) is not a superset of ToolSEM rule.
- **Conclusion:** No
'''
validation_previous_msg = [validation_prompt, validation_asw]

check_all_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 

1. Determine whether objects that the rule in Google {Language} Style checks is more general than objects that the matching rule in {Tool} checks. 
2. If GJS rule is more specific, WRONG!!! stop thinking.
3. analyze semantic of the rule in Google {Language} Style and the semantic of matching rule in {Tool}. 
4. Compare whether the semantic of the rule in Google {Language} Style is equivalent to the semantic of matching rule in {Tool}.
5. If CSLs is more general, WRONG!!!  Otherwise, Correct!
6. If CSLs is more specific, Correct!

Respond with "Wrong" or "Correct".
'''
# 1. Analyze the objects and functionality of GJS and CSLs.

check_all_prompt_2 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the functionality of GJS and CSLs.
2. If objects of CSLs rule specifically have objects of GJS, and functionality of GJS and CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or functionality of GJS and CSLs is not same, Wrong!!!

Give analysis, finally, Respond with "Wrong" or "Correct".
'''
check_all_prompt_4 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the functionality of GJS and possible matching rule of CSLs.
2. If objects of possible matching rule of CSLs rule specifically have objects of GJS, and functionality of GJS and possible matching rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or functionality of GJS and possible matching rule of CSLs is not same, Wrong!!!

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the functionality of GJS and possible matching rule of CSLs.
2. If objects of subsets rule of CSLs specifically have objects of GJS, and functionality of GJS and subsets rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or functionality of GJS and subsets rule of CSLs is not same, Wrong!!!

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
2. If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!!

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
2. If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!! 
4. If objects of GJS rule is more general, and semantics of GJS and subsets rule of CSLs is same, Correct!!! 


Give analysis, finally, Respond with "Wrong" or "Correct".
'''
check_all_prompt_5_imprv = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. First Analyze Basic Rules of CheckStyle based on the following steps
    1.1 Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
    1.2 If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
    1.3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Go to Step 2!!! 

2. If CSLs has Option Rules, Analyze Option Rules of CSLs based on the following steps
    2.1 Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
    2.2 If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
    2.3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!! 

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5_imprv2 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. First Analyze Basic Rules of CheckStyle based on the following steps
    1.1 Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
    1.2 If objects of subsets rule of CSLs are basically same as the objects of GJS, and semantics of GJS and subsets rule of CSLs is basically same, Correct!!!
    1.3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Go to Step 2!!! 

2. If CSLs has Option Rules, Analyze Option Rules of CSLs based on the following steps
    2.1 Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
    2.2 If objects of subsets rule of CSLs  are basically same as objects of GJS, and semantics of GJS and subsets rule of CSLs is basically same, Correct!!!
    2.3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!! 

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5_simple = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
2. If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!! 

Give analysis, finally, Respond with "Wrong" or "Correct".
'''

check_all_prompt_5_each_rule = f'''For each rule in RuleSet of Google {Language} Style Guide (GJS), determine whether there exists matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects and the semantics of GJS and possible matching rule of CSLs.
2. If objects of subsets rule of CSLs specifically have objects of GJS, and semantics of GJS and subsets rule of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or semantics of GJS and subsets rule of CSLs is not same, Wrong!!!

for each mapping, respond with "Correct" or "Wrong"
'''
check_all_prompt_3 = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. Analyze the objects of GJS and CSLs that checks and the functionality of GJS and CSLs.
2. If objects of CSLs rule is more specific, and functionality of GJS and CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or functionality of GJS and CSLs is not same, Wrong!!!

Respond with "Wrong" or "Correct".
'''

check_all_prompt_2_option = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration is correct or wrong. 
1. If CSL has Option rule with set option values, only analyze the objects and the functionality of GJS and Option rule with set option values of CSLs.
2. If objects of Option rules of CSLs rule specifically have objects of GJS, and functionality of GJS and Option rules of CSLs is same, Correct!!!
3. If objects of GJS rule is more specific, or functionality of GJS and Option rules of CSLs is not same, Wrong!!!

Respond with "Wrong" or "Correct".
'''
check_all_prompt_option = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 

1. Determine whether objects that the rule in Google {Language} Style checks is same as objects that the matching rule in {Tool} checks. 
2. If no, determine whether objects that the rule in Google {Language} Style checks is same as objects of Option rules and option values in {Tool} checks. 
3. If no, the matching rule is wrong, stop thinking.
4. If yes, analyze whether semantic of the rule in Google {Language} Style is same as the semantic of matching rule in {Tool}. 
5. If yes, matching rule is correct! stop thinking.
6. If no, analyze whether Option rules and option values of semantic of the rule in Google {Language} Style is same as the semantic of matching rule in {Tool}. Otherwise, the matching rule is wrong

Please analyze based on the above steps!

Respond with "Wrong" or "Correct".
'''
check_all_objects_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. Extract objects that GJS checks and objects that the matching rule in CSLs checks.
2. Compare whether objects that the matching rule in CSLs checks is equivalent to objects that GJS checks.
3. If CSLs is more general or rather different in scope, WRONG!!!
4. If CSLs is more specific or more limited in scope, Correct!!!
Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}
'''
check_all_semantic_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. Analyze semantics of GJS and the semantic of CSLs.
2. Compare whether the semantic of the matching rule in CSLs is equivalent to the semantic of GJS.
3. If CSLs is more general, WRONG!!!  Otherwise, Correct!
Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}
'''
check_type_prompt_total = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 
For the above configuration, GJS is on the left of ">>>" starting with "Mandatory" or "Optional", and CSLs are on the right of ">>>" consisting of RuleName, basic rules and Option Rule.

1. Extract GJS and corresponding matching rules from basic rules and Option Rule of CSLs.
2. Extract rule type ("Mandatory" or "Optional") of GJS
3. Extract rule type ("Mandatory" or "Optional") of the matching rules in {Tool} (CSLs).
4. If rule type ("Mandatory" or "Optional") of GJS is Optional and rule type ("Mandatory" or "Optional") of the matching rules in CSL is Mandatory, matching rules is WRONG!!! 
Respond with "Wrong" or "Correct".
    '''
check_objects_prompt_total = '''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 
For the above configuration, GJS is on the left of ">>>" starting with "Mandatory" or "Optional", and CSLs are on the right of ">>>" consisting of RuleName, basic rules and Option Rule.

1. Extract GJS and corresponding matching rules from basic rules and Option Rule of CSLs.
2. Extract objects that GJS checks. 
3. Extract objects by combining basic rules with Option rules that CSLs checks.
4. Compare whether objects that GJS checks is equivalent to objects by combining basic rules with Option rules that CSLs checks.
5. If CSLs by combining basic rules with Option rules of CSLs is more general or rather different in scope, WRONG!!!

Respond with "Wrong" or "Correct".
    '''
check_semantics_prompt_total = '''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding matching rules of CheckStyle (CSLs) from the above Configuration. 
For the above configuration, GJS is on the left of ">>>" starting with "Mandatory" or "Optional", and CSLs are on the right of ">>>" consisting of RuleName, basic rules and Option Rule.

1. Extract GJS (left of ">>>") and corresponding matching rules from basic rules and Option Rule of CSLs (right of ">>>").
2. Analyze semantics of GJS.
3. Analyze semantic by combining basic rules with Option rules of CSLs.
4. Compare whether the semantic by combining basic rules with Option rules of CSLs is equivalent to the semantic of GJS.
5. If CSLs by combining basic rules with Option rules of CSLs is more general, WRONG!!! 
Respond with "Wrong" or "Correct".
'''

# For the above configuration, GJS is on the left of ">>>", CSLs are on the right of ">>>" consisting of RuleName, basic rules and Option Rule.

check_type_prompt = '''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding basic rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. Extract rule type ("Mandatory" or "Optional") of GJS and rule type ("Mandatory" or "Optional") of the matching basic rules in {Tool} (CSLs).
2. If rule type ("Mandatory" or "Optional") of GJS is Optional and rule type ("Mandatory" or "Optional") of CSL is Mandatory, matching basic rules is WRONG!!! 
Respond with "Wrong" or "Correct".
    '''
check_objects_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding basic rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. Extract objects that GJS checks and objects that basic rules in CSLs checks.
2. Compare whether objects that basic rules in CSLs checks is equivalent to objects that GJS checks.
3. If basic rules in CSLs is more general or rather different in scope, WRONG!!!
4. If basic rules in CSLs is more specific or more limited in scope, Correct!!!
Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}
    '''
check_semantics_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding basic rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. Analyze semantics of GJS and the semantic of basic rules in CSLs.
2. Compare whether the semantic of basic rules in CSLs is equivalent to the semantic of GJS.
3. If basic rules in CSLs is more general, WRONG!!!  Otherwise, Correct!
Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}
'''

check_hasOptionRule_prompt = '''For the above configuration, the rule of Google {Language} Style Guide (GJS) is on the left of ">>>" and the corresponding rules of CheckStyle (CSLs) are on the right. 
Determine whether CSLs have Option Rules. 
Respond with "Yes" or "No".
   '''

check_option_type_prompt = '''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding Option rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. If CSL has Option rule with set option values, extract rule type ("Mandatory" or "Optional") of GJS and rule type ("Mandatory" or "Optional") of Option rule with set option values from CSLs.
2. If GJS is Optional, and matching option rules with set option values in CSL is Mandatory, WRONG!!!  Otherwise, Correct!
Respond with "Wrong" or "Correct".                '''
check_option_obj_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding Option rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. If CSL has Option rule with set option values, only extract objects that Option rule of CSLs checks
2. extract objects that GJS checks.
3. Compare whether the objects that Option rule of CSL check is equivalent to the objects that GJS check.
4. If the option rule of CSLs is more general or rather different in scope, WRONG!!!
5. If the option rule of CSLs is more specific or more limited in scope, Correct!!!

Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}'''
check_option_semantics_prompt = f'''For the rule in RuleSet of Google {Language} Style Guide (GJS), determine whether the corresponding Option rules of CheckStyle (CSLs) from the above Configuration. 
GJS consist of rules without rulename and option rules, and CSLs consists of RuleName, basic rules and Option Rule.

1. If CSL has Option rule with set option values, only analyze the semantic of Option rule of CSLs
2. analyze the semantic of GJS.
3. Then, compare whether the semantic of Option rule of CSLs is equivalent to the semantic of GJS.
4. If the option rule of CSLs is more general, WRONG!!!  Otherwise, Correct!
Respond with "Wrong" or "Correct".

Rule expressed in Grammar:
{dsl}'''

example_extract_each_map_xml = [['''Extract each Mapping and XML Configuration from the following Text. If no configurations, gives None. 

Text:
### Step-by-Step Analysis:

#### Step 1: Identify matching rules from Basic rules in Checkstyle

- **RuleSet of Google Java Style Guide:**
  - **Mandatory: [LineBreak] before [NonAssignmentOperator]**

- **Checkstyle:**
  - **RuleName: OperatorWrap**
    - **Basic Rule:**
      - **Mandatory: [line] wrap on [operator]**

This matches the Google Java Style Guide rule as it specifies mandatory line wrapping on operators.

#### Step 2: Identify related option names, data types, and matching option rules from Option rules in Checkstyle

- **Checkstyle:**
  - **RuleName: OperatorWrap**
    - **Option Rule:**
      - **option: WrapOption; {nl, eol}**
        - **nl: Mandatory: [operator] is on [new line]**
        - **eol: Mandatory: [operator] is at [end of line]**
      - **tokens: String[]; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}**
        - **String[]: Mandatory: [line] wrap on [operator] of {{tokens}}**

#### Step 3: Instantiate complete option values of related option names based on data type, objects, and semantics of the rule in RuleSet of Google Java Style Guide

- **Option Name: WrapOption**
  - **Data Type: Enum**
  - **Value: nl**
  - **Semantics: [operator] is on [new line]**

- **Option Name: tokens**
  - **Data Type: String[]**
  - **Value: {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}**
  - **Semantics: [line] wrap on [operator] of {{tokens}}**

#### Step 4: Ensure option values are valid for data type and value range in Option rules in Checkstyle

- **WrapOption: nl** is valid as it is within the value range {nl, eol}.
- **tokens: {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}** is valid as it is within the value range.

#### Step 5: Check whether miss related option name and option values for objects of the rule in RuleSet of Google Java Style Guide

- No related option names or option values are missed.

#### Step 6: Ensure the semantics of matching RuleNames and Option values is consistent with the rule in RuleSet of Google Java Style Guide

- The semantics of **OperatorWrap** with **WrapOption: nl** and **tokens** is consistent with the Google Java Style Guide rule **Mandatory: [LineBreak] before [NonAssignmentOperator]**.

### Configuration:

1. **RuleSet of Google Java Style Guide:**
   - **Mandatory: [LineBreak] before [NonAssignmentOperator]**
   - **>>>**
   - **Checkstyle:**
     - **RuleName: OperatorWrap**
       - **Basic Rule:**
         - **Mandatory: [line] wrap on [operator]**
       - **Option Rule:**
         - **WrapOption; nl; Mandatory: [operator] is on [new line]**
         - **tokens; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}; Mandatory: [line] wrap on [operator] of {{tokens}}**

### Summary:

```xml
<module name='OperatorWrap'>
    <property name='WrapOption' value='nl'/>
    <property name='tokens' value='QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF'/>
</module>
```

This configuration ensures that the rule from the Google Java Style Guide is correctly mapped to the corresponding Checkstyle rule with the appropriate options.'''
                                    ,
                                 '''Configuration:
                               **Each Mapping:**
                               1. Mandatory: [LineBreak] before [NonAssignmentOperator] >>>
                                    RuleName: OperatorWrap
                                    Basic Rule:
                                    Mandatory: [line] wrap on [operator]
                               
                                    Option Rule:
                                    WrapOption; nl; Mandatory: [operator] is on [new line]**
                                    tokens; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}; Mandatory: [line] wrap on [operator] of {{tokens}}**
                               
                               **XML Configuration:**
                               ```xml
                               <module name='OperatorWrap'>
                                   <property name='WrapOption' value='nl'/>
                                   <property name='tokens' value='QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF'/>
                               </module>
                               ''']]

example_eachMap = [['''Extract each Mapping from the following Text. If no configurations, gives None. 

Text:
### Step-by-Step Analysis:

#### Step 1: Identify matching rules from Basic rules in Checkstyle

- **RuleSet of Google Java Style Guide:**
  - **Mandatory: [LineBreak] before [NonAssignmentOperator]**

- **Checkstyle:**
  - **RuleName: OperatorWrap**
    - **Basic Rule:**
      - **Mandatory: [line] wrap on [operator]**

This matches the Google Java Style Guide rule as it specifies mandatory line wrapping on operators.

#### Step 2: Identify related option names, data types, and matching option rules from Option rules in Checkstyle

- **Checkstyle:**
  - **RuleName: OperatorWrap**
    - **Option Rule:**
      - **option: WrapOption; {nl, eol}**
        - **nl: Mandatory: [operator] is on [new line]**
        - **eol: Mandatory: [operator] is at [end of line]**
      - **tokens: String[]; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}**
        - **String[]: Mandatory: [line] wrap on [operator] of {{tokens}}**

#### Step 3: Instantiate complete option values of related option names based on data type, objects, and semantics of the rule in RuleSet of Google Java Style Guide

- **Option Name: WrapOption**
  - **Data Type: Enum**
  - **Value: nl**
  - **Semantics: [operator] is on [new line]**

- **Option Name: tokens**
  - **Data Type: String[]**
  - **Value: {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}**
  - **Semantics: [line] wrap on [operator] of {{tokens}}**

#### Step 4: Ensure option values are valid for data type and value range in Option rules in Checkstyle

- **WrapOption: nl** is valid as it is within the value range {nl, eol}.
- **tokens: {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}** is valid as it is within the value range.

#### Step 5: Check whether miss related option name and option values for objects of the rule in RuleSet of Google Java Style Guide

- No related option names or option values are missed.

#### Step 6: Ensure the semantics of matching RuleNames and Option values is consistent with the rule in RuleSet of Google Java Style Guide

- The semantics of **OperatorWrap** with **WrapOption: nl** and **tokens** is consistent with the Google Java Style Guide rule **Mandatory: [LineBreak] before [NonAssignmentOperator]**.

### Configuration:

1. **RuleSet of Google Java Style Guide:**
   - **Mandatory: [LineBreak] before [NonAssignmentOperator]**
   - **>>>**
   - **Checkstyle:**
     - **RuleName: OperatorWrap**
       - **Basic Rule:**
         - **Mandatory: [line] wrap on [operator]**
       - **Option Rule:**
         - **WrapOption; nl; Mandatory: [operator] is on [new line]**
         - **tokens; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}; Mandatory: [line] wrap on [operator] of {{tokens}}**

### Summary:

```xml
<module name='OperatorWrap'>
    <property name='WrapOption' value='nl'/>
    <property name='tokens' value='QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF'/>
</module>
```

This configuration ensures that the rule from the Google Java Style Guide is correctly mapped to the corresponding Checkstyle rule with the appropriate options.
'''

                       , '''Configuration:
**Each Mapping:**
Mandatory: [LineBreak] before [NonAssignmentOperator] >>>
     RuleName: OperatorWrap

     Basic Rule:
     Mandatory: [line] wrap on [operator]

     Option Rule:
     WrapOption; nl; Mandatory: [operator] is on [new line]
     tokens; {QUESTION, COLON, EQUAL, NOT_EQUAL, DIV, PLUS, MINUS, STAR, MOD, SR, BSR, GE, GT, SL, LE, LT, BXOR, BOR, LOR, BAND, LAND, LITERAL_INSTANCEOF, TYPE_EXTENSION_AND, ASSIGN, DIV_ASSIGN, PLUS_ASSIGN, MINUS_ASSIGN, STAR_ASSIGN, MOD_ASSIGN, SR_ASSIGN, BSR_ASSIGN, SL_ASSIGN, BXOR_ASSIGN, BOR_ASSIGN, BAND_ASSIGN, METHOD_REF}; Mandatory: [line] wrap on [operator] of {{tokens}}**

''']]

example_eachMap_config = [['''Extract each Mapping from the following Text. If no configurations, gives None. 

Text:
1 ### Step-by-Step Analysis

#### Rule 1: 
**Google Java Style Guide Rule:**
Mandatory: No [WhitespaceCharacter] except [HorizontalSpaceCharacter] in [SourceFile]

**Step 1: Identify possible matching rules from Basic rules in Checkstyle:**
- No exact match found in the provided Checkstyle rules.

**Step 2: Identify related option rules:**
- No related option rules found in the provided Checkstyle rules.

**Step 3: Configure/Set/Instantiate corresponding option values:**
- Not applicable as no matching option rules were found.

**Step 4: Ensure option values are valid:**
- Not applicable as no matching option rules were found.

**Configuration:**
1. Mandatory: No [WhitespaceCharacter] except [HorizontalSpaceCharacter] in [SourceFile] >>> None

#### Rule 2:
**Google Java Style Guide Rule:**
Mandatory: [WhitespaceCharacter] in [StringLiteral], [CharacterLiteral] is [Escaped]

**Step 1: Identify possible matching rules from Basic rules in Checkstyle:**
- No exact match found in the provided Checkstyle rules.

**Step 2: Identify related option rules:**
- No related option rules found in the provided Checkstyle rules.

**Step 3: Configure/Set/Instantiate corresponding option values:**
- Not applicable as no matching option rules were found.

**Step 4: Ensure option values are valid:**
- Not applicable as no matching option rules were found.

**Configuration:**
2. Mandatory: [WhitespaceCharacter] in [StringLiteral], [CharacterLiteral] is [Escaped] >>> None

#### Rule 3:
**Google Java Style Guide Rule:**
Mandatory: No [TabCharacter] for [Indentation]

**Step 1: Identify possible matching rules from Basic rules in Checkstyle:**
- RuleName: FileTabCharacter
  - Basic Rule: Mandatory: No [tab characters] in [source code]

**Step 2: Identify related option rules:**
- eachLine option:
  - datatype: boolean; value range: {true, false}; default value: false
  - true: Mandatory: each [line] containing [tab character] is reported
  - false: Optional: only the first [line] containing [tab character] is reported

- fileExtensions option:
  - datatype: String[]; value range: all files; default value: all files
  - Mandatory: [file extensions] of [files] to process is {{fileExtensions}}

**Step 3: Configure/Set/Instantiate corresponding option values:**
- eachLine option: true (to ensure each line containing a tab character is reported)
- fileExtensions option: all files (default value)

**Step 4: Ensure option values are valid:**
- eachLine option: true (valid boolean value)
- fileExtensions option: all files (valid String[] value)

**Configuration:**
3. Mandatory: No [TabCharacter] for [Indentation] >>> 
    RuleName: FileTabCharacter; 
    Mandatory: No [tab characters] in [source code]

    Option Rule:
    eachLine; true; Mandatory: each [line] containing [tab character] is reported
    fileExtensions; all files; Mandatory: [file extensions] of [files] to process is {{fileExtensions}}

### Summary:
**Final configurations of Checkstyle in XML format:**
```xml
<module name='FileTabCharacter'>
    <property name='id' value='identifier'/>
    <property name='eachLine' value='true'/>
    <property name='fileExtensions' value='all files'/>
</module>
```'''
                              , '''Configuration:
**Each Mapping:**
1. Mandatory: No [WhitespaceCharacter] except [HorizontalSpaceCharacter] in [SourceFile] >>> None

2. Mandatory: [WhitespaceCharacter] in [StringLiteral], [CharacterLiteral] is [Escaped] >>> None

3. Mandatory: No [TabCharacter] for [Indentation] >>> 
    RuleName: FileTabCharacter; 
    Mandatory: No [tab characters] in [source code]

    Option Rule:
    eachLine; true; Mandatory: each [line] containing [tab character] is reported
    fileExtensions; all files; Mandatory: [file extensions] of [files] to process is {{fileExtensions}}

**XML Configuration:**
```xml
<module name='FileTabCharacter'>
    <property name='id' value='identifier'/>
    <property name='eachLine' value='true'/>
    <property name='fileExtensions' value='all files'/>
</module>
''']]
example_config_json = [['''Extract the final XML configuration in {{tool}} from the following Text. 

Text:
Let's analyze the given configurations and correctness information step by step.

### Original Configurations

**Each Mapping:**
1. Optional: [LineWrapping] is for [Code] [that [FitsWithinColumnLimit]] >>> 
    RuleName: LineLength
    Basic Rule: Mandatory: Number of [line length] <= 80
    Option Rule:
    max option: 80; Mandatory: Number of [line length] <= {{max}}

2. Optional: [ExtractMethod] or [ExtractLocalVariable] is for [AvoidLineWrapping] >>> 
    RuleName: MethodLength
    Basic Rule: Mandatory: Number of [lines] <= 150
    Option Rule:
    max option: 150; Mandatory: Number of [lines] <= {{max}}

**XML Configuration:**
```xml
<module name='LineLength'>
  <property name='id' value='identifier'/>
  <property name='max' value='80'/>
</module>

<module name='MethodLength'>
  <property name='id' value='identifier'/>
  <property name='max' value='150'/>
</module>
```

### Correctness Information of Each Mapping

Let's assume the correctness information is as follows:

1. LineLength mapping: Correct
2. MethodLength mapping: Wrong

### Steps to Modify Original Configurations

1. **Extract Each Mapping from Original Configurations:**
   - Mapping 1: LineLength
   - Mapping 2: MethodLength

2. **Extract the Correctness of Each Mapping:**
   - LineLength: Correct
   - MethodLength: Wrong

3. **Modify Configurations Based on Correctness:**
   - Since LineLength is correct, we keep it.
   - Since MethodLength is wrong, we remove it.

### Final Correct Configurations

**Each Mapping:**
1. Optional: [LineWrapping] is for [Code] [that [FitsWithinColumnLimit]] >>> 
    RuleName: LineLength
    Basic Rule: Mandatory: Number of [line length] <= 80
    Option Rule:
    max option: 80; Mandatory: Number of [line length] <= {{max}}

**XML Configuration:**
```xml
<module name='LineLength'>
  <property name='id' value='identifier'/>
  <property name='max' value='80'/>
</module>
```

### Analysis Results

**Configuration:**
**Each Mapping:**
1. Optional: [LineWrapping] is for [Code] [that [FitsWithinColumnLimit]] >>> 
    RuleName: LineLength
    Basic Rule: Mandatory: Number of [line length] <= 80
    Option Rule:
    max option: 80; Mandatory: Number of [line length] <= {{max}}

**XML Configuration:**
```xml
<module name='LineLength'>
  <property name='id' value='identifier'/>
  <property name='max' value='80'/>
</module>
```

This is the final correct configuration after removing the incorrect mapping and its corresponding XML configuration.
''',
                        '''
                      Configuration:
                      <module name='LineLength'>
                        <property name='id' value='identifier'/>
                        <property name='max' value='80'/>
                      </module>
                      ''']]

example_json_ans_config = [['''Extract the final json configuration in {{tool}} from the following Text. 

Text:
Configuration:
```json
{
    "plugins": ["jsdoc"],
    "rules": {
        "jsdoc/require-jsdoc": ["error", {
            "require": {
                "ClassDeclaration": true,
                "MethodDefinition": true,
                "FieldDefinition": true
            }
        }]
    }
}
```''',
                            '''
                          ```json
                          {
                            "Answer": "No",
                            "Configuration": {
                                  "require-jsdoc": ["error", {
                                      "require": {
                                          "ClassDeclaration": true,
                                          "MethodDefinition": true,
                                          "FieldDefinition": true
                                      }
                                  }]
                              }
                          }
                          ```''']]

options = '''<!DOCTYPE html>
<!--
 | Generated by Apache Maven Doxia Site Renderer 1.11.1 from src/xdocs/property_types.xml at 2024-05-26

 | Rendered using Apache Maven Default Skin
-->
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="generator" content="Apache Maven Doxia Site Renderer 1.11.1" />
    <title>checkstyle &#x2013; Property Types</title>
    <link rel="stylesheet" href="./css/maven-base.css" />
    <link rel="stylesheet" href="./css/maven-theme.css" />
    <link rel="stylesheet" href="./css/site.css" />
    <link rel="stylesheet" href="./css/print.css" media="print" />
<script type="text/javascript" src="./js/checkstyle.js"></script>
        <script type="text/javascript"
              src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
        <script type="text/javascript" src="./js/anchors.js"></script>
        <script type="text/javascript" src="./js/google-analytics.js"></script>
        <link rel="icon" href="./images/favicon.png" type="image/x-icon" />
        <link rel="shortcut icon" href="./images/favicon.ico" type="image/ico" />
  </head>
  <body class="composite">
    <div id="banner">
<a href="./" id="bannerLeft" title="Checkstyle"><img src="images/header-checkstyle-logo.png"  alt="Checkstyle"/></a><a href="./" id="bannerRight" title="Checkstyle"><img src="images/header-right-ruller.png"  alt="Checkstyle"/></a>      <div class="clear">
        <hr/>
      </div>
    </div>
    <div id="breadcrumbs">
      <div class="xright"><a href="" title="toTop">toTop</a>         | <span id="publishDate">Last Published: 2024-05-26</span>
         | <span id="projectVersion">Version: 10.17.0</span>
      </div>
      <div class="clear">
        <hr/>
      </div>
    </div>
    <div id="leftColumn">
      <div id="navcolumn">
       <h5>About</h5>
    <ul>
     <li class="none"><a href="index.html" title="Checkstyle">Checkstyle</a></li>
     <li class="none"><a href="releasenotes.html" title="Release Notes">Release Notes</a></li>
     <li class="none"><a href="consulting.html" title="Consulting">Consulting</a></li>
     <li class="none"><a href="sponsoring.html" title="Sponsoring">Sponsoring</a></li>
    </ul>
       <h5>Documentation</h5>
    <ul>
     <li class="expanded"><a href="config.html" title="Configuration">Configuration</a>
      <ul>
       <li class="none"><strong>Property Types</strong></li>
       <li class="none"><a href="config_system_properties.html" title="System Properties">System Properties</a></li>
      </ul></li>
     <li class="expanded"><a href="running.html" title="Running">Running</a>
      <ul>
       <li class="none"><a href="anttask.html" title="Ant Task">Ant Task</a></li>
       <li class="none"><a href="cmdline.html" title="Command Line">Command Line</a></li>
      </ul></li>
     <li class="expanded"><a href="checks.html" title="Checks">Checks</a>
      <ul>
       <li class="collapsed"><a href="checks/annotation/index.html" title="Annotations">Annotations</a></li>
       <li class="collapsed"><a href="checks/blocks/index.html" title="Block Checks">Block Checks</a></li>
       <li class="collapsed"><a href="checks/design/index.html" title="Class Design">Class Design</a></li>
       <li class="collapsed"><a href="checks/coding/index.html" title="Coding">Coding</a></li>
       <li class="collapsed"><a href="checks/header/index.html" title="Headers">Headers</a></li>
       <li class="collapsed"><a href="checks/imports/index.html" title="Imports">Imports</a></li>
       <li class="collapsed"><a href="checks/javadoc/index.html" title="Javadoc Comments">Javadoc Comments</a></li>
       <li class="collapsed"><a href="checks/metrics/index.html" title="Metrics">Metrics</a></li>
       <li class="collapsed"><a href="checks/misc/index.html" title="Miscellaneous">Miscellaneous</a></li>
       <li class="collapsed"><a href="checks/modifier/index.html" title="Modifiers">Modifiers</a></li>
       <li class="collapsed"><a href="checks/naming/index.html" title="Naming Conventions">Naming Conventions</a></li>
       <li class="collapsed"><a href="checks/regexp/index.html" title="Regexp">Regexp</a></li>
       <li class="collapsed"><a href="checks/sizes/index.html" title="Size Violations">Size Violations</a></li>
       <li class="collapsed"><a href="checks/whitespace/index.html" title="Whitespace">Whitespace</a></li>
      </ul></li>
     <li class="collapsed"><a href="filters/index.html" title="Filters">Filters</a></li>
     <li class="collapsed"><a href="filefilters/index.html" title="File Filters">File Filters</a></li>
     <li class="expanded"><a href="style_configs.html" title="Style Configurations">Style Configurations</a>
      <ul>
       <li class="none"><a href="google_style.html" title="Google's Style">Google's Style</a></li>
       <li class="none"><a href="sun_style.html" title="Sun's Style">Sun's Style</a></li>
      </ul></li>
    </ul>
       <h5>Developers</h5>
    <ul>
     <li class="expanded"><a href="extending.html" title="Extending Checkstyle">Extending Checkstyle</a>
      <ul>
       <li class="none"><a href="writingchecks.html" title="Writing Checks">Writing Checks</a></li>
       <li class="none"><a href="writingjavadocchecks.html" title="Writing Javadoc Checks">Writing Javadoc Checks</a></li>
       <li class="none"><a href="writingfilters.html" title="Writing Filters">Writing Filters</a></li>
       <li class="none"><a href="writingfilefilters.html" title="Writing File Filters">Writing File Filters</a></li>
       <li class="none"><a href="writinglisteners.html" title="Writing Listeners">Writing Listeners</a></li>
      </ul></li>
     <li class="none"><a href="contributing.html" title="Contributing">Contributing</a></li>
     <li class="expanded"><a href="beginning_development.html" title="Beginning Development">Beginning Development</a>
      <ul>
       <li class="none"><a href="eclipse.html" title="Eclipse IDE">Eclipse IDE</a></li>
       <li class="none"><a href="netbeans.html" title="NetBeans IDE">NetBeans IDE</a></li>
       <li class="none"><a href="idea.html" title="IntelliJ IDE">IntelliJ IDE</a></li>
      </ul></li>
     <li class="none"><a href="apidocs/index.html" title="Javadoc">Javadoc</a></li>
    </ul>
       <h5>Project Documentation</h5>
    <ul>
     <li class="collapsed"><a href="project-info.html" title="Project Information">Project Information</a></li>
     <li class="collapsed"><a href="project-reports.html" title="Project Reports">Project Reports</a></li>
    </ul>
      <a href="https://github.com/checkstyle/checkstyle" title="GitHub" class="poweredBy">
        <img class="poweredBy"  alt="GitHub" src="images/github_logo_social_coding_outlined.png"     />
      </a>
      <a href="https://twitter.com/checkstyle_java/" title="Twitter" class="poweredBy">
        <img class="poweredBy"  alt="Twitter" src="images/twitter_button.png"     />
      </a>
      <a href="https://stackoverflow.com/questions/tagged/checkstyle" title="Stackoverflow" class="poweredBy">
        <img class="poweredBy"  alt="Stackoverflow" src="images/stackoverflow.jpeg"     />
      </a>
      <a href="https://groups.google.com/forum/#!forum/checkstyle" title="GoogleGroups" class="poweredBy">
        <img class="poweredBy"  alt="GoogleGroups" src="images/groups.png"     />
      </a>
      <a href="https://www.ej-technologies.com/products/jprofiler/overview.html" title="JProfiler" class="poweredBy">
        <img class="poweredBy"  alt="JProfiler" src="https://www.ej-technologies.com/images/product_banners/jprofiler_medium.png"     />
      </a>
      </div>
    </div>
    <div id="bodyColumn">
      <div id="contentBox">



    <section>
<h2><a name="Content"></a>Content</h2>




<ul>
<li><a href="#Content">Content</a></li>
<li><a href="#Overview">Overview</a></li>
<li><a href="#boolean">boolean</a></li>
<li><a href="#byte">byte</a></li>
<li><a href="#byte.5B.5D">byte[]</a></li>
<li><a href="#char">char</a></li>
<li><a href="#char.5B.5D">char[]</a></li>
<li><a href="#double">double</a></li>
<li><a href="#double.5B.5D">double[]</a></li>
<li><a href="#float">float</a></li>
<li><a href="#float.5B.5D">float[]</a></li>
<li><a href="#int">int</a></li>
<li><a href="#int.5B.5D">int[]</a></li>
<li><a href="#long">long</a></li>
<li><a href="#long.5B.5D">long[]</a></li>
<li><a href="#short">short</a></li>
<li><a href="#short.5B.5D">short[]</a></li>
<li><a href="#AccessModifierOption.5B.5D">AccessModifierOption[]</a></li>
<li><a href="#BlockOption">BlockOption</a></li>
<li><a href="#ClosingParensOption">ClosingParensOption</a></li>
<li><a href="#ElementStyleOption">ElementStyleOption</a></li>
<li><a href="#File">File</a></li>
<li><a href="#ImportOrderOption">ImportOrderOption</a></li>
<li><a href="#JavadocContentLocationOption">JavadocContentLocationOption</a></li>
<li><a href="#LeftCurlyOption">LeftCurlyOption</a></li>
<li><a href="#LineSeparatorOption">LineSeparatorOption</a></li>
<li><a href="#PadOption">PadOption</a></li>
<li><a href="#Pattern">Pattern</a></li>
<li><a href="#Pattern.5B.5D">Pattern[]</a></li>
<li><a href="#RightCurlyOption">RightCurlyOption</a></li>
<li><a href="#Scope">Scope</a></li>
<li><a href="#SeverityLevel">SeverityLevel</a></li>
<li><a href="#String">String</a></li>
<li><a href="#String.5B.5D">String[]</a></li>
<li><a href="#TrailingArrayCommaOption">TrailingArrayCommaOption</a></li>
<li><a href="#URI">URI</a></li>
<li><a href="#WrapOption">WrapOption</a></li></ul>
    </section>

    <section>
<h2><a name="Overview"></a>Overview</h2>

<p>
        Checkstyle is configured using properties, which are string
        representations. This document describes how these string
        representations are mapped to typed properties.
      </p>
    </section>

    <section>
<h2><a name="boolean"></a>boolean</h2>

<p>
        This type represents a boolean.
        The following string representations will map to <code>true</code>:
      </p>


<ul>

<li><code>yes</code></li>

<li><code>true</code></li>

<li><code>on</code></li>
      </ul>


<p>Anything else will map to <code>false</code>.</p>
    </section>

    <section>
<h2><a name="byte"></a>byte</h2>

<p>
        This type represents a byte. The string representation is
        parsed using the <code>java.lang.Byte</code> class.
      </p>
    </section>

    <section>
<h2><a name="byte.5B.5D"></a>byte[]</h2>

<p>
        This type represents a set of bytes. The string representation
        is parsed as a set of comma (',') separated bytes that are parsed
        using the <code>java.lang.Byte</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated byte values.
      </p>
    </section>

    <section>
<h2><a name="char"></a>char</h2>

<p>
        This type represents a char. The string representation is
        parsed using the <code>java.lang.Character</code> class.
      </p>
    </section>

    <section>
<h2><a name="char.5B.5D"></a>char[]</h2>

<p>
        This type represents a set of chars. The string representation
        is parsed as a set of comma (',') separated chars that are parsed
        using the <code>java.lang.Character</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated char values.
      </p>
    </section>

    <section>
<h2><a name="double"></a>double</h2>

<p>
        This type represents a double. The string representation is
        parsed using the <code>java.lang.Double</code> class.
      </p>
    </section>

    <section>
<h2><a name="double.5B.5D"></a>double[]</h2>

<p>
        This type represents a set of doubles. The string representation
        is parsed as a set of comma (',') separated doubles that are parsed
        using the <code>java.lang.Double</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated integers. For example, the
        following:
      </p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;0.42,0.666&quot;/&gt;
      </pre></div>

<p>can instead be expressed as:</p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;0.42&quot;/&gt;
&lt;property name=&quot;tokens&quot; value=&quot;0.666&quot;/&gt;
      </pre></div>
    </section>

    <section>
<h2><a name="float"></a>float</h2>

<p>
        This type represents a float. The string representation is
        parsed using the <code>java.lang.Float</code> class.
      </p>
    </section>

    <section>
<h2><a name="float.5B.5D"></a>float[]</h2>

<p>
        This type represents a set of floats. The string representation
        is parsed as a set of comma (',') separated floats that are parsed
        using the <code>java.lang.Float</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated float values.
      </p>
    </section>

    <section>
<h2><a name="int"></a>int</h2>

<p>
        This type represents an integer. The string representation is
        parsed using the <code>java.lang.Integer</code> class.
      </p>
    </section>

    <section>
<h2><a name="int.5B.5D"></a>int[]</h2>

<p>
        This type represents a set of integers. The string representation
        is parsed as a set of comma (',') separated integers that are parsed
        using the <code>java.lang.Integer</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated integers. For example, the
        following:
      </p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;42,666&quot;/&gt;
      </pre></div>

<p>can instead be expressed as:</p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;42&quot;/&gt;
&lt;property name=&quot;tokens&quot; value=&quot;666&quot;/&gt;
      </pre></div>
    </section>

    <section>
<h2><a name="long"></a>long</h2>

<p>
        This type represents a long. The string representation is
        parsed using the <code>java.lang.Long</code> class.
      </p>
    </section>

    <section>
<h2><a name="long.5B.5D"></a>long[]</h2>

<p>
        This type represents a set of longs. The string representation
        is parsed as a set of comma (',') separated longs that are parsed
        using the <code>java.lang.Long</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated long values.
      </p>
    </section>

    <section>
<h2><a name="short"></a>short</h2>

<p>
        This type represents a short. The string representation is
        parsed using the <code>java.lang.Short</code> class.
      </p>
    </section>

    <section>
<h2><a name="short.5B.5D"></a>short[]</h2>

<p>
        This type represents a set of shorts. The string representation
        is parsed as a set of comma (',') separated shorts that are parsed
        using the <code>java.lang.Short</code> class.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated short values.
      </p>
    </section>

    <section>
<h2><a name="AccessModifierOption.5B.5D"></a>AccessModifierOption[]</h2>

<p>This type represents Java access modifiers.</p>


<ul>

<li><code>public</code></li>

<li><code>protected</code></li>

<li><code>package</code></li>

<li><code>private</code></li>
      </ul>
    </section>

    <section>
<h2><a name="BlockOption"></a>BlockOption</h2>

<p>
        This type represents the policy for checking block statements. The
        following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="block options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>

<tr class="b">

<td align="left"><code>text</code></td>

<td>
              Require that there is some text in the block. For example:

<div class="wrapper">

<div>
<pre>
    catch (Exception ex) {
        // This is a bad coding practice
    }
                </pre></div>
              </div>
            </td>
          </tr>

<tr class="a">

<td align="left"><code>statement</code></td>

<td>
              Require that there is a statement in the block. For example:

<div class="wrapper">

<div>
<pre>
    finally {
        lock.release();
    }
                </pre></div>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="ClosingParensOption"></a>ClosingParensOption</h2>

<p>
        This type represents the policy for the styles for the ending
        parenthesis. The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="closingParens options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>always</code></td>

<td>
              Example:

<div class="wrapper">

<div>
<pre>@Deprecated()</pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>never</code></td>

<td>
              Example:

<div class="wrapper">

<div>
<pre>@Deprecated</pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>ignore</code></td>

<td>
              Anything goes.
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="ElementStyleOption"></a>ElementStyleOption</h2>

<p>
        This type represents the policy for the styles for defining
        elements in an annotation. The following table
        describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="elementStyle options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>expanded</code></td>

<td>
              The expanded version is sometimes referred to as &quot;named parameters&quot;
              in other languages.
              Example:

<div class="wrapper">

<div>
<pre>@SuppressWarnings(value={&quot;unchecked&quot;,&quot;unused&quot;,})</pre></div>
              </div>
              Example of violation:

<div class="wrapper">

<div>
<pre>@SuppressWarnings({&quot;unchecked&quot;,&quot;unused&quot;,})</pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>compact</code></td>

<td>
              This style can only be used when there is an element called 'value'
              which is either the sole element or all other elements have default
              values.
              Example:

<div class="wrapper">

<div>
<pre>
                @SuppressWarnings({&quot;unchecked&quot;,&quot;unused&quot;,})
                @SuppressWarnings(&quot;unchecked&quot;)
                </pre></div>
              </div>
              Example of violation:

<div class="wrapper">

<div>
<pre>
                @SuppressWarnings(value = {&quot;unchecked&quot;,&quot;unused&quot;,})
                @SuppressWarnings(value = &quot;unchecked&quot;)
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>compact_no_array</code></td>

<td>
              It is similar to the <code>compact</code> style but
              single value arrays are flagged. With annotations a single value
              array does not need to be placed in an array initializer.
              Example:

<div class="wrapper">

<div>
<pre>
              @SuppressWarnings(&quot;unchecked&quot;)
              @MyAnnotation(someArray = &quot;some value&quot;)
                </pre></div>
              </div>
              Example of violation:

<div class="wrapper">

<div>
<pre>
              @SuppressWarnings({&quot;unchecked&quot;})
              @MyAnnotation(someArray = {&quot;some value&quot;})
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>ignore</code></td>

<td>
              Anything goes.
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="File"></a>File</h2>

<p>
        This type represents a local file. Unlike the <a href="#URI">uri</a> type,
        which implies read only and not modifiable access to the resource,
        a property of this type indicates files whose contents can be modified by Checkstyle.
      </p>
    </section>

    <section>
<h2><a name="ImportOrderOption"></a>ImportOrderOption</h2>

<p>
        This type represents the policy for checking imports order.
        The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="ImportOrderOptions">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>top</code></td>

<td>All static imports are at the top.
                Groups for static import are defined by the property 'staticGroups'.
                The blank line between groups is driven by the property 'separatedStaticGroups'.
                For example:

<div class="wrapper">

<div>
<pre>
    import static a.b.C.*;
    import static x.y.Z.*;

    import a.b.D;
    import x.y.Z;</pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>above</code></td>

<td>All static imports are above the local group. For example:

<div class="wrapper">

<div>
<pre>
    import static a.b.C.*;
    import a.b.D;

    import static x.y.Z.*;
    import x.y.Z;</pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>inflow</code></td>

<td>All static imports are processed like non static
                imports. For example:

<div class="wrapper">

<div>
<pre>
    import static a.b.C.*;
    import a.b.D;

    import x.y.Z;
    import static x.y.Z.*;</pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>under</code></td>

<td>All static imports are under the local group. For example:

<div class="wrapper">

<div>
<pre>
    import a.b.D;
    import static a.b.C.*;

    import x.y.Z;
    import static x.y.Z.*;</pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>bottom</code></td>

<td>All static imports are at the bottom.
                Groups for static import are defined by the property 'staticGroups'.
                The blank line between groups is driven by the property 'separatedStaticGroups'.
                For example:

<div class="wrapper">

<div>
<pre>
    import a.b.D;
    import x.y.Z;

    import static a.b.C.*;
    import static x.y.Z.*;</pre></div>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="JavadocContentLocationOption"></a>JavadocContentLocationOption</h2>

<p>
        This type represents policy on placement of the Javadoc content.
        The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="JavadocContentLocationOption options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>FIRST_LINE</code></td>

<td>
              Represents the policy for Javadoc content starts from the same line
              as <code>/**</code>.
              Example:

<div class="wrapper">

<div>
<pre>
            /** Summary text.
              * More details.
              */
            public void method();
                </pre></div>
              </div>
              This style is also known as &quot;scala&quot; style.
            </td>
          </tr>


<tr class="a">

<td align="left"><code>SECOND_LINE</code></td>

<td>
              Represents the policy for Javadoc content starts from the next line
              after <code>/**</code>.
              Example:

<div class="wrapper">

<div>
<pre>
              /**
              * Summary text.
              * More details.
              */
              public void method();
                </pre></div>
              </div>
              This style is common to java projects.
            </td>
          </tr>

        </table>
      </div>
    </section>

    <section>
<h2><a name="LeftCurlyOption"></a>LeftCurlyOption</h2>

<p>
        This type represents the policy for checking the placement of a
        left curly brace (<code>'{'</code>). The following table
        describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="left curly options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>eol</code></td>

<td>
              The brace must always be on the end of the line. For example:#

<div class="wrapper">

<div>
<pre>
    if (condition) {
        ...
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>nl</code></td>

<td>
              The brace must always be on a new line. For example:

<div class="wrapper">

<div>
<pre>
    if (condition)
    {
        ...
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>nlow</code></td>

<td>
              If the statement/expression/declaration connected to the brace spans multiple lines,
              then apply <code>nl</code> rule. Otherwise, apply the <code>eol</code> rule.
              <code>nlow</code> is a mnemonic for &quot;new line on wrap&quot;.
              For the example above Checkstyle will enforce:

<div class="wrapper">

<div>
<pre>
    if (condition) {
        ...
                </pre></div>
              </div>
              But for a statement spanning multiple lines, Checkstyle will
              enforce:

<div class="wrapper">

<div>
<pre>
    if (condition1 &amp;&amp; condition2 &amp;&amp;
        condition3 &amp;&amp; condition4)
    {
        ...
                </pre></div>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="LineSeparatorOption"></a>LineSeparatorOption</h2>

<p>
        This type represents the policy for line returns. The
        following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="line separator options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>

<tr class="b">

<td align="left"><code>crlf</code></td>

<td>Windows-style</td>
          </tr>

<tr class="a">

<td align="left"><code>cr</code></td>

<td>Mac-style</td>
          </tr>

<tr class="b">

<td align="left"><code>lf</code></td>

<td>Unix-style</td>
          </tr>

<tr class="a">

<td align="left"><code>lf_cr_crlf</code></td>

<td>lf, cr or crlf</td>
          </tr>

<tr class="b">

<td align="left"><code>system</code></td>

<td>system default</td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="PadOption"></a>PadOption</h2>

<p>
        This type represents the policy for padding with white space. The
        following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="padding options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>

<tr class="b">

<td align="left"><code>nospace</code></td>

<td>
              Do not pad. For example, <code>method(a, b);</code>
            </td>
          </tr>

<tr class="a">

<td align="left"><code>space</code></td>

<td>
              Ensure padding. For example,
              <code>method( a, b );</code>
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="Pattern"></a>Pattern</h2>

<p>
        This type represents a regular expression. The string representation is parsed using
        <a class="externalLink" href="https://docs.oracle.com/javase/8/docs/api/index.html?java/util/regex/package-summary.html">
        java.util.regex package</a>.
      </p>
    </section>

    <section>
<h2><a name="Pattern.5B.5D"></a>Pattern[]</h2>

<p>
        This type represents a set of patterns. The string representation
        is parsed as a set of comma (',') separated patterns.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple
        times which is equivalent to a set of comma separated patterns.
        For example, the following:
      </p>

<div class="source">
<pre>
&lt;property name=&quot;patterns&quot; value=&quot;^prefix*$, ^*suffix$&quot;/&gt;
      </pre></div>

<p>can instead be expressed as:</p>

<div class="source">
<pre>
&lt;property name=&quot;patterns&quot; value=&quot;^prefix*&quot;/&gt;
&lt;property name=&quot;patterns&quot; value=&quot;^*suffix$&quot;/&gt;
      </pre></div>
    </section>

    <section>
<h2><a name="RightCurlyOption"></a>RightCurlyOption</h2>

<p>
        This type represents the policy for checking the placement of a
        right curly brace (<code>'}'</code>) in blocks but not blocks of expressions.
        For right curly brace of expression blocks please follow issue
        <a class="externalLink" href="https://github.com/checkstyle/checkstyle/issues/5945">#5945</a>. The following
        table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="right curly options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>alone</code></td>

<td>
              The brace must be alone on the line. For example:

<div class="wrapper">

<div>
<pre>
    try {
        ...
    <b>}</b>
    finally {
        ...
    <b>}</b>
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>alone_or_singleline</code></td>

<td>
                    The brace must be alone on the line, yet
                    single-line format of block is allowed.
                    For example:

<div class="wrapper">

<div>
<pre>
    // Brace is alone on the line
    try {
        ...
    <b>}</b>
    finally {
        ...
    <b>}</b>

    // Single-line format of block
    public long getId() { return id; <b>}</b>
                </pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>same</code></td>

<td>
              Works like <code>alone_or_singleline</code> but the brace should be on the same line
              as the next part of a multi-block statement
              (one that directly contains multiple blocks: if/else-if/else or try/catch/finally).
              If no next part of a multi-block statement present, brace must be alone on line.
              It also allows single-line format of multi-block statements.


<p>Examples:</p>


<div class="wrapper">

<div>
<pre>
    public long getId() {return id;<b>}</b> // this is OK, it is single-line

    // try-catch-finally blocks
    try {
        ...
    <b>}</b> catch (Exception ex) { // this is OK
        ...
    <b>}</b> finally { // this is OK
        ...
    }

    try {
        ...
    <b>}</b> // this is NOT OK, not on the same line as the next part of a multi-block statement
    catch (Exception ex) {
          ...
    <b>}</b> // this is NOT OK, not on the same line as the next part of a multi-block statement
    finally {
          ...
    }

    // if-else blocks
    if (a &gt; 0) {
       ...
    <b>}</b> else { // this is OK
       ...
    }

    if (a &gt; 0) {
       ...
    <b>}</b> // this is NOT OK, not on the same line as the next part of a multi-block statement
    else {
       ...
    }

    if (a &gt; 0) {
       ...
    <b>}</b> int i = 5; // NOT OK, no next part of a multi-block statement, so should be alone

    Thread t = new Thread(new Runnable() {
       @Override
       public void run() {
                  ...
       <b>}</b> // this is OK, should be alone as next part of a multi-block statement is absent
    <b>}</b>); // this case is out of scope of RightCurly Check (see issue #5945)

    if (a &gt; 0) { ... <b>}</b> // OK, single-line multi-block statement
    if (a &gt; 0) { ... } else { ... <b>}</b> // OK, single-line multi-block statement
    if (a &gt; 0) {
        ...
    } else { ... <b>}</b> // OK, single-line multi-block statement
                </pre></div>
              </div>
            </td>
          </tr>

        </table>
      </div>
    </section>

    <section>
<h2><a name="Scope"></a>Scope</h2>

<p>This type represents a Java scope. Checks use this to determine which
      methods/fields/classes will be examined by its logic. The valid options are:</p>


<ul>

<li><code>nothing</code></li>

<li><code>public</code></li>

<li><code>protected</code></li>

<li><code>package</code></li>

<li><code>private</code></li>

<li><code>anoninner</code></li>
      </ul>


<p>Using a specific scope means not only will that modifier be examined, but also all the
      modifiers listed above it in the previous list. Specifying <code>public</code> means only
      items with <code>public</code> modifiers are checked. Specifying <code>protected</code>
      means only <code>public</code> and <code>protected</code> modifiers are checked.
      If you wish to only validate items with <code>private</code> modifiers and ignore any
      others, then you must set the exclude scope property, if available, to the scope above
      it in the table. In this case you would exclude <code>package</code>.
      </p>
    </section>

    <section>
<h2><a name="SeverityLevel"></a>SeverityLevel</h2>

<p>
        This type represents the severity level of a module violation.
        The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>

<td><a href="cmdline.html">CLI</a></td>

<td><a href="anttask.html">Ant task</a></td>
          </tr>


<tr class="b">

<td align="left"><code>ignore</code></td>

<td>
              If a violation occurs, modules with this severity are ignored as if they never
              occurred.
              This severity can be used to disable a module in the configuration.
            </td>

<td>
              Such violation not printed in output, however,
              depending on the setting of
              <a href="cmdline.html#Command_line_usage"><code>executeIgnoredModules</code></a>
              when executed, the module may still run and if an exception occurs, the exception
              will turn into an error and act as one.
            </td>

<td>
              Such violation not printed in output, however,
              depending on the setting of
              <a href="anttask.html#Parameters"><code>executeIgnoredModules</code></a>
              when executed, the module may still run and if an exception occurs, the exception
              will turn into an error and act as one.
            </td>
          </tr>


<tr class="a">

<td align="left"><code>info</code></td>

<td>
              If a violation occurs, modules with this severity are displayed as informational.
            </td>

<td>
              Displays the violation, but not fail the execution.
            </td>

<td>
              Displays the violation, but not fail the execution.
            </td>
          </tr>


<tr class="b">

<td align="left"><code>warning</code></td>

<td>
              This severity behaves exactly the same as <code>info</code> in Checkstyle.
              It can be used to let user bring more attention to reviewers of such violations.
            </td>

<td>
              Displays the violation, but not fail the execution.
            </td>

<td>
              Displays the violation, might fail the execution.<br />
              <a href="anttask.html#Parameters"><code>maxWarnings</code></a> can be used to pass
              the execution until a certain number of warnings are found.
            </td>
          </tr>


<tr class="a">

<td align="left"><code>error</code></td>

<td>
              If a violation occurs, modules with this severity are displayed as error and should
              be considered as a failure.
            </td>

<td>
              Displays the violation, fail the execution.
            </td>

<td>
              Displays the violation, might fail the execution.<br />
              <a href="anttask.html#Parameters"><code>maxErrors</code></a> can be used to pass
              the execution until a certain number of error are found.
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="String"></a>String</h2>

<p>
        This type represents a string. The literal string representation
        is used.
      </p>
    </section>

    <section>
<h2><a name="String.5B.5D"></a>String[]</h2>

<p>
        This type represents a set of strings. The string representation
        is parsed as a set of comma (',') separated strings. Extra spaces are allowed.
      </p>

<p>
        Alternatively, a property of this type can be supplied multiple times which
        is equivalent to a set of comma separated strings. For example, the
        following:
      </p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;DIV_ASSIGN, PLUS_ASSIGN&quot;/&gt;
      </pre></div>

<p>can instead be expressed as:</p>

<div class="source">
<pre>
&lt;property name=&quot;tokens&quot; value=&quot;DIV_ASSIGN&quot;/&gt;
&lt;property name=&quot;tokens&quot; value=&quot;PLUS_ASSIGN&quot;/&gt;
      </pre></div>
    </section>

    <section>
<h2><a name="TrailingArrayCommaOption"></a>TrailingArrayCommaOption</h2>

<p>
        This type represents the policy for the styles for the trailing
        array comma. The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="trailingArrayComma options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>


<tr class="b">

<td align="left"><code>always</code></td>

<td>
              Example:

<div class="wrapper">

<div>
<pre>@SuppressWarnings(value={&quot;unchecked&quot;,&quot;unused&quot;,})</pre></div>
              </div>
            </td>
          </tr>


<tr class="a">

<td align="left"><code>never</code></td>

<td>
              Example:

<div class="wrapper">

<div>
<pre>@SuppressWarnings(value={&quot;unchecked&quot;,&quot;unused&quot;})</pre></div>
              </div>
            </td>
          </tr>


<tr class="b">

<td align="left"><code>ignore</code></td>

<td>
              Anything goes.
            </td>
          </tr>
        </table>
      </div>
    </section>

    <section>
<h2><a name="URI"></a>URI</h2>

<p>
        This type represents a URI. The string representation is parsed using a custom
        routine to analyze what type of URI the string is.
        It can be a URL, regular file, a file referenced using 'classpath:' protocol, or
        a resource path. It will try loading the path as a URL first, then as a file that
        must exist, and then finally as a resource on the classpath.

        Note that the pseudo URL `classpath:` specifies that the resource
        should be loaded from the class path, if it is not a local file.
      </p>
    </section>

    <section>
<h2><a name="WrapOption"></a>WrapOption</h2>

<p>
        This type represents the policy for wrapping lines.
        The following table describes the valid options:
      </p>


<div class="wrapper">

<table border="0" class="bodyTable" summary="wrap options">

<tr class="a">

<td align="left">Option</td>

<td>Definition</td>
          </tr>

<tr class="b">

<td align="left"><code>nl</code></td>

<td>
              The token must be on a new line. For example:

<div class="wrapper">

<div>
<pre>
    someVariable = aBigVariableNameToMakeThings + &quot;this may work&quot;
                   + lookVeryInteresting;
                </pre></div>
              </div>
            </td>
          </tr>

<tr class="a">

<td align="left"><code>eol</code></td>

<td>
              The token must be at the end of the line. For example:

<div class="wrapper">

<div>
<pre>
    someVariable = aBigVariableNameToMakeThings + &quot;this may work&quot; +
                   lookVeryInteresting;
                </pre></div>
              </div>
            </td>
          </tr>
        </table>
      </div>
    </section>


      </div>
    </div>
    <div class="clear">
      <hr/>
    </div>
    <div id="footer">
      <div class="xright">
        Copyright &#169;      2001&#x2013;2024..      </div>
      <div class="clear">
        <hr/>
      </div>
    </div>
  </body>
</html>
'''