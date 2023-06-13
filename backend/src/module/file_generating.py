import csv
import json
import os
import pandas as pd
import nltk

from model import Model
from nltk.corpus import wordnet
from transformers import T5ForConditionalGeneration, T5TokenizerFast
from transformers import pipeline
from text_vectorizing import TextVectorizing
from text_processing import TextProcessing
from files_path import (
    FILE_GENERAL,
    FILE_PAIRING,
    FILE_SUGESSION_WEIGHTAGE,
    FILE_IQL,
    FILE_GLOBAL_CONFIG,
    FILE_CONTEXTS,
    FILE_PENDING_DATA,
    DIR_GROUPINGS,
)

COMMON_MODEL = None


def get_synonyms(word):
    nltk.download("wordnet")
    synonyms = set()
    for synset in wordnet.synsets(word):  # type: ignore
        for lemma in synset.lemmas():  # type: ignore
            synonyms.add(lemma.name())
    return list(synonyms)


def GenerateIQLFile():

    """
    IQL stands for Id, Question, Label
    This data structure is convenient for model trainings
    """

    iql_data = pd.DataFrame(columns=["id", "question", "label"])

    # Read the new data from general CSV file using Pandas
    general_data = pd.read_csv(FILE_GENERAL, usecols=[0, 1, 3], header=0)
    general_data.columns = ["id", "question", "label"]

    # Combine the two DataFrames using the concat() method
    combined_data = pd.concat([iql_data, general_data], ignore_index=True)

    # Write the combined data to the 'IQL.csv' file
    combined_data.to_csv(FILE_IQL, index=False, header=["id", "question", "label"])

    # Read the JSON file into a pandas DataFrame
    global_config = pd.read_json(FILE_GLOBAL_CONFIG)

    # Get the last ID
    last_id = general_data.iloc[-1]["id"]

    # Modify the value of "last_id"
    global_config["data"]["last_id"] = last_id

    # Write the updated data back to the JSON file
    global_config.to_json(FILE_GLOBAL_CONFIG)


def GenerateGroupingFiles():
    # Read data from the pending-data CSV file
    data = pd.read_csv(FILE_GENERAL)

    # Create the folder for the CSV files (if it doesn't already exist)
    os.makedirs(DIR_GROUPINGS, exist_ok=True)

    # Write the question and response to the correct CSV file based on their label
    for label, group in data.groupby("label"):
        # Select only the 'question' and 'response' columns from the group DataFrame
        group[["question", "response"]].to_csv(
            f"{DIR_GROUPINGS}/{label}.csv", index=False
        )


def UpdateFiles(vocab):

    # Read the JSON file into a pandas DataFrame
    global_config = pd.read_json(FILE_GLOBAL_CONFIG)
    pending_data = pd.read_csv(FILE_PENDING_DATA)
    iql_data = pd.read_csv(FILE_IQL)
    general_data = pd.read_csv(FILE_GENERAL)
    suggestion_data = pd.read_csv(FILE_SUGESSION_WEIGHTAGE)
    folder_name = DIR_GROUPINGS

    # Write the updated data back to the JSON file
    global_config.to_json(FILE_GLOBAL_CONFIG)

    # Get the last ID from the global_config file
    LASTID = global_config["data"]["last_id"]

    new_pending_data = {"question": [], "response": [], "label": []}

    # Append new data to the general CSV file, skipping duplicates
    for _, r in pd.DataFrame(pending_data).iterrows():
        question = r["question"]
        response = r["response"]
        label = r["label"]

        vectorizer = TextVectorizing(vocab=vocab)
        vec_questions = [
            vectorizer.vectorize(TextProcessing(sentence=i).get_processed_text_list())
            for i in general_data["question"]
        ]

        # Convert Sentence to processed sentence in a list
        # then vectorize word by word based on the vocab
        vec_q = vectorizer.vectorize(
            TextProcessing(sentence=question).get_processed_text_list()
        )

        # Check IF vectorized sentence in the exisitng vectorised questions
        if vec_q in vec_questions:

            # IF vectorized sentence exists BUT the given response is not in the general data
            # PUSH IT to the suggestion weightage for later FINE-TUNING
            if response not in general_data["response"].values:
                index = vec_questions.index(vec_q)
                ids = list(general_data["id"])
                id = ids[index]
                weight = 1
                isFound = False
                update_index = None
                for idx, (_, r) in enumerate(suggestion_data.iterrows()):
                    if response == r["response"]:
                        weight = int(r["weight"] + 1)
                        update_index = int(idx)
                        isFound = True
                        break
                    else:
                        continue
                data = {"id": id, "response": response, "weight": weight}
                if not isFound:
                    df = pd.DataFrame(data, index=[0])
                    df.to_csv(
                        FILE_SUGESSION_WEIGHTAGE, mode="a", index=False, header=False
                    )
                else:
                    suggestion_data.loc[update_index, "weight"] = weight  # type: ignore
                    # writing into the file
                    suggestion_data.to_csv(FILE_SUGESSION_WEIGHTAGE, index=False)
            continue

        # IF the question does not exist, append a new row to the file
        LASTID += 1
        new_row = pd.DataFrame(
            [[LASTID, question, response, label]], columns=general_data.columns
        )
        new_row.to_csv(FILE_GENERAL, mode="a", index=False, header=False)

        # Append new data to the IQL CSV file, skipping duplicates
        new_row = pd.DataFrame([[LASTID, question, label]], columns=iql_data.columns)
        new_row.to_csv(FILE_IQL, mode="a", index=False, header=False)
        new_pending_data["question"].append(question)
        new_pending_data["response"].append(response)
        new_pending_data["label"].append(label)

    # Update the last id in the global config
    # Modify the value of "last_id"
    global_config["data"]["last_id"] = LASTID

    # Write the updated data back to the JSON file
    global_config.to_json(FILE_GLOBAL_CONFIG)

    new_pending_data = pd.DataFrame(new_pending_data)

    # Write the question and response to the correct CSV file based on their label
    for label, group in new_pending_data.groupby("label"):
        filename = os.path.join(folder_name, f"{label}.csv")
        if os.path.exists(filename):
            # Check if questions already exist in the file
            existing_questions = pd.read_csv(filename)["question"]
            new_questions = group["question"][
                ~group["question"].isin(existing_questions)
            ]

            # Append new questions to the file
            if not new_questions.empty:
                group.loc[group["question"].isin(new_questions)][
                    ["question", "response"]
                ].to_csv(filename, mode="a", header=False, index=False)
        else:
            group[["question", "response"]].to_csv(filename, index=False)

    pending_data = pd.DataFrame(columns=["question", "response", "label"])
    pending_data.to_csv(FILE_PENDING_DATA, index=False)


