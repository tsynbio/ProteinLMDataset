import requests
from utils.requests_retry import requests_retry_session
import pandas as pd
import csv
import os

progress_file = 'Data/pmid2pmcid_progress.txt'
if os.path.exists(progress_file):
    with open(progress_file, 'r') as file:
        start_index = int(file.readline().strip())
else:
    start_index = 0

def pmid_to_pmcid(pmid):
    base_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    params = {
        "ids": pmid,
        "format": "json",
        "tool": "pmid2pmcid",
        "email": "your_email@example.com" # Replace this email to yours
    }
    try:
        response = requests_retry_session().get(base_url, params=params)
        data = response.json()
        records = data.get("records", [])
        if records:
            return records[0].get("pmcid", None)
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed: ', e)
        return None


from tqdm import tqdm

df = pd.read_csv('Data/SIFTS/pdb_pubmed.csv', skiprows=1)
pmid_list = list(sorted(set(df['PUBMED_ID'])))
with open('Data/SIFTS/pubmed_pmc.csv', 'a', newline='') as f:
    start_index = 0
    for i in tqdm(pmid_list[start_index:]):
        print(i)
        csv_write = csv.writer(f)
        pmc_id = pmid_to_pmcid(i)
        if pmc_id:
            data_row = [i, pmc_id]
        else:
            data_row = [i, False]
        csv_write.writerow(data_row)
        start_index += 1
        with open(progress_file, 'w') as file:
            file.write(f"{start_index}")
