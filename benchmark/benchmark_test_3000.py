from benchmark_3000 import multichoice
model_name_list = [
    'internlm2-7b-0410-ssl+sft'
]
for model in model_name_list:
    try:
        acc = multichoice(model)
        print(f"3000 bench Try: Acc of {model} is: {acc}")
    except Exception as e:
        continue

