import json
import re
from tqdm import tqdm


def fill_tamplate(protein):
    uniprot_id = protein['Entry']
    full_name = protein['Protein names']
    length = protein['Length']
    organism = protein['Organism']
    sequence = protein['Sequence']
    function = protein['Function']
    subunit = protein['Subunit structure'].replace('SUBUNIT: ', '', 1)
    tissue = protein['Tissue specificity'].replace('TISSUE SPECIFICITY: ', '', 1)
    induction = protein['Induction'].replace('INDUCTION: ', '', 1)
    domain = protein['Domain[CC]']
    ptm = protein['Post-translational modification']
    disease_association = protein['Involvement in disease']

    tamplate_intro = \
f"""Introduction:
The protein with UniProt accession number {uniprot_id}, known as {full_name}, is a protein of {length} amino acids found in {organism}."""

    tamplate_sequence = f"""
The sequence of {full_name} with UniProt accession is as follow:
<seq> {sequence} </seq>"""

    if function:
        tamplate_function = f"""
Function:
The functions of {full_name} are as follows: {function}"""

    else:
        tamplate_function = ''

    if subunit:
        tamplate_subunit = f"""
Subunit Structure:
Regarding the subunit composition of {full_name}, the details are as follows: {subunit}"""
    else:
        tamplate_subunit = ''

    if tissue:
        tamplate_tissue = f"""
Tissue Specificity:
In terms of tissue specificity, {full_name} exhibits the following characteristics: {tissue}"""
    else:
        tamplate_tissue = ''

    if induction:
        tamplate_induction = f"""
Induction:
Concerning the induction of {full_name}, it is observed that: {induction}"""
    else:
        tamplate_induction = ''

    if domain:
        tamplate_domain = f"""
Domain:
Regarding the domain structure of {full_name}, it is detailed as follows: {domain}"""
    else:
        tamplate_domain = ''

    if ptm:
        tamplate_ptm = f"""
Post-translational Modifications (PTM):
The post-translational modifications (PTMs) of {full_name} are as follows: {ptm}"""
    else:
        tamplate_ptm = ''

    if disease_association:
        tamplate_disease = f"""
Disease Association:
In relation to disease association, {full_name} is linked with the following conditions: {disease_association}"""
    else:
        tamplate_disease = ''

    tamplate_all = \
f"""{tamplate_intro}
    {tamplate_sequence}
    {tamplate_function}
    {tamplate_subunit}
    {tamplate_tissue}
    {tamplate_induction}
    {tamplate_domain}
    {tamplate_ptm}
    {tamplate_disease}"""

    return tamplate_all

json_file_1 = 'proteins1.json'
json_file_2 = 'proteins2.json'
with (open(json_file_1) as protein_data_1,
      open(json_file_2) as protein_data_2):
    data_1 = json.load(protein_data_1)
    data_2 = json.load(protein_data_2)
    for protein_1, protein_2 in tqdm(zip(data_1[1:], data_2[1:])):
        protein_1['Protein names'] = protein_2['Protein names']
        for key in protein_1:
            protein_1[key] = re.sub(r'\(PubMed(:\d+)(, PubMed:\d+)*\)', '', protein_1[key])
            protein_1[key] = re.sub(r'\{ECO:([^\}]+)\}\.',
                                  "", protein_1[key])
            protein_1[key] = protein_1[key].replace('. .', '.')

        protein_1['Sequence'] = ' '.join([char for char in protein_1['Sequence']])
        protein_1['Subunit structure'] = protein_1['Subunit structure'].replace('SUBUNIT: ', ' ', 1)
        protein_1['Tissue specificity'] = protein_1['Tissue specificity'].replace('TISSUE SPECIFICITY:', '', 1)
        protein_1['Domain[CC]'] = protein_1['Domain[CC]'].replace('DOMAIN', '', 1)

        result = fill_tamplate(protein_1)

        outputfile_path = f'{protein_1["Entry"]}.txt'
        with open(outputfile_path, 'w') as outputfile:
            outputfile.write(result)
        # break


