import os
from multiprocessing import Pool
from tqdm import tqdm
from utils.data_utils import get_text
import json

data = []
data = set(data)
with open('Data/protein_name_to_pmcid.json', 'r', encoding='utf-8') as file:
    for line in file:
        try:
            pmcid = json.loads(line)['ids']
            data.update(pmcid)
        except json.JSONDecodeError as e:
            print(f"Parse error: {e.msg} in line {e.lineno}")

filePath = 'Data/Literature/articles_json'
for i in os.listdir(filePath):
    exist_ids = i[8:-5]
    data.discard(exist_ids)

pmcids = list(sorted(data))
print(len(pmcids))

with Pool(16) as p:
    tqdm(p.map(get_text, pmcids), total=len(pmcids))