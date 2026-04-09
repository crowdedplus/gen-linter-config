from litellm import completion

print("=" * 60)
print("实例1-使用千问模型")
print("=" * 60)
response = completion(
    model="dashscope/qwen3-max",
    messages=[
        {"role": "user", "content": "你好，请用中文介绍一下自己"}
    ],
)
print(response.choices[0].message.content)
print('\n')
print("=" * 60)
print("实例2-使用deepseek模型")
print("=" * 60)
response = completion(
    model="deepseek/deepseek-chat",
    messages=[
        {"role": "user", "content": "你好，请用中文介绍一下自己"}
    ],
)
print(response.choices[0].message.content)
print('\n')
