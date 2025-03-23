from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("{subject}") + \
        ', 2+2=?' + \
        '\n{language}'

prompt_value = prompt.invoke({'subject': '程序员', 'language': '中文'})

print(prompt_value.to_string())