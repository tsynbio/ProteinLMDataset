import copy

instruction_template = {
    "Function": {
        "instruction": "The sequence of the protein is as follows. Please analyze the sequence and describe the functions of this protein.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "The determined function(s) of the protein include(s): {output}"
    },
    "Subunit structure": {
        "instruction": "Examine this protein sequence and provide a comprehensive description of its subunit structure, including details on how the subunits are organized and interact with each other.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "Based on the analysis, the protein's subunit structure is characterized by: {output}"
    },
    "Involvement in disease": {
        "instruction": "Analyze this protein sequence for any known associations with diseases, including details on the nature of the involvement and relevant diseases.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "This protein is associated with the following disease(s): {output}"
    },
    "Post-translational modification": {
        "instruction": "Identify and describe any post-translational modifications in the given protein sequence, including types of modifications and their locations.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "The post-translational modification(s) identified in this protein include(s): {output}"
    },
    "Tissue specificity": {
        "instruction": "Examine the provided protein sequence and detail its tissue specificity, including which tissues or organ systems the protein is predominantly expressed in.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "The tissue specificity of this protein is characterized by: {output}"
    },
    "Induction": {
        "instruction": "Investigate and describe any known inducers or conditions that lead to the expression of this protein.",
        "input": "Presented here is a sequence of amino acids in a protein: <seq> {sequence} </seq>",
        "output": "The known inducer(s) or condition(s) leading to the expression of this protein include(s): {output}"
    }
}
def sft_template_insert(template_name, context):
    if template_name in instruction_template:
        this_template = copy.deepcopy(instruction_template[template_name])
        this_template["input"] = this_template["input"].format(sequence=context["Sequence"])
        this_template["output"] = this_template["output"].format(output=context[template_name])
        return this_template
    else:
        return None


