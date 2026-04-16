# encoding=utf-8
"""
requires openai == 1.25.0

"""
# {"steps":[
#     {"explanation":"Start by isolating the term with the variable. Subtract 7 from both sides to do this.","output":"8x + 7 - 7 = -23 - 7"},
#     {"explanation":"Simplify both sides. On the left side, 7 - 7 cancels out, and on the right side, -23 - 7 equals -30.","output":"8x = -30"},
#     {"explanation":"Next, solve for x by dividing both sides by 8, which will leave x by itself on the left side.","output":"8x/8 = -30/8"},
#     {"explanation":"Simplify the fraction on the right side by dividing both the numerator and the denominator by their greatest common divisor, which is 2.","output":"x = -15/4"}],
#     "final_answer":"x = -15/4"}

from openai import OpenAI
from retry import retry
from litellm import completion
from retry import retry
import httpx
import re
wrapper = None
class GPTAgent:
    def __init__(self) -> None:
        # 不再需要任何初始化，使用litellm库直接解析模型接入点
        # 自动读取环境中的key，简化了和模型通信的过程。
        pass

    @retry(delay=0, tries=6, backoff=1, max_delay=120)
    def ask(self, content,examples=None,model="dashscope/qwen3-max",temperature=0,previous_msg=[]):
        """
        :param content:
        :param examples:
        :param model: 完整模型名称，例如"dashscope/qwen3-max"或者"deepseek/deepseek-chat"
        :param temperature:
        :param previous_msg:
        :return:
        """
        messages = []
        # messages.extend(previous_msg)

        # 1.上下文处理
        if isinstance(previous_msg, list):
            for i, each_prompt in enumerate(previous_msg):
                role = "user" if i % 2 else "assistant"
                messages.append({"role": role, "content": each_prompt})

        #  2.处理Few-shot实例
        if examples:
            '''
            https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb
              {"role": "user", "content": "Help me translate the following corporate jargon into plain English."},
            {"role": "assistant", "content": "Sure, I'd be happy to!"},
            '''
            for user_prompt, response in examples:
                messages.extend([
                    {"role": "user",
                     "content": user_prompt},
                    {"role": "assistant",
                     "content": str(response)}])
        # 3.添加当前的用户提问
        messages.append({"role": "user", "content": content})
        # print(">>>>messages: ",messages)

        try:
            response = completion(
                model=model,
                messages=messages,
                temperature=temperature
            )
        except Exception as e:
            print(f"Error calling model {model} : {e}")
            raise e
        return response.choices[0].message.content


    def get_response(self, prompt,examples=None,model="dashscope/qwen3-max",temperature=0,previous_msg=[]):
        answer = self.ask(prompt,examples,model,temperature,previous_msg)
        return answer
        # if len(eslint_rules_simple) > 0:
        #     # question = "Given a rule:\n\n"
        #     # question += rule
        #     # question += "Can you find a corresponding rule in the following rule set?\n\n"
        #     # question += eslint_rules_simple
        #     answer = self.wrapper.ask(prompt)
        #     print(answer)

