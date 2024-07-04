import json
from tqdm import tqdm
from template import sft_template_insert
import re


import os
current_directory = os.getcwd()
print("Current directory:", current_directory)
keywords = ['Function', 'Subunit structure', 'Involvement in disease', 'Post-translational modification', 'Tissue specificity', 'Induction', 'Domain[CC]']
# keywords = []
json_file_1 = '../Uniprot/proteins1.json'
json_file_2 = '../Uniprot/proteins2.json'
with (open(json_file_1, 'r') as protein_data_1,
      open(json_file_2, 'r') as protein_data_2):
    
    data_1 = json.load(protein_data_1)
    data_2 = json.load(protein_data_2)
    print(data_1[:5])

    for protein_1, protein_2 in tqdm(zip(data_1[1:], data_2[1:])):
        protein_1['Protein names'] = protein_2['Protein names']
        for key in protein_1:
            protein_1[key] = re.sub(r'\(PubMed(:\d+)(, PubMed:\d+)*\)', '', protein_1[key])
            protein_1[key] = re.sub(r'\{ECO:([^\}]+)\}\.',
                                    "", protein_1[key])
            protein_1[key] = re.sub(r'\[MIM(:\d+)(, MIM:\d+)*\]', '', protein_1[key])
            protein_1[key] = protein_1[key].replace('. .', '.')

        protein_1['Sequence'] = ' '.join([char for char in protein_1['Sequence']])
        protein_1['Subunit structure'] = protein_1['Subunit structure'].replace('SUBUNIT: ', ' ', 1)
        protein_1['Induction'] = protein_1['Induction'].replace('INDUCTION: ', '', 1)
        protein_1['Tissue specificity'] = protein_1['Tissue specificity'].replace('TISSUE SPECIFICITY:', '', 1)
        protein_1['Domain[CC]'] = protein_1['Domain[CC]'].replace('DOMAIN', '', 1)

for key_word in keywords:
    with open(f'sft_uniprot_{key_word}.json', 'w') as result_file:

        result_file.write('[')
        first_element = True
        for protein_1 in tqdm(data_1[1:]):
            if protein_1[key_word] != '':
                result = sft_template_insert(key_word, protein_1)

                if not first_element:
                    result_file.write(',\n')
                else:
                    first_element = False
                # print(result)
                json.dump(result, result_file, indent=4)
        result_file.write(']')
