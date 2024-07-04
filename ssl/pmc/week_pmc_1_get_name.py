import requests
from tqdm import tqdm
import pandas as pd
import csv
import os
from utils.requests_retry import requests_retry_session

def extract_name(data):
    # Check if there is a recommendedName
    recommended_info = data.get('recommendedName')
    if recommended_info:
        full_name = recommended_info.get('fullName', {})
        name = full_name.get('value', 'Name not found')
        return {'nameType': 'recommendedName', 'name': name}

    # If there is not recommendedName，check submittedName
    submitted_names = data.get('submittedName', [])
    if submitted_names:
        first_submitted_name = submitted_names[0]
        full_name = first_submitted_name.get('fullName', {})
        name = full_name.get('value', 'Name not found')
        return {'nameType': 'submittedName', 'name': name}

    # If neither of them exists, return Not found
    return {'nameType': 'None', 'name': 'Name not found'}

def uniprotkb_to_gene_name(uniprot_id):
    base_url = "https://www.ebi.ac.uk/proteins/api/proteins/"
    headers = {
        "User-Agent": "Python script",
        "From": "youremail@example.com"  # Replace with your email
    }

    # Construct the full URL
    full_url = f"{base_url}{uniprot_id}"

    try:
        response = requests_retry_session().get(full_url, headers=headers)
        data = response.json()
        # Get the first gene info if available
        protein_info = data.get('protein')  
        name = extract_name(protein_info)

        return name
    except requests.exceptions.RequestException as e:
        print('HTTP Request failed: ', e)
        return {'nameType': 'None', 'name': 'No such entry'}

progress_file = 'Data/uniprot2proteinname_progress.txt'
if os.path.exists(progress_file):
    with open(progress_file, 'r') as file:
        start_index = int(file.readline().strip())
else:
    start_index = 0

df = pd.read_csv('Data/SIFTS/pdb_chain_uniprot.csv', skiprows=1)
uniprot_list = list(sorted(set(df['SP_PRIMARY'])))
with open('Data/uniprot_protein1.csv', 'a', newline='') as f:
    csv_write = csv.writer(f)
    for i in tqdm(uniprot_list[start_index:]):
        try:
            protein_name = uniprotkb_to_gene_name(i)
            if protein_name:
                data_row = [i, protein_name['nameType'], protein_name['name']]
            else:
                data_row = [i, 'None', 'No such entry']
            csv_write.writerow(data_row)

        except Exception as e:
            print(f"Error processing {i}: {e}")

        start_index += 1
        with open(progress_file, 'w') as file:
            file.write(f"{start_index}")
