import os, json
from transformers import AutoTokenizer, AutoModelForCausalLM
def multichoice(model_name):
    QnA_dir_path = '/data/benchmark/final_benchmark_dataset.json'
    with open(QnA_dir_path, 'r') as f:
        file_data = json.load(f)

    model_path = f'/data/llm_models/{model_name}'
    if 'models--' in model_name:
        fs = f'/data/llm_models/huggingface/hub/{model_name}/snapshots/'
        model_path = fs + os.listdir(f'/data/llm_models/huggingface/hub/{model_name}/snapshots/')[0]
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, device_map = "auto").eval()

    import re
    answer_list = [f['answer'] for f in file_data]
    answer_list = [re.search(r'\d+', a).group() for a in answer_list]

    prompt = ("""
Answer the multiple-choice question based solely on the provided context. 
If you are still unsure about the answer, output option 7.
Select only ONE correct option by its number. Start your response with 'The correct option is' followed by the option number ONLY. eg: "The correct option is Option X."
Think step by step.
    """)
    question = []


    for f in file_data:
        options = ''
        for o in f['options']:
            options += o + '\n'
        sb = prompt + '\n Question: \n' + f['question'] + '\n Options: \n' + options + '\nThe correct option is:'
        question.append(sb)

    inputs = []
    tokenizer.pad_token = tokenizer.eos_token
    for q in question:
    # for q in question:
    #     a = tokenizer.apply_chat_template([{"role": "user", "content": q}], return_tensors="pt").to("cuda")
        a = tokenizer(q, return_tensors="pt", padding=True)
        input_ids = a.input_ids.to('cuda')
        inputs.append(input_ids)

    print(len(inputs))

    chat_model = ('chat' in model_name) or ('Chat' in model_name)
    if 'Yi' in model_name:
        chat_model = False
    from tqdm import tqdm
    output_list = []

    temp = 0.1
    mnt = 20
    for q in tqdm(inputs[:]):
        if chat_model:
            try:
                if 'Mistral' in model_name:
                    output_list.append(model.chat(tokenizer, q, do_sample=True, max_new_tokens=mnt, temperature=temp, history=[], eos_token_id=2, pad_token_id=2))
                else:
                    output_list.append(model.chat(tokenizer, q, max_new_tokens=mnt, do_sample=True, temperature=temp, history=[]))
            except:
                output_list.append(model.generate(q, max_new_tokens=mnt, do_sample=True, temperature=temp))
        else:
            if 'Mistral' in model_name:
                output_list.append(model.generate(q, max_new_tokens=mnt,do_sample=True, temperature=temp, eos_token_id=2, pad_token_id=2))
            else:
                output_list.append(model.generate(q, max_new_tokens=mnt, do_sample=True,temperature=temp))

    lst = [tokenizer.decode(i[0], skip_special_tokens=True) for i in output_list]


    after = []
    for i, j in zip(lst, question):
    # for i, j in zip(output_list, question):
        after.append(i.replace(j, ''))

    # print(after)
    v_ans = []
    non_number = 0
    for o in after:
        try:
            # v_ans.append(re.search(r'The correct option number is: (\d+)', o).group(1))
            v_ans.append(re.search(r'\d+', o).group())
        except:
            non_number += 1
            v_ans.append("None")

    print(non_number)
    psd = 0
    # wrong_list = []
    from datetime import datetime
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d_%H%M%S")
    if "/" in model_name:
        model_name = model_name.split("/")[2]

    with open(f'result/raw_result_{formatted_time}_{model_name}.json', 'w') as jj:
        json.dump(after, jj)

    with open(f'result/rst_compar_{formatted_time}_{model_name}.txt', 'w') as results:
        for i in range(len(v_ans)):
            # print(i)
            if v_ans[i] != answer_list[i]:
                results.write(str(v_ans[i]) + "   "+ str(answer_list[i]))
                results.write("\n")
                continue
            else:
                results.write("Right")
                psd+=1
                results.write("\n")

    accuracy = psd/len(v_ans)
    print('correct rate: ' + str(psd / len(v_ans)))

    del tokenizer
    del model
    return accuracy

model_name_list = [
    'your_model1',
    'your_model2'
]
for model in model_name_list:
    try:
        acc = multichoice(model)
        print(f"Acc of {model} is: {acc}")
    except Exception as e:
        continue

