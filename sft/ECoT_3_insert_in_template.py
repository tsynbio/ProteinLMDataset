import os, json
import pandas as pd

def insert_CoT(enzyme_data, seq):
    results = {"instruction":"Analyze the sequence of the following enzyme protein, and step by step deduce which reaction(s) this enzyme is involved in?"}
    results["input"] = "<seq>" + " ".join(seq) + "</seq>"
    function = enzyme_data["Comments"]
    action = enzyme_data["Reaction"]
    if "Accepted name" in enzyme_data:
        name = enzyme_data["Accepted name"]
    elif "Other name(s)" in enzyme_data:
        name = enzyme_data["Other name(s)"].split(";")[0]
    
    if name.startswith(" "):
        name = name[1:]
    fuction_tmpl = f"Based on the analysis of the provided protein sequence, the function of this protein is described as follows: {function} "
    name_tmpl = f"So, this enzyme should belong to the {name}. " 
    action_tmpl = f"Therefore, by synthesizing the analysis of this enzyme, we can determine the reaction(s) it is involved in as follows: \n{action}."
    results["output"] = fuction_tmpl + name_tmpl + action_tmpl
    return results

with open("Data/SFT/process/enzyme_simple_info_1.json", "r") as f:
    data = json.load(f)
    # print(data[1])
    data_dict = {item['_id']: item for item in data}


sequences = {}
current_id = None
current_sequence = []
with open("Data/SFT/process/idmapping.fasta", "r") as faa:
    for line in faa:
        line = line.strip()
        if line.startswith('>'):
            if current_id:
                sequences[current_id] = ''.join(current_sequence)
            # 提取UniProt ID
            parts = line.split('|')
            current_id = parts[1]
            current_sequence = []
        else:
            current_sequence.append(line)

    if current_id:
        sequences[current_id] = ''.join(current_sequence)
print(len(sequences))

index_path = 'Data/SFT/processed_index.csv'
index_data = pd.read_csv(index_path)
# print(index_data.head(5))
result_list = []
for index, row in index_data.iterrows():
    print(row["ACCESSION"], row["EC_NUMBER"])
    uniprot_id = row["ACCESSION"]
    ec_number = f"EC {row['EC_NUMBER']}"
    try: 
        result_list.append(insert_CoT(data_dict[ec_number], sequences[uniprot_id]))
    except:
        continue

with open("Data/SFT/Enzyme_CoT.json", "w") as cot_data:
    json.dump(result_list, cot_data, ensure_ascii=False, indent=4)
    
    # print(len(result_list))
