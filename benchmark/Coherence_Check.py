import json
import embedding_model as em
from time import time
import re
from tqdm import tqdm

with open('valid_pairs.json', 'r') as f:
    QnA = json.load(f)

def embed_questions():
    questions = [i['question'] for i in QnA]

    batch_size = 40  # Define the size of each batch
    # Loop over the documents in batches of 'batch_size'
    questions_embeddings = []

    for i in tqdm(range(0, len(questions), batch_size)):
        # Select a batch of documents
        time_emb_start = time()
        batch_docs = questions[i:i + batch_size]
        # Get embeddings for the current batch of document contents
        questions_embeddings.extend(em.r_embeddings(batch_docs).tolist())
        time_emb_end = time()
        print(f"We spend {time_emb_end-time_emb_start}s in embedding this batch.")

    with open('question_embeddings.json', 'w') as qe:
        json.dump(questions_embeddings, qe)
        print('Q embeddings store finished')

    for j in range(len(QnA)):
        QnA[j]['Q_embeddings'] = questions_embeddings[j]

def load_q_embeddings():
    with open('question_embeddings.json', 'r') as f:
        q_embeddings = json.load(f)

    if len(q_embeddings) != len(QnA):
        raise IndexError('what the f')

    for j in range(len(QnA)):
        QnA[j]['Q_embeddings'] = q_embeddings[j]

def embed_answers():
    wasted = []

    ans_indices = []
    for o in QnA:
        # Check if 'answer' contains "option"
        if "ption" in o['answer']:
            ans = re.search(r'\d+', o['answer'])
            # If there's a number in 'answer', append its index (number - 1)
            if ans:
                ans_indices.append(int(ans.group()) - 1)
            else:
                ans_indices.append(-1)
        else:
            ans_indices.append(-1)

    print('QnA length', len(QnA))
    print('ans length', len(ans_indices))
    aande = []
    for i in range(len(QnA)):
        if ans_indices[i] == -1:
            temp = 'None'
            wasted.append(QnA[i])
        else:
            try:
                temp = (QnA[i]['options'][ans_indices[i]] +" "
                        + QnA[i]['explanation'])
            except IndexError:
                print('Index error: QnA: ', QnA[i])
                temp = 'None'
                wasted.append(QnA[i])
        aande.append(temp)

    batch_size = 20  # Define the size of each batch
    # Loop over the documents in batches of 'batch_size'
    ans_and_expl_embeddings = []

    for i in tqdm(range(0, len(QnA), batch_size)):
        # Select a batch of documents
        time_emb_start = time()
        batch_docs = aande[i:i + batch_size]
        # Get embeddings for the current batch of document contents
        ans_and_expl_embeddings.extend(em.r_embeddings(batch_docs).tolist())
        time_emb_end = time()
        print(f"We spend {time_emb_end-time_emb_start}s in embedding this batch.")

    with open('improved_a_embedding.json', 'w') as ae:
        json.dump(ans_and_expl_embeddings, ae)
        print('A embeddings store finished')

    for j in range(len(QnA)):
        if aande[j] == 'None':
            continue
        QnA[j]['A_embeddings'] = ans_and_expl_embeddings[j]

    return wasted



if __name__ == '__main__':
    # embed_questions()

    load_q_embeddings()

    w = embed_answers()
    with open('CC_v2.json', 'w') as file:
        json.dump(QnA, file)
        print('store results finished')

    with open('wasted_qna_2.json', 'w') as file:
        json.dump(w, file)
        print('store wasted qna finished')
