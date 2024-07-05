import os, json
import pandas as pd

index_path = 'Data/SIFTS/pdb_chain_enzyme.csv'
index_data = pd.read_csv(index_path, skiprows=1)
index_data = index_data[index_data['EC_NUMBER'] != '?']
index_data['EC_NUMBER'] = index_data['EC_NUMBER'].str.lstrip("'")
index_data = index_data[~index_data['EC_NUMBER'].str.endswith('-')]
index_data = index_data.drop(columns=['PDB','CHAIN']).drop_duplicates()
index_data_result = index_data.groupby('EC_NUMBER').apply(lambda x: x.sample(n=20, replace=False) if len(x) > 20 else x).reset_index(drop=True)

index_data_result.to_csv("Data/SFT/processed_index.csv", index=False)
with open("Data/SFT/process/uniprot_id_enzyme.txt", "w") as f:
    for index, row in index_data_result.iterrows():
        f.write(row["ACCESSION"] + "\n")
# You can use the ACCESSIONs in this table to Uniprot official website to get the sequence of these proteins. Url: https://www.uniprot.org/id-mapping
