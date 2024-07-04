import json
import os
from Bio import Entrez
from requests_retry import requests_retry_session

def get_data_arg(name):
    dataset_arg = {}
    if name == 'full_text_sample':
        dataset_arg['root'] = 'Data/Literature'
        dataset_arg['subdirs_1_level'] = ['1', '2', '3']
        dataset_arg['ngram_size'] = 5
        dataset_arg['ngram_size'] = 9000

def get_all_files(dir_root, subdirs):
    # Get json
    file_list = []
    name_list = []
    for subdir in subdirs:
        # build full path for subdir
        dir_path = os.path.join(dir_root, subdir)
        for root, dirs, files in os.walk(dir_path):
            for json_file in files:
                if json_file.endswith(".json"):
                    # print(f"file name: {json_file}")
                    file_list.append(os.path.join(root, json_file))
                    name_list.append(json_file)
    print(len(set(name_list)))
    return file_list

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data['full_text'], data['article_id']

def fetch_pubmed_details(pmid_list):
    if isinstance(pmid_list, list):
        pmid_list = ','.join(pmid_list)
    Entrez.email = 'chen.za@northeastern.edu'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=pmid_list)

    results = Entrez.read(handle)
    return results

import re
import requests
from lxml import etree
def cleanData(text):
    translation_map = str.maketrans('“”‘’', '""\'\'')
    text_no_table_ref = re.sub(r'<xref rid="tbl\d+" ref-type="table">.*?</xref>', '', text)
    text_no_fig_ref = re.sub(r'<xref rid="fig\d+" ref-type="fig">.*?</xref>', '',
                                       text_no_table_ref)

    text_no_citations = re.sub(r'\[\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*\]', '',
                                         text_no_fig_ref)
    text_cleaned = re.sub(r'\s{2,}', ' ', text_no_citations).strip()
    text_cleaned = re.sub(r'\s,\s', ', ', text_cleaned)
    text_cleaned = text_cleaned.translate(translation_map)

    text_cleaned = re.sub(r'\[\s*,\s*', '[', text_cleaned)
    text_cleaned = re.sub(r'\s*,\s*\]', ']', text_cleaned)
    text_cleaned = re.sub(r'\(\s*,\s*', '(', text_cleaned)
    text_cleaned = re.sub(r'\s*,\s*\)', ')', text_cleaned)
    text_cleaned = re.sub(r'\[\]', '', text_cleaned)
    text_cleaned = re.sub(r'\(\)', '', text_cleaned)

    text_cleaned = re.sub(r'\[-\]', '', text_cleaned)
    text_cleaned = re.sub(r'\(-\)', '', text_cleaned)

    text_cleaned = re.sub(r'\(\d+(?:[–-]\d+)?(?:,\s*\d+(?:[–-]\d+)?)*\)', '', text_cleaned)
    text_cleaned = re.sub(r'\d+(?:,\d+)+', '', text_cleaned)

    text_no_comma_sequences = re.sub(r'\[(,\s*)+\]', '', text_cleaned)

    return text_no_comma_sequences

def check_file_exist(pmcid):
    try:
        pmcid_parent_tag = pmcid[3:-6]
    except:
        return False
    # parent_dir = "not exist"
    if pmcid_parent_tag == "":
        parent_dir = "PMC000xxxxxx"
    elif pmcid_parent_tag in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        parent_dir = f"PMC00{pmcid_parent_tag}xxxxxx"
    elif pmcid_parent_tag == "10":
        parent_dir = "PMC010xxxxxx"

    try:
        if os.path.exists(f"/data/paper_text_dataset/pmc/{parent_dir}/{pmcid}.txt"):
            return f"/data/paper_text_dataset/pmc/{parent_dir}/{pmcid}.txt"
        else:
            return False
    except:
        return False

def get_ab_title(xml_root, pmcid):
    orig_texts = xml_root.xpath('//abstract/p')

    at = {}
    at['article_id'] = pmcid
    for i, orig_text in enumerate(orig_texts):
        text = orig_text.xpath('string()')
        if i == 0:
            at['abstract'] = text
        elif i == 1:
            at['title'] = text
    return at

def get_full_text(xml_root, pmcid, text_min_len=100):
    for table in xml_root.xpath('//table-wrap'):
        table.getparent().remove(table)

    paragraphs = xml_root.xpath('//sec/p')
    full_text = ''

    for paragraph in paragraphs:
        paragraph_text = paragraph.xpath('string()')
        full_text += cleanData(paragraph_text) + '\n\n'

    if text_min_len:
        if len(full_text) < text_min_len:
            return False

    article_data = {
        'article_id': pmcid,
        'full_text': full_text
    }
    return article_data

def get_text(pmcid, fnc_tag = "full_text", output_dir = 'Data/Literature/articles_json'):
    '''
    input: pmcid
    output: whether get file
    '''
    result = {}
    if not isinstance(pmcid, str):
        pmcid = "PMC" + str(pmcid)

    file_path = check_file_exist(pmcid)

    if file_path:
        with open(file_path, "r") as f:
            file_context = f.read()
            data = {
                "article_id": pmcid,
                "full_text": file_context.split("==== Refs", 1)[0]
            }
            result.update(data)
    else:

        url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}'
        response = requests_retry_session().get(url)

        try:
            root = etree.fromstring(response.content)
        except etree.XMLSyntaxError as e:
            print(f"{pmcid}: {e}")
            return False
        
        if fnc_tag == "full_text":
            a = get_full_text(root, pmcid)
            if not a:
                return False
            else:
                result.update(a)
        elif fnc_tag == "ab_title":
            result.update(get_ab_title(root, pmcid))

    output_file = os.path.join(output_dir, f'article_{pmcid[3:]}.json')

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)
    print(f'Article {pmcid}: saved to {output_file}.')

    return True