def UpdateLabel(word: str):

    # Read the JSON file
    with open(FILE_PAIRING, "r") as file:
        data = json.load(file)

    types = [d["type"] for d in data]

    # Check if newData already exists in datas
    if word in types:
        index = types.index(word)
        return index
    else:
        synonyms = get_synonyms(word)
        synonyms_as_strings = [str(syn) for syn in synonyms] + [word]

        # Define the new data
        latest_id = len(data)
        newData = {
            "label": latest_id,
            "type": word,
            "keywords": synonyms_as_strings,
        }

        # Add newData to data
        data.append(newData)

        # Write the updated data to the JSON file
        with open(FILE_PAIRING, "w") as file:
            json.dump(data, file)

        return latest_id


def LabelExisting(label: int):
    # Read the JSON file
    with open(FILE_PAIRING, "r") as f:
        data = f.readlines()
    data = json.loads(" ".join(data))

    length = len(data)

    # Check if newData already exists in datas
    if label >= 0 and label < length:
        return True
    else:
        return False


def GenerateContextsData(model):

    COMMON_MODEL = model  # Update everytime this function is called
    hfmodel = T5ForConditionalGeneration.from_pretrained(  # type: ignore
        "ThomasSimonini/t5-end2end-question-generation"
    )
    tokenizer = T5TokenizerFast.from_pretrained("t5-base")
    contexts = pd.read_csv(FILE_CONTEXTS)
    contexts_ = contexts["context"]
    labels = contexts["label"]

    def get_questions(input_string, **generator_args):
        generator_args = {
            "max_length": 256,
            "num_beams": 3,
            "length_penalty": 1.5,
            "no_repeat_ngram_size": 3,
            "early_stopping": True,
        }
        input_string = "generate questions: " + input_string + " </s>"
        input_ids = tokenizer.encode(input_string, return_tensors="pt")
        res = hfmodel.generate(input_ids, **generator_args)  # type: ignore
        output = tokenizer.batch_decode(res, skip_special_tokens=True)
        output = [item.split("<sep>") for item in output]
        return output

    def get_answers(questions, context):
        question_answerer = pipeline(
            "question-answering", model="distilbert-base-cased-distilled-squad", top_k=1  # type: ignore
        )

        final_result = []

        for question in questions:
            result = question_answerer(question=question, context=context)  # type: ignore
            final_result.append([question.strip(), result["answer"]])
        return final_result

    def to_dataframe(question_answer_pairs, default_label):
        df = pd.DataFrame(question_answer_pairs, columns=["question", "response"])
        for index, row in df.iterrows():
            # Detect label here
            COMMON_MODEL.initialize(row["question"])
            label = COMMON_MODEL.get_label()
            df["label"] = label if label != -1 else default_label

        return df

    for i in range(len(contexts_)):
        # for context in contexts:
        context = str(contexts_[i])
        default_label = int(labels[i])
        q = get_questions(context)[0][0]
        q = [i + "?" for i in q.split("?") if i != ""]
        df = to_dataframe(get_answers(q, context), default_label)
        df.to_csv(FILE_PENDING_DATA, mode="a", index=False, header=False)

    # Clear Context file
    df = pd.read_csv(FILE_CONTEXTS)
    df = df.iloc[1:]
    df.to_csv(FILE_CONTEXTS, index=False)
