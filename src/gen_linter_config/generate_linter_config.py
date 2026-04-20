
import os
import sys
import argparse
import json
import re
import inspect
import json


# 导入项目模块
from gen_linter_config.checkstyle.gen_checkstyle_config import gen_checkstyle
from gen_linter_config.ESLint.gen_eslint_config import gen_eslint
from others import gen_lint_config_rough

def _get_input_content(input_arg):
    """获取输入内容"""
    if os.path.isfile(input_arg):
        # 从文件读取
        with open(input_arg, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        # 直接输入
        return input_arg.strip()

"""
模型名称，例如"dashscope/qwen3-max"或者"deepseek/deepseek-chat"
"""
def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        prog="gen-linter-config",
        description="代码检查工具配置生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
**Examples:**
  gen-linter-config --tool checkstyle --model deepseek/deepseek-chat --input "No more than 5 function parameters."
  gen-linter-config -t checkstyle -i path/to/rule.txt -o path/to/output.json
  gen-linter-config -t eslint -m deepseek/deepseek-chat -i "The parent class construction must be called in the constructor."
**Wrong Usages:**
  gen-linter-config -t eslint -m deepseek/deepseek-chat -- no input
  gen-linter-config  -i "My coding rules" -- no tool name
        """
    )

    parser.add_argument('--tool', '-t', required=True,
                        help='Specify the code checking tool')
    # 需要添加linter name参数，input改为coding standard
    parser.add_argument('--input', '-i', required=True, help='File path or rule text')
    parser.add_argument('--model', '-m',default='dashscope/qwen3-max',help='Specify the model to use')
    parser.add_argument('--out', '-o', help='Output file path')
    # parser.add_argument('--format', '-f', choices=['text', 'json'], default='json', help='output format')
    parser.add_argument('--examples', '-e', help='Sample text')

    args = parser.parse_args()

    input_content = _get_input_content(args.input)
    # format and example may be None
    # if args.format is None:
    #     args.format = 'json'
    if args.examples is None:
        args.examples = ""
    try:
        if args.tool == "checkstyle":
            gen_checkstyle_config = gen_checkstyle()
            result = gen_checkstyle_config.process_input(input_content=input_content,model= args.model,examples= args.examples,)
        elif args.tool == "eslint":
            gen_eslint_config_ = gen_eslint()
            result = gen_eslint_config_.process_input(input_content=input_content,model= args.model,examples= args.examples)
        else:
            result = gen_lint_config_rough.generate_lint_config(rule=input_content,lint_name=args.tool,model=args.model)

        # 输出结果
        if args.out:
            with open(args.out, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"\n" + "=" * 60)
            print(f"结果已保存到: {args.out}")
            print("=" * 60)
        else:
            # 如果没有指定输出文件，才在控制台显示最终合并结果
            print("\n" + "=" * 60)
            print("最终合并结果")
            print("=" * 60)
            print(result)

    except Exception as e:
        print(f"处理错误: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()