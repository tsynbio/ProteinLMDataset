import os
import json
import re
import csv
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import argparse

parser = argparse.ArgumentParser(description='Get Start Index', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--start_index', '-s', help='start_index which file to start', required = True)
parser.add_argument('--sum_items', '-i', help='sum items. How many files should be processed', default = 10)
parser.add_argument('--cuda', '-c', help='Get cuda number', default = 'auto')
args = parser.parse_args()


model_path = "/home/chenzan/workSpace/mmPLM/model/internlm-chat-20b/"
root_path = '/home/chenzan/workSpace/bern2-annotation/'
dataset_path = f'{root_path}annotation_v1.1_filtered_98'
output_path = f'{root_path}results'
anno_list = os.listdir(dataset_path)
anno_list = list(sorted(set(anno_list)))
start_index = int(args.start_index)
sum_items = int(args.sum_items)
device_map = args.cuda

processing_file = f'{output_path}/processing_{start_index}.csv'


tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False, trust_remote_code=True)
print("Start loading Model")

model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True, x=device_map, load_in_4bit=True)
model = model.eval()
prompt_template = """Task: Please classify the following keywords as proteins or genes according to the context.
The keywords are as follow:
{keywords}
The context is as follow:
{text}
Please output the results in json form, where the json key is keywords, and the corresponding value is "protein" or "gene". The output format is as follows:
"keyword1": "gene"(or "protein"), "keyword2": "gene"(or "protein"), ..."""



def format_output(output):
    pattern = r'\{([^}]+)\}'
    match = re.search(pattern, output)
    if match:
        json_include = match.group(1).replace('\n', '')
        return "{"+json_include+"}"
    else:
        return "{}"
keywords = []
from tqdm import tqdm
if os.path.exists(processing_file):
    processed = pd.read_csv(processing_file)
    processed_pmids = processed['processed_pmid'].tolist()
else:
    with open(processing_file, 'w') as init:
        init.write('processed_pmid')
        init.write('\n')
    processed_pmids = []

for file_name in tqdm(anno_list[start_index:start_index+sum_items]):
    data_path = f'{dataset_path}/{file_name}'
    with (
        open(data_path, 'r') as f,
        open(f'{output_path}/{file_name[:-5]}_result.json', 'a') as result,
        open(processing_file, 'a') as processing
    ):

        data_set = f.readlines()
        for data in tqdm(data_set):
            keywords = []
            json_data = json.loads(data)

            if int(json_data['pmid']) not in processed_pmids:
                for i in json_data['annotations']:
                    keywords.append(i['mention'])

                
                input_massage = prompt_template.format(text=json_data["text"], keywords=keywords)
                response, history = model.chat(tokenizer, input_massage, history=[])
                try:
                    response = format_output(response)
                except:
                    response = ""
                format_data = {"pmid": json_data['pmid'], "text": json_data['text'], "response": json.loads(response)}
                json.dump(format_data, result)
                result.write('\n')

            processing_writer = csv.writer(processing)
            processing_writer.writerow([json_data['pmid']])
            result.flush()
            os.fsync(result.fileno())
            processing.flush()
            os.fsync(processing.fileno())

