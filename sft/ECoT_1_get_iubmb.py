import re
import os
import json
from utils.requests_retry import requests_retry_session
from tqdm import tqdm


def get_all_EC():
    output_file_path_single_line = 'EC_number.json'
    files = os.listdir('Data/EC_file')
    files = sorted([f for f in files if f.endswith('.html')])
    ec2ac_name = {}
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        lines = html_content.split('\n')

        for line in lines:
            # Find all EC numbers in the current line
            ec_numbers_in_line = re.findall(r'EC \d+\.\d+\.\d+\.\d+', line)
            # Write all found EC numbers in a single line
            if ec_numbers_in_line:
                ac_name = line.replace(ec_numbers_in_line[0], '', 1)
                ec2ac_name[ec_numbers_in_line[0]] = re.sub(r"<(?!\/?(i|sup|sub)\b)[^>]*>", "", ac_name)

    with open(output_file_path_single_line, 'w', encoding='utf-8') as file_single_line:
        json.dump(ec2ac_name, file_single_line, indent=4, ensure_ascii=False)

def clean_ec_numbers():
    with open('Data/SFT/process/EC_number.txt', 'r') as f:
        ec_set = set()
        original = set()
        lines = f.readlines()
        print(len(lines))
        for line in lines:
            ec_list = line.replace('\n', '').split(",")
            original.add(ec_list[0])
            if len(ec_list) != 1:
                if ec_list:
                    ec_set.discard(ec_list[0])
                    for ec in ec_list[1:]:
                        if ec.startswith(" "):
                            ec = ec.replace(' ', '', 1)
                        ec_set.add(ec)
            else:
                ec_set.add(ec_list[0])
        ec_set.discard('EC 6.3.2.20')
        return sorted(ec_set)

def get_EC_detail(ec_set):
    keywords = ['Reaction', 'Other name(s)', 'Systematic name', 'Comments']
    with open('Data/SFT/process/enzyme_simple_info_1.json', 'w') as enzy_info, open('Data/SFT/process/EC_number.json', 'r') as ac_name:
        ac_name = json.load(ac_name)
        # We haven't got the enzyme name of EC 6.3.2.20
        if 'EC 6.3.2.20' in ec_set:
            ec_set.discard('EC 6.3.2.20')

        enzy_info.write("[")
        first_element = False
        for ec in tqdm(list(ec_set)):
            ec_number = ec.split(' ')[1] # ec -> "EC X.X.X.X"
            one, two, three, four = ec_number.split('.')
            url = f"https://iubmb.qmul.ac.uk/enzyme/EC{one}/{two}/{three}/{four}.html"
            # Initialize a dictionary to store information about an EC entry
            extracted_info = {}

            response = requests_retry_session().get(url)
            responses = response.text.split('<p>')

            extracted_info['_id'] = ec
            extracted_info['Accepted name'] = ac_name[f'EC {one}.{two}.{three}.{four}']

            try:
                for i in responses[1:8]:
                    text = i.replace('\r\r', '', 1).replace('\r\r', ' ')
                    clean_text = re.sub(r"<(?!\/?(i|sup|sub)\b)[^>]*>", "", text)
                    for keyword in keywords:
                        if keyword in clean_text:
                            value = clean_text.replace(keyword, '', 1).replace(":", '', 1)
                            extracted_info[keyword] = value
                            break
                    if 'Glossary' in text:
                        extracted_info['Reaction'] = extracted_info['Reaction'] + ' ' + clean_text.replace('Glossary:', '', 1)
            except Exception as e:
                print(e)
                extracted_info['error'] = 'Retry'

            if not first_element:
                enzy_info.write(',\n')
            else:
                first_element = False
            # print(result)
            json.dump(extracted_info, enzy_info, indent=4, ensure_ascii=False)
        enzy_info.write("]")

# get_all_EC()
ec_set = clean_ec_numbers()
get_EC_detail(ec_set)
