import weaviate.classes as wvc
import weaviate
import json
import re
from tqdm import tqdm

with open('after_CC.json', 'r') as f:
    after_CC = json.load(f)


weaviate.classes.init.Auth.client_password('tiy', 'try.1206')
client = weaviate.connect_to_local(
    host='localhost',
    port=8080,
    grpc_port=50051,

)
collection = client.collections.get('validation')

rst = []
for qa in tqdm(after_CC):
    ans = re.search(r'\d+', qa['answer'])
    ans_index = int(ans.group()) - 1
    ans_exp = qa['options'][ans_index] + ' ' + qa['explanation']
    response = collection.query.hybrid(
        query=ans_exp,
        filters=wvc.query.Filter.by_property("collection_id").equal('PMC' + qa['pmc_id'])
                & wvc.query.Filter.by_property("chunk_id").equal(qa['chunk_id']),
        fusion_type=wvc.query.HybridFusion.RELATIVE_SCORE,
        alpha=0.8,
        vector=qa['A_embeddings'],
        query_properties=["text"],
        return_metadata=wvc.query.MetadataQuery(score=True, explain_score=True),
        limit=1
    )
    qa['matched_text'] = response.objects[0].properties['text']
    qa['matched_score'] = response.objects[0].metadata.score
    rst.append(qa)

print('matched chunk found all')

with open('with_text_and_score.json', 'w') as f:
    json.dump(rst, f)
print('storing finished')

