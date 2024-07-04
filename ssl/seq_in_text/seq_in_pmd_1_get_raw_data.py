import xml.etree.ElementTree as ET
import json
import os


def pmd_xml2json(folder_path, file_name):
    articles = []

    tree = ET.parse(os.path.join(folder_path, file_name))
    root = tree.getroot()
    
    for article in root.findall('.//PubmedArticle'):
        pmid = article.find('.//PMID').text
        
        title = article.find('.//ArticleTitle').text

        abstract = article.find('.//Abstract/AbstractText')
        abstract_text = abstract.text if abstract is not None else ''

        articles.append({'pmid': pmid, 'title': title, 'text': title + '\n' + abstract_text})

    with open(f'{file_name[:-4]}.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False)

folder_path = 'Data/pubmed_xml_data/'
xml_files = [f for f in os.listdir(folder_path) if f.endswith('.xml')]
for xml_file in xml_files:
    pmd_xml2json(folder_path, xml_file)
    