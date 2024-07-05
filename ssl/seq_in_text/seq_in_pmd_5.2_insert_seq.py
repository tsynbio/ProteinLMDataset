import os, json
from tqdm import tqdm
import pandas as pd
from time import sleep
import psycopg2
import re

'''
Before using this code, you need to create two new tables in the database: 
1. The link between gene_id and protein_accession.version, this can get from file gene2refseq (downloads from NCBI website)
2. The link between protein_accession.version and the local location where the sequence is saved.
'''

conn = psycopg2.connect(
    dbname="yourDatabaseName",
    user="yourUserId",
    password="yourPassword",
    host="localhost"
)
cursor = conn.cursor()
def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

def replace_first_keyword(sentences, keyword, replacement):
    replaced_sentences = []
    for sentence in sentences:
        # Only replace the first occurrence of the keyword 
        replaced_sentence = re.sub(keyword, replacement, sentence, count=1)
        replaced_sentences.append(replaced_sentence)
    return replaced_sentences

def get_specific_file(file_list):
    result = []
    for file in file_list:
        if file.endswith('.json'):
            result.append(file)
    return result

def get_sequence(seq_id):
    """Use index and fasta files to retrieve protein sequences for a specific ID"""

    cursor = conn.cursor()
    cursor.execute("SELECT file_name, file_loc FROM refseq_seq WHERE refseq_id = %s", (seq_id,))

    values = cursor.fetchone()

    fasta_file_path = '/10TB_3/non_redundant_faa/'
    if values:
        with open(f'{fasta_file_path}{values[0]}', 'r') as file:
            # Locate the starting position of the sequence
            file.seek(values[1])  
            header = file.readline().strip()
            sequence = []
            for line in file:
                if line.startswith('>'):
                    break  # Reach next sequence, stop reading
                sequence.append(line.strip())
            return ''.join(sequence)
    else:

        return None

root_path = 'bern2-annotation'
results_path = f'{root_path}/results' # filtered_pubmed22n1060_result.json
filtered_data_path = f'{root_path}/annotation_v1.1_filtered_98'
data_path = f'{root_path}/annotation_v1.1'
result_list = get_specific_file(os.listdir(results_path))
result_list = list(sorted(set(result_list)))
pure_text_path = f'{root_path}/text'

if not os.path.exists(pure_text_path):
    os.makedirs(pure_text_path)

def find_entry_by_pmid(pmid, data):
    for entry in data:
        if entry['_id'] == pmid:
            return entry
    return None

for file_name in tqdm(result_list):

    original_file_name = f'{file_name[9:-12]}.json'
    if not os.path.exists(f'{root_path}/process_file/'):
        os.makedirs(f'{root_path}/process_file/')
    processing_file = f'{root_path}/process_file/processing_{original_file_name[:-5]}.csv'
    if os.path.exists(processing_file):
        processed = pd.read_csv(processing_file)
        processed_pmids = set(processed['processed_pmid'].values)
    else:
        with open(processing_file, 'w') as init:
            init.write('processed_pmid')
            init.write('\n')
        processed_pmids = {}

    with (
        open(f'{data_path}/{original_file_name}', 'r') as f,
        open(f'{results_path}/filtered_{original_file_name[:-5]}_result.json', 'r') as results_data,
        open(f'{filtered_data_path}/filtered_{original_file_name[:-5]}.json', 'r') as filtered_data,
        open(f'{pure_text_path}/puretext_{original_file_name[:-5]}.txt', 'w') as text_file,
        open(processing_file, 'a') as init,
        # open(f'{dataset_file_path}/processing.csv', 'a') as processing,
    ):

        raw_dataset = f.readlines()
        results = results_data.readlines()
        filtered_data_list = filtered_data.readlines()

        if len(filtered_data_list) != len(results):
            # Record the missing items
            print(f"The NER dataset has {len(filtered_data_list)}, but the result has {len(results)}.")
            sleep(10)
            # format as json
        else:
            raw_json_data = [json.loads(f) for f in raw_dataset]
            filtered_json_data = [json.loads(f) for f in filtered_data_list]

            for result, filterd in tqdm(zip(results, filtered_json_data)):
                result_json = json.loads(result)
                filterd_item = filterd['annotations']
                id = result_json['pmid']
                if id not in processed_pmids:
                    raw_data = find_entry_by_pmid(id, raw_json_data)
                    text = raw_data['text']
                    if len(result_json["response"]) == len(filterd_item):
                        for (key, value), item in zip(result_json["response"].items(), filterd_item):

                            if value == 'protein':
                                try:
                                    item_id = int(item['id'][0].split(':')[1])
                                except IndexError:
                                    print(f'Something error in {id}')
                                    continue
                                try:
                                    cursor.execute("SELECT refseqID FROM gid2pid WHERE GeneID = %s;",
                                                   (item_id,))
                                    pid_info = cursor.fetchone()[0]
                                except:
                                    print(f'There are no Protein for GeneID:{item_id}')
                                    continue
                                try:
                                    # print(pid_info)
                                    seq = get_sequence(pid_info)
                                    split_seq = ' '.join([char for char in seq])
                                    replace_data = f" <seq> {split_seq} </seq> "
                                    # replace the first key words
                                    sentences = split_into_sentences(text)
                                    replaced_sentences = replace_first_keyword(sentences, key, key+replace_data)
                                    # trans to str
                                    replaced_text = ' '.join(replaced_sentences)
                                except Exception as e:
                                    print(f'There are no Protein {pid_info}, which named {key}')
                        if text != replaced_text:
                            json_text = {'id': id, 'text': replaced_text}
                            json_string = json.dumps(json_text)  # Convert dictionary to JSON string
                            text_file.write(json_string)
                            text_file.write('\n')
                            init.write(id)
                            init.write('\n')

