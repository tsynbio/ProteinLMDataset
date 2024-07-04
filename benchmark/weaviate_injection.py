from time import time
import csv
import json
from unstructured.cleaners.core import clean
from unstructured.partition.text import partition_text
import weaviate
import os
from typing import List
from weaviate.util import generate_uuid5  # Generate a deterministic ID
import embedding_model as em
from tqdm import tqdm
from weaviate.exceptions import WeaviateQueryError, WeaviateGRPCUnavailableError, WeaviateInsertManyAllFailedError, WeaviateBatchError
import weaviate.classes as wvc
from unstructured.documents.elements import Element

def large_chunk(lst):
    # Initialize variables
    result = []
    current_chunk = []
    current_word_count = 0

    for item in lst:
        # Count words in the current item
        item_word_count = len(item)

        # If adding this item exceeds the word limit, finish the current chunk and start a new one
        if current_word_count + item_word_count > 5000:
            result.append(' '.join(current_chunk))  # Join the current chunk into a string and add to the result
            current_chunk = []  # Start a new chunk
            current_word_count = 0  # Reset word count for the new chunk

        # Add the current item to the chunk and update the word count
        current_chunk.append(item)
        current_word_count += item_word_count

    # Add the last chunk if it's not empty
    if current_chunk:
        result.append(' '.join(current_chunk))

    return result


def insert_data_to_weaviate(collection_id: str, objs):

    inserting = True

    time_start = time()

    if not objs:
        return

    data_objects = []
    for i in range(len(objs)):
        data_object = {
            "collection_id": collection_id,
            "chunk_id": objs[i]['chunk_id'],
            "text": objs[i]['text'],
        }
        try_id = generate_uuid5(data_object)

        w_obj = wvc.data.DataObject(
            properties=data_object,
            uuid=try_id,
            vector=objs[i]['embedding'].tolist()
        )
        data_objects.append(w_obj)

    while inserting:
        try:
            collection.data.insert_many(data_objects)
            inserting = False
        except WeaviateBatchError:
            print(f'insert retry file {collection_id}')

    time_end = time()
    print(f"We spend {time_end-time_start}s in inserting this small chunk.")


def injection(file_pmc_id: str) -> None:

    # Assuming you have a JSON file named 'data.json'
    file_name = 'article_' + file_pmc_id[3:] + '.json'
    file_path = '/home/luhan/articles_json/' + file_name

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except:
        return

    raw = data.get('full_text')

    # cleaning the text
    cleaned = clean(raw, trailing_punctuation=True, dashes=True, bullets=True)
    list_from_string = cleaned.split('\n\n')
    chunked_list = large_chunk(list_from_string)

    total = []
    for i in range(len(chunked_list)):
        if len(chunked_list[i]) <= 300:
            obj = {'text': chunked_list[i], 'chunk_id': i}
            total.append(obj)
        else:
            elements = partition_text(text=chunked_list[i], min_partition=300, max_partition=1100)
            for ele in elements:
                obj = {'text': ele.text, 'chunk_id': i}
                total.append(obj)


    batch_size = 40  # Define the size of each batch
    # Loop over the documents in batches of 'batch_size'
    time_emb_start = time()
    for i in range(0, len(total), batch_size):
        # Select a batch of documents

        batch_docs = total[i:i + batch_size]
        # Get embeddings for the current batch of document contents
        em.get_embeddings(batch_docs)
    time_emb_end = time()
    print(f"We spend {time_emb_end-time_emb_start}s in embedding this batch.")


    insert_data_to_weaviate(file_pmc_id, total)
    print('file ' + file_pmc_id + ' injection completed')


if __name__ == '__main__':

    running = True

    pmc_id_list = []

    with open('./pubmed_pmc.csv') as pmc:
        reader = csv.reader(pmc)
        for row in reader:
            # check pmc_row data
            if row[1] != 'False':
                pmc_id_list.append(row[1])
    # print([i[3:] for i in pmc_id_list[:5]])

    pmc_id_list = list(sorted(set(pmc_id_list)))

    # Load the PMC IDs from the document into a set for fast lookup
    doc_path = "./finished.txt"  # Path to your document
    existing_pmc_ids = set()

    with open(doc_path, 'r') as file:
        for line in file:
            existing_pmc_ids.update(line.strip().split(', '))

    while running:
        try:
            weaviate.classes.init.Auth.client_password('tiy', 'try.1206')
            client = weaviate.connect_to_local(
                host='localhost',
                port=8080,
                grpc_port=50051,

            )
            collection = client.collections.get('validation')

        # Iterate through your list of PMC IDs
            for pmcid in tqdm(pmc_id_list):
                # Check if the PMC ID is already in the document
                if pmcid in existing_pmc_ids:
                    # If it is, skip this iteration
                    continue

                # If the PMC ID is not in the document, perform your desired operation
                injection(pmcid)

                # Then append the PMC ID to the document and the set to avoid re-reading the document
                with open(doc_path, 'a') as file:
                    file.write(f', {pmcid}')
                existing_pmc_ids.add(pmcid)
            running = False
            client.close()

        except WeaviateGRPCUnavailableError as e:
            print('haha, again')





