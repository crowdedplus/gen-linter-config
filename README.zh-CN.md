[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/crowdedplus/gen-linter-config/blob/main/README.md)
[![zh-cn](https://img.shields.io/badge/lang-zh--cn-blue.svg)](https://github.com/crowdedplus/gen-linter-config/blob/main/README.zh-CN.md)

# gen-linter-config

一个基于大语言模型的linter配置生成工具。

## 使用方法

1. 安装：打开终端：

```python
pip install gen-linter-config
```

2. 配置大模型：本项目使用litellm库进行大模型的统一格式调用，在使用前请确保您有充足的token资源，api_key可以自动从环境变量读取或者通过参数传递。

3. 使用示例：

   ```python
   gen-linter-config -t checkstyle --input "函数参数不多于5个"
   gen-linter-config -t checkstyle --input rule.txt --out output.json
   gen-linter-config -t checkstyle --input "使用大括号包裹代码块" --format json
   gen-linter-config -t checkstyle -m deepseek/deepseek-v4-pro -i "The package declaration is not line-wrapped. The column limit(Section 4.4, Column limit: 100) does not apply to package declarations."
   ```


### 将key配置为系统级环境变量

Windows：通过系统属性设置。找到系统-属性，找到高级系统设置-环境变量，然后在上方的用户环境变量中新建一个变量名为OPENAI_API_KEY，值为密钥的值的用户变量。

Linux/macos：在shell配置文件中设置环境变量。打开终端，根据使用shell的不同执行指令：

```python
# Bash
nano ~/.bashrc
# Zsh
nano ~/.zshrc
# 其它的shell可能需要查阅相关文档确定具体指令。
```

在配置文件中添加：

```py
export OPENAI_API_KEY=[你的 OpenAI API 密钥]
```

然后保存并退出。让更改生效：

```python
# Bash
source ~/.bashrc
# Zsh
source ~/.zshrc
# 其它的shell可能需要查阅相关文档确定具体指令。
```

## 参数介绍

| 参数           | 介绍                               | 是否必须 | 默认值      |
| -------------- | ---------------------------------- | -------- | ----------- |
| -h, --help     | 打印帮助信息并退出                 | 否       | -           |
| --tool, -t     | 指定代码检查工具                   | 是       | -           |
| --input, -i    | 代码规范的文本路径或者文字描述     | 是       | -           |
| --model, -m    | 指定使用模型                       | 否       | qwen3.7-max |
| --out, -o      | 输出文件路径                       | 否       | -           |
| --examples, -e | 文本示例                           | 否       | -           |
| --full         | 完整提示词模式                     | 否       | false       |
| --api-key,-k   | 大模型的key                        | 否       | -           |
| --debug,-d     | 调试模式，输出完整日志在logs文件夹 | 否       | false       |
| --version, -v  | 打印包版本并退出                   | 否       | -           |

当不指定输出文件只会直接输出在控制台中。

## 支持的工具清单

| 工具       | 是否支持 |
| :--------- | -------- |
| Checkstyle | 是       |
| ESLint     | 是       |
| Biome      | 是       |
| ClangTidy  | 是       |
| CppCheck   | 是       |
| Flake8     | 是       |
| PMD        | 是       |
| Pylint     | 是       |
| Reek       | 是       |
| RuboCop    | 是       |
| Ruff       | 是       |

其中Checkstyle和ESLint支持较为完善的生成机制，其余工具则不支持，更多工具的配置生成还在开发中。