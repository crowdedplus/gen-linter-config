[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/crowdedplus/gen-linter-config/blob/main/README.md)
[![zh-cn](https://img.shields.io/badge/lang-zh--cn-blue.svg)](https://github.com/crowdedplus/gen-linter-config/blob/main/README.zh-CN.md)

# gen-linter-config

A LLM-based linter configuration generate tool .

## How to use

1. install:

```python
pip install gen-linter-config
```

2. Configuring LLM: This project uses `litellm` to call large model in a unified format, so please make sure that you have configured your key as an environment variable and have sufficient token resources before using it.

3. Usage Example：

   ```python
   gen-linter-config -t checkstyle --input "No more than 5 function parameters"
   gen-linter-config -t checkstyle --input rule.txt --out output.json
   gen-linter-config -t checkstyle --input "Wrap the code block in braces" --format json
   gen-linter-config --tool Cppcheck --model dashscope/qwen3-max --input "It is forbidden to use malloc functions that may return null pointers without checking."
   # Cppcheck does not apply to the attribute name system, so it will not actually return the content containing the attribute name.
   ```
   
   If you don't specify an output file, the output will directly printed in the console.

## Configure key as a system-level environment variable

Windows：Through the system property settings. Find system-properties, find advanced system settings-environment variable, and then create a new user variable with the variable named OPENAI_API_KEY and the value of the key in the user environment variable above.

Linux/macos：Set environment variables in the shell configuration file. Open the terminal and execute the instructions according to different shell:

```python
# Bash
nano ~/.bashrc
# Zsh
nano ~/.zshrc
# Other shell may need to consult relevant documents.
```

Add in the configuration file:

```py
export OPENAI_API_KEY=[Your OpenAI API key]
```

Then save and exit. Make the changes take effect:

```python
# Bash
source ~/.bashrc
# Zsh
source ~/.zshrc
# 其它的shell可能需要查阅相关文档确定具体指令。
```

## List of supported tools

| Tool       | Y/N  |
| :--------- | ---- |
| Checkstyle | Y    |
| ESLint     | Y    |
| Biome      | Y    |
| ClangTidy  | Y    |
| CppCheck   | Y    |
| Flake8     | Y    |
| PMD        | Y    |
| Pylint     | Y    |
| Reek       | Y    |
| RuboCop    | Y    |
| Ruff       | Y    |

Among them, Checkstyle and ESLint support a relatively perfect generation mechanism, while other tools do not. The configuration generation of more tools is still under development.
