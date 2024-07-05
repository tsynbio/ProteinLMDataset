from langchain_openai import ChatOpenAI
import os
import json
import csv
from tqdm import tqdm
from unstructured.cleaners.core import clean
from unstructured.partition.text import partition_text
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
import re

# Berfore this step, please use vLLM to initial the model, this place we choose to use mixtral8x7b as validator.
model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"

os.environ["OPENAI_API_BASE"] = "http://localhost:8000/v1"
os.environ["OPENAI_API_KEY"] = "xxx"
llm = ChatOpenAI(model_name=model_id)

print("Initialing QnA llm chain ...")
class QnA(BaseModel):
    problem: str = Field(description="a multiple choice problem about synthetic biology")
    options: List[str] = Field(description="options for the problem, remember to include option number and a period, e.g. 'option 1: xxx'")
    answer: str = Field(description="the correct answer to the problem, just output the option number is enough e.g. 'option 1'")
    explanation: str = Field(description="explanation for the correct answer, within 100 words")

parser = PydanticOutputParser(pydantic_object=QnA)

template = """
Extract factual knowledge and generate a multiple-choice question based on the provided segment of synthetic biology document, suitable for building a benchmark dataset. The questions should:

1. Be broadly applicable, avoiding trivial or experiment-specific details that do not contribute to a general understanding of the field.
2. Cover a range of topics and difficulty levels, appropriate for users with intermediate to advanced knowledge of protein engineering and synthetic biology.
3. Include 6 plausible answer options, with one correct answer clearly indicated, along with a justification based on the document's content.

Remember to ensure the questions are self-contained and that the correct answer and its rationale are justifiable with a general understanding of the field, rather than knowledge of specific experimental setups or data.

{format_instructions}

Paper Segment: {content}
"""
prompt = PromptTemplate(
    template=template,
    input_variables=["content"],
    partial_variables={"format_instructions": parser.get_format_instructions() + 'Ignore irrelevant texts'}
)

compress_template = """
Summarize the provided segment of synthetic biology document, focusing on the most important information and omitting trivial or experiment-specific details. The summary should be concise, clear, and informative, providing a general understanding of the field without requiring knowledge of specific experimental setups or data. 

Your summary should be approximately 1000 words in length. Please ensure that the summary is self-contained and does not require additional context to be understood.

Paper Segment: {content}
"""

compress_prompt = PromptTemplate(
    template=compress_template,
    input_variables=["content"],
)

from langchain.output_parsers import OutputFixingParser

new_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)

from langchain_core.runnables import RunnablePassthrough
chain = {'content': RunnablePassthrough()} | compress_prompt | llm | {'content': RunnablePassthrough()} | prompt | llm | new_parser
print("Chain initialization successful!")


# Article preprocess
def article_preprocess(pmc_id):
    # print("Preprocess article ...")

    
    with open(f'/root/lanyun-tmp/data/articles_json/article_{pmc_id}.json', 'r') as file:
        data = json.load(file)
    raw = data.get('full_text')

        # cleaning the text

    cleaned = clean(raw, trailing_punctuation=True, dashes=True, bullets=True)
    # elements = partition_text(text=cleaned)

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

    list_from_string = cleaned.split('\n\n')
    chunked_list = large_chunk(list_from_string)
    # print("Preprocess finished!")
    
    raw_length = len(raw)
    if chunked_list == []:
        print("There is no article to generate QnA because the artile length is {raw_length}")
    return chunked_list


    
def fix_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        
        # To safely remove the last comma, try parsing the JSON first
        try:
            data = json.loads(file_content)
            print(f"The file {file_path} is already in valid JSON format, no modification is needed.")
            return data
        except Exception as e:
            corrected_content = re.sub(r'\,(?=\s*?[\}\]])', '', file_content)
            data = json.loads(corrected_content)

            return data
        
    except Exception as e:
        print(f"An error occurred while processing the file {file_path}: {e}")





def main():
    pmc_id_list = []
    # print(os.path.exists('/root/lanyun-tmp/data/pubmed_pmc.csv'))
    with open('/root/lanyun-tmp/data/pubmed_pmc.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # check pmc_row data
            if row[1] != 'False':
                pmc_id_list.append(row[1][3:])
    # print([i[3:] for i in pmc_id_list[:5]])

    pmc_id_list = list(sorted(set(pmc_id_list)))
    flag = 0
    for pmc_id in tqdm(pmc_id_list[35000:35000+1071+888+69]):
        if flag:
            continue

        file_name = f'/root/lanyun-tmp/data/QnA_generation_result/QnA_generation_PMC{pmc_id}.json'
        error_name = f'/root/lanyun-tmp/data/QnA_generation_error/QnA_generation_error_PMC{pmc_id}.txt'



        if not os.path.exists(file_name):
            with open(f'not_exist.json', 'w') as miss_file:
                miss_file.write(f"File PMC{pmc_id} not exist! \n")
            continue
        
        outputs = []
        wasted_chunk = []
        unparsed = []
        chunked_list = article_preprocess(pmc_id)

        if not chunked_list:
            continue

        if os.path.exists(error_name):
            with open(error_name) as ef:
                file_content = ef.read()
                if not file_content:
                    continue
                else:
                    print()
        else:
            flag = 1
            continue

        print(pmc_id)
        for c in tqdm(chunked_list):
            try:
                output = chain.invoke(c)
                outputs.append(output)
                # print(output)

            except Exception as e:
                # print(e)
                wasted_chunk.append(c)
                unparsed.append(e)

        with open(f'/root/lanyun-tmp/data/QnA_generation_result/QnA_generation_PMC{pmc_id}.json', 'w') as f:
            # print(len(outputs))
            f.write("[")
            for o in outputs:
                item = {
                    "question": o.problem,
                    "options": o.options,
                    "answer": o.answer,
                    "explanation": o.explanation
                }
                json_string = json.dumps(item, indent=4, ensure_ascii=False)
                f.write(json_string + ',\n')
            f.write("]")

        if unparsed:
            with open(f'/root/lanyun-tmp/data/QnA_generation_error/QnA_generation_error_PMC{pmc_id}.txt', 'w') as e_file:
                for e in range(len(unparsed)):
                    e_file.write(str(unparsed[e]) + '\n')
                    e_file.write(str(wasted_chunk[e]) + '\n')
                    e_file.write('---\n')
main()
