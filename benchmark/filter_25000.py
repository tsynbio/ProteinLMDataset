import os, json, re
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from tqdm import tqdm

with open('25000_unvalidated_withNotSure.json', 'r') as f:
    d = json.load(f)


# model_id = "./mixtral8x7b"
# model_name = 'models--CohereForAI--c4ai-command-r-v01'
# fs = f'/data/llm_models/huggingface/hub/{model_name}/snapshots/'
# model_path = fs + os.listdir(f'/data/llm_models/huggingface/hub/{model_name}/snapshots/')[0]
model_path = '/data/llm_models/Meta-Llama-3-8B-Instruct'

os.environ["OPENAI_API_BASE"] = "http://localhost:8000/v1"
os.environ["OPENAI_API_KEY"] = "xxx"
llm = ChatOpenAI(model_name=model_path)

rst = []
validator_template = """
    Answer the multiple-choice question based solely on the provided context. 
    If you are still unsure about the answer, output option 7.
    Select only ONE correct option by its number. Start your response with 'The correct option is' followed by the option number ONLY. eg: "The correct option is Option X."
    Think step by step.

    Context: {context}
    
    Question: {question}
    
    Options: {options}

    Remember, only one option is correct. Please select the single most appropriate option and be sure not to output any other superfluous content. 
    The correct option is: 
"""



validator_prompt = PromptTemplate(
    template=validator_template,
    input_variables=["context", 'question', 'options'],
)
v_chain = RunnablePassthrough() | validator_prompt | llm | RunnableLambda(lambda x: x.content)

for q in tqdm(d):
    dic = {'context': q['matched_text'],
           'question': q['question'],
           'options': q['options']
           }
    rst.append(v_chain.invoke(dic))

from datetime import datetime
now = datetime.now()
formatted_time = now.strftime("%Y%m%d_%H%M%S")

with open(f'./validator_ans/25000_answer_{formatted_time}_byLlama-3-8B.json', 'w') as m:
    json.dump(rst, m)

v_ans = []
non_number = 0
for o in rst:
    try:
        v_ans.append(re.search(r'\d+', o).group())
    except:
        non_number += 1
        v_ans.append("None")

print(non_number)
o_ans = [re.search(r'\d+', o['answer']).group() for o in d]

psd = []
for i in range(len(d)):
    print(i)
    if v_ans[i] != o_ans[i]:
        continue
    psd.append(d[i])

print('correct rate ' + str(len(psd) / len(d)))



with open(f'./validator_ans/25000_passed_{formatted_time}_byLlama-3-8B.json', 'w') as md:
    json.dump(psd, md)
