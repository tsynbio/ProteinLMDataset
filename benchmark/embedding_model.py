import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List
from langchain_core.documents.base import Document

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('Salesforce/SFR-Embedding-Mistral')
model = AutoModel.from_pretrained('Salesforce/SFR-Embedding-Mistral', device_map='auto')
tokenizer.add_eos_token = True

def last_token_pool(last_hidden_states: Tensor,
                    attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def get_embeddings(texts: List[Dict]) -> None:

    if not texts:
        return

    corpora = [text['text'] for text in texts]

    # Tokenize and encode the texts
    batch_dict = tokenizer(corpora, max_length=4096 - 1, padding=True, truncation=True, return_tensors="pt")

    # Run the model and get the last hidden states
    with torch.no_grad():
        outputs = model(**batch_dict)

    # Pool the last token's embeddings
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

    # Normalize the embeddings
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    for i in range(len(texts)):
        texts[i]['embedding'] = embeddings[i]

    # return embeddings


def r_embeddings(texts: List[str]):
    if not texts:
        return

    # Tokenize and encode the texts
    batch_dict = tokenizer(texts, max_length=4096 - 1, padding=True, truncation=True, return_tensors="pt")

    # Run the model and get the last hidden states
    with torch.no_grad():
        outputs = model(**batch_dict)

    # Pool the last token's embeddings
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])

    # Normalize the embeddings
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    return embeddings
