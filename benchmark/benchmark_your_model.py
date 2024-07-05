from benchmark_3000 import multichoice
model_name_list = [
    'your_model1',
    'your_model2'
]
for model in model_name_list:
    try:
        acc = multichoice(model)
        print(f"3000 bench Try: Acc of {model} is: {acc}")
    except Exception as e:
        continue

