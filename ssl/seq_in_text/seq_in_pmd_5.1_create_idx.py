import os
import pandas as pd
from tqdm import tqdm



def load_gid2pid(index_file_path):
    df = pd.read_csv(index_file_path, delimiter='\t')
    print("Columns in DataFrame:", df.columns)
    try:
        df = df[['GeneID', 'protein_accession.version']].drop_duplicates(subset='GeneID', keep='first')
        data = df.set_index('GeneID').apply(tuple, axis=1).to_dict()
        return data
    except Exception as e:
        print(e)
        duplicates = df[df['GeneID'].duplicated(keep=False)]
        print(duplicates)
        
# You can choose to save gene2refseq directly or save the simplified version
# index_path = '/10TB_3/index_dir/gene2refseq'
# index = load_gid2pid(index_path)

def create_index(root_path, file_name, index_file_path):
    # Create an index for the fasta file and display a progress bar
    file_path = os.path.join(root_path, file_name)
    file_size = os.path.getsize(file_path)  # Get the file size for the progress bar

    with open(file_path, 'r') as file, open(index_file_path, 'a') as index_file:
        tqdm_iter = tqdm(total=file_size, unit='B', unit_scale=True, desc="Creating index")
        position = 0
        line = file.readline()
        while line:
            if line.startswith('>'):
                seq_id = line[1:].split()[0]  # Remove the leading '>'
                index_file.write(f"{seq_id}\t{file_name}\t{position}\n")
            position = file.tell()
            tqdm_iter.update(len(line.encode('utf-8')))  # Update progress bar
            line = file.readline()
        tqdm_iter.close()

    print(f"Extract file '{file_name}' successfully.")

fasta_path = "Data/non_redundant_faa/"
index_path = "Data/faa_idx/all_index.idx"
fasta_list = list(sorted(set(os.listdir(fasta_path))))
for fasta_name in fasta_list[0:2]:
    create_index(fasta_path, fasta_name, index_path)


