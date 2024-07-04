import os, json
from tqdm import tqdm

def extract_entities(entry, prob_bar):
    # Filter out only annotations that contain obj as 'gene' and have a probability higher than 98
    gene_annotations = False
    new_annotations = []
    for annotation in entry['annotations']:
        if annotation['obj'] == 'gene' and annotation['prob'] > prob_bar:
            new_annotations.append(annotation)
    if gene_annotations:
        entry['annotations'] = new_annotations
        return entry
    else:
        return False

root_path = "/home/chenzan/workSpace/bern2-annotation/annotation_result"
anno_list = os.listdir(root_path)

sum_item = 0
prob_bar = 0.98
for file_name in tqdm(anno_list):
    data_path = f'{root_path}/{file_name}'
    output_path = f'{root_path}_threshold_{int(prob_bar*100)}'
    output_file = f'{root_path}_threshold_{int(prob_bar*100)}/filtered_{file_name[:-5]}.json'
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if not os.path.exists(output_file):
        with open(data_path, 'r') as f:
            data_set = f.readlines()
            filtered_data = []
            for data in data_set:
                try:
                    json_data = json.loads(data)
                    title = json_data["title"]
                    filtered_item = extract_entities(json_data, title, prob_bar)
                    if filtered_item:
                        filtered_data.append(filtered_item)
                except Exception as e:
                    with open(f'{root_path}/../error_report', 'a') as errors:
                        errors.write(str(e)+'\n')
            sum_item += len(filtered_data)

            with open(output_file, 'w') as result:
                json.dump(filtered_data, result, ensure_ascii=False)
                print(f'filtered_{file_name} saved.')
                
print(f"We have {sum_item}.")