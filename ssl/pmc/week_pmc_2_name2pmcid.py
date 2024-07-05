import json
from utils.requests_retry import requests_retry_session
import os
from lxml import etree
import csv
from tqdm import tqdm

base_path = "Data/Literature"
files_number = 50

progress_file = os.path.join(base_path, 'uniprot2pmcid_progress.txt')
if os.path.exists(progress_file):
    with open(progress_file, 'r') as file:
        start_index = int(file.readline().strip())
else:
    start_index = 0

with open('Data/uniprot_protein1.csv') as f:
    reader = list(csv.reader(f))
    # total_lenth = len(reader) - start_index
    for i, keyword in enumerate(tqdm(reader[start_index:], desc="Processing")):

        if keyword[1] != "None":
            query = f"{keyword[2]}"
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={query}&retmax={files_number}"
            search_response = requests_retry_session().get(search_url)
            search_root = etree.fromstring(search_response.content)
            ids = search_root.xpath('//IdList/Id/text()')
            # print(type(ids))
            data = {
                "Uniprot_id": keyword[0],
                "nameType": keyword[1],
                "ids": ids}

            with open('Data/protein_name_to_pmcid.json', 'a', encoding='utf-8') as file:
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

            with open(progress_file, 'w') as file:
                file.write(f"{i+1+start_index}")
