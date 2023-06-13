import pandas as pd
import numpy as np
import pickle
import nltk
import random

from text_processing import TextProcessing
from text_vectorizing import TextVectorizing
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from files_path import (
    FILE_GENERAL,
    FILE_PAIRING,
    FILE_SUGESSION_WEIGHTAGE,
    DIR_GROUPINGS,
)

# Explanation here
"""
+-------------+
| EXPLANATION |
+-------------+

FINE_TUNING
    After getting the response, the model will check if there is another preferred response generated from feedbacks from agent.
        IF there is
        THEN the preferred response will be returned

        IF there is more than one
        THEN refer to the weight, return the top two response with weight

GENERAL_DATA
    Refer to the data of the "general.csv" file.

LABELLING_MODEL
    The first layer's model of the model object which is used to detect possible label
        IF any of the keywords of the label is matched
        THEN
            IF there is only one label
            THEN return the label

            IF there is not only one label
            THEN move to second layer and use the TEXT_CLASSIFIER_MODEL to figure which is more accurate
                IF the returned value of the text classifier model is in the detected labels list 
                THEN return that returned value

                IF the returned value of the text classifier model is not in the detected labels list
                THEN append the returned value to the detected labels list, return a label randomly

    SUGGESTION FROM BYNG:
        most of the algorithm in this model is applying the linear search, in the future, binary search
        shall be applied to make itself more effective, less calculation time.

    
PREV_SUMMARY_LABELS_WITH_LENGTHS
    Store the previous labels data length:
        IF it is firstly initialised
        THEN data length start with nothing

        IF it is not firsly initialised
        THEN store the current groupings files' length
        // e.g. 
        //      1.csv has 2 datarows and 2.csv has 3 datarows
        //      self.data_length will be {'1': 2, '2': 3}
    This is declared to let model itself to decide if any particular model file needs updating.

SUGGESTION_WEIGHTAGE
    Storing data with [original response id, preferred response, weight]

VOCAB_LIST
    To vectorize the sentences, a vocabulary list is used to stored the word that the model has seen.
        IF the word of a sentence is stored before
        THEN the index of the word in the vocab list will be returned

        IF the word of a sentence is NOT stored before
        THEN the word will be stored into the list and return the index of it.
    
    SUGGESTION FROM BYNG:   
        this is a temporary way to deal with text-vectorizing, in the future, using a vectorizer from other trustable libraries 
        or re-define a new text-vectorizing algorithm is needed to make itself more effective in terms of calculation.

"""


class Model:
    def __init__(self) -> None:

        # This is needed to always update the necessary data for text processing
        nltk.download("wordnet")

        # # Pre-define GENERAL_DATA
        # self.data = pd.read_csv(FILE_GENERAL)

        # Initialise VOCAB_LIST
        self.vocab = []

        # Initialise the PREV_SUMMARY_LABELS_WITH_LENGTH
        self.data_length = dict()

        # Initialise the TEXT_VECTORIZER with 50 max length
        self.vectorizer = TextVectorizing(self.vocab, 50)

        # Start training models if necessary
        self.update()

    def initialize(self, target_sentence):

        # Store passed sentence, in case of later use
        self.target_sentence = target_sentence

        # Get precessed words in list form
        self.processed_target_list = list(
            set(TextProcessing(sentence=self.target_sentence).get_processed_text_list())
        )

    def classify(self):

        # Get PAIRING_DATA
        data = pd.read_json(FILE_PAIRING)

        # Transform and Store the data into the model memory
        self.data_keywords = list(data["keywords"])
        self.data_types = list(data["type"])
        self.data_labels = list(data["label"])

        # Get GENERAL_DATA
        general_data = pd.read_csv(FILE_GENERAL)

        # Declare supportive variables
        isExisting = False
        predicted_response = ""
        possible_label = ""

        # Vectorize sentence
        vec_target_sentence = self.vectorizer.vectorize(self.processed_target_list)

        for idx, (_, r) in enumerate(general_data.iterrows()):

            """
            Check if there is a same VECTORIZED_SENTENCE with the incoming vectorized sentence
                IF there is
                THEN return the response and label
                IF there is not
                THEN proceed to the next step to find out the possible label and possible response
            """

            if (
                self.vectorizer.vectorize(
                    TextProcessing(sentence=r["question"]).get_clean_text()
                )
                == vec_target_sentence
            ):
                predicted_response = r["response"]
                possible_label = r["label"]
                isExisting = True

        # Here is where the model will proceed to the next step to find out the possible label and possible response
        if not isExisting:

            # Generate a sorted processed keywords list of lists
            labels_data_ls = [
                sorted([TextProcessing(sentence=kw).get_clean_text() for kw in kws])
                for kws in self.data_keywords
            ]

            # Update the latest processed keywords list to the LABELLING_MODEL
            self.labelling_model.update_list(labels_data_ls)

            # Get the possible label
            possible_label = self.labelling_model.search(self.processed_target_list)

            # If it is not found
            if possible_label == -1:
                return False

            # Load model through model object file
            mdl = pickle.load(open(f"./data/models/{possible_label}.sav", "rb"))

            # Process the sentence
            s = TextProcessing(sentence=self.target_sentence).get_clean_text()

            # Define a new input text
            new_input_text = [s]

            # Vectorize the new input text
            input_vectors = self.vectorizer.vectorize(new_input_text)

            # Use the model to predict a response for the input text
            predicted_response = mdl.predict(input_vectors)[0]

        """
        SPLIT HERE
        """

        # Get data
        general_data = pd.read_csv(FILE_GENERAL)
        suggestion_data = pd.read_csv(FILE_SUGESSION_WEIGHTAGE)

        # Declare lists that are needed
        res = general_data["response"].tolist()
        ids = general_data["id"].tolist()
        res_ids = [[res[i], ids[i]] for i in range(len(res))]

        # sort the response ids
        res = sorted(res_ids, key=lambda x: x[0][0])  # type: ignore

        # Declare supportive variable
        id = None
        sfs = None
        # index = self.str_binary_search(res, 0, len(res)-1, predicted_response) # Waited to be improved

        # Linear search the id of the response
        for i in res:
            if i[0] == predicted_response:
                id = i[1]
                break

        # Inner class to support formatting the data
        class Suggestion:
            def __init__(self, id, res, w):
                self.id = id
                self.res = res
                self.w = w

        # Declare FINE_TUNING dataset
        list_suggestion_data = [
            Suggestion(int(r["id"]), r["response"], int(r["weight"]))
            for _, r in pd.DataFrame(suggestion_data).iterrows()
        ]

        # IF the id of the response is not existing in the SUGGESTION_WEIGHTAGE
        # THEN no need for fine-tuning
        if id not in [d.id for d in list_suggestion_data]:
            return {"response": [predicted_response], "label": possible_label}

        else:
            # Declare sorted suggestions where the id is matched
            sfs = sorted(
                [d for d in list_suggestion_data if d.id == id],
                key=lambda x: x.w,
                reverse=True,
            )

        # IF the suggestions are more than 2
        # THEN check
        #       IF the top 1's weight not same with the 2nd
        #       THEN return the top 1 and randomly pick one from the suggestions which have the same weight with the 2nd
        #       IF the top 1's weight same with the 2nd
        #       THEN return randomly pick two from suggestions which have the same weight with the top 1
        if len(sfs) >= 2:
            if sfs[0].w != sfs[1].w:
                random_response = random.sample(
                    [d for d in sfs if d.w == sfs[1].w], k=1
                )[0].res
                return {
                    "response": [sfs[0].res, random_response],
                    "label": possible_label,
                }

            else:
                random_response = random.sample(
                    [d for d in sfs if d.w == sfs[0].w], k=2
                )
                random_response = [d.res for d in random_response]
                return {"response": random_response, "label": possible_label}

        # IF the suggestions are less than or equal to 2
        # THEN abstract the responses
        final_res = [i.res for i in sfs]
        return {"response": final_res, "label": possible_label}

    def get_labelling_model(self, _list):
        """
        To:
            1) Loop list through index
            2) Once key word matched return index

        Params:
            1) _list        [LIST] with lists of keywords
            2) _target_list [LIST] with processed words
        """

        # Get labelling model (with Text Classifer)
        # Enable to return the vectorizer (different from customised one) for later use
        (vec, model) = self.get_labelling_model_TC()

        # Inner class of declaring labelling model
        class labelling:
            def __init__(self, ls, tc_model, tc_vec) -> None:
                """
                Params:
                    1) ls[LIST]     list of lists of string
                    2) tls[LIST]    list of target sentence's tokens
                """

                self.ls = ls
                self.tcmd = tc_model
                self.tcvec = tc_vec

            # Update list for enhancing latest searching
            def update_list(self, ls):
                self.ls = ls

            def search(self, tls, easy_search=True, output=[]):
                self.tls = tls

                """
                Searching:
                    [LAYER 1] Easy Search
                    using jaccard similarity to match with keywords

                    [LAYER 2]
                    using text classifer to get the most relavent keywords
                    *** this layer is triggered only if more than 1 matched keywords are found in [LAYER 1]


                Returns:
                    1) -1       [INT] if no match in [LAYER 1]
                    2) Label    [INT]

                """

                import random

                scores = []
                max_score = 0.0
                _output = output

                if easy_search:

                    # Apply Jaccard Similarity Counting
                    for l in self.ls:
                        scores.append(self.jaccard_similarity(l, self.tls))

                    max_score = max(scores)

                    # If any result
                    if max_score != 0.0:

                        # If only 1 result
                        if scores.count(max_score) == 1:
                            return scores.index(max_score)

                        # If more than 1 result
                        # Proceed to layer 2
                        else:
                            _output = [
                                index
                                for index, x in enumerate(scores)
                                if x == max_score
                            ]
                            return self.search(self.tls, False, _output)
                    else:
                        return -1
                else:
                    # Layer 2
                    # Use the Text Classifer(TC) model to predict labels for new data
                    new_data = self.tls
                    new_X = self.tcvec.transform([" ".join(new_data)])
                    new_label = int(self.tcmd.predict(new_X))
                    if new_label in _output:
                        return new_label
                    _output.append(new_label)
                    random.shuffle(_output)
                    return random.choice(_output)

            def jaccard_similarity(self, l1, l2):
                """
                Params:
                    1) l1   [LIST] base list
                    2) l2   [LIST] target list
                Return:
                    value of the similarity of l2 caompared to l1
                """

                s1 = set(l1)
                s2 = set(l2)
                intersection = len(s1.intersection(s2))
                union = len(s1.union(s2))

                return intersection / union if union else 0

        # Returning the labelling model
        return labelling(_list, model, vec)

    def get_labelling_model_TC(self):

        # Declare necessary data
        data = [" ".join(d) for d in self.data_keywords]
        labels = [d for d in self.data_labels]

        # Declare vectorizer
        vectorizer = TfidfVectorizer()

        # Vectorize data
        X = vectorizer.fit_transform(data)

        # Split the data into training and testing sets
        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42
        )

        # Train a Naive Bayes text classification model
        clf = MultinomialNB()
        clf.fit(X_train, y_train)

        return vectorizer, clf

    def get_label(self):
        """
        Returns:
        -1 if no result
        index, otherwise
        """
        return self.labelling_model.search(self.processed_target_list)

    def get_res_model(self):

        # train different model
        import os, os.path

        # path joining version for other paths
        DIR = DIR_GROUPINGS
        grps = len(
            [
                name
                for name in os.listdir(DIR)
                if os.path.isfile(os.path.join(DIR, name))
            ]
        )
        cur_data_length = dict()

        # If the data_length is uninitialised
        if len(self.data_length) == 0:
            for i in range(0, grps):
                file = DIR + f"/{i}.csv"

                # Define the dataset (input text and corresponding labels)
                data = pd.read_csv(file)
                cur_data_length[i] = len(data)

                input_texts = data["question"]
                responses = data["response"]

                for j in range(len(input_texts)):
                    input_texts[j] = TextProcessing(
                        sentence=input_texts[j]
                    ).get_clean_text()

                # Convert the input text into numeric
                input_vectors = self.vectorizer.vectorize(input_texts)

                # Define the Naive Bayes model and train it on the input vectors and labels
                model = MultinomialNB()
                model.fit(input_vectors, responses)

                # Save model object into file for later loading
                pickle.dump(model, open(f"./data/models/{i}.sav", "wb"))

        # If data_length is initialised
        else:
            # Get current data_length
            cur_data_length = {
                i: len(pd.read_csv(DIR + f"/{i}.csv")) for i in range(grps)
            }

            # Validate data_length and cur_data_length
            # Filter out:
            #   IF the grouping(i) file is in the data_length data
            #   THEN check if the prev data_length and cur data_length are different
            #   IF the grouping(i) file is NOT in the data_length data
            #   THEN append to dif_data_length
            dif_data_length = [
                i
                for i in range(len(cur_data_length))
                if (
                    i in self.data_length
                    and i in cur_data_length
                    and self.data_length[i] != cur_data_length[i]
                )
                or i not in self.data_length
            ]

            # Only retrain or update specific models
            if (
                len(self.data_length) != len(cur_data_length)
                or len(dif_data_length) > 0
            ):
                for i in dif_data_length:
                    file = DIR + f"/{i}.csv"

                    # Define the dataset (input text and corresponding labels)
                    data = pd.read_csv(file)
                    cur_data_length[i] = len(data)

                    input_texts = data["question"]
                    responses = data["response"]

                    for j in range(len(input_texts)):
                        input_texts[j] = TextProcessing(
                            sentence=input_texts[j]
                        ).get_clean_text()

                    # Convert the input text into numeric
                    input_vectors = self.vectorizer.vectorize(input_texts)

                    # Define the Naive Bayes model and train it on the input vectors and labels
                    model = MultinomialNB()
                    model.fit(input_vectors, responses)

                    pickle.dump(model, open(f"./data/models/{i}.sav", "wb"))

        # Update data_length record
        self.data_length = cur_data_length

    def update(self):
        # Get latest data
        data = pd.read_json(FILE_PAIRING)
        self.data_keywords = list(data["keywords"])
        self.data_types = list(data["type"])
        self.data_labels = list(data["label"])
        labels_data_ls = [
            sorted([TextProcessing(sentence=kw).get_processed_text() for kw in kws])
            for kws in self.data_keywords
        ]

        # Update model
        self.labelling_model = self.get_labelling_model(labels_data_ls)
        self.get_res_model()

    def get_vocab(self):
        return self.vocab

    def str_binary_search(self, arr, low, high, x):
        # Check base case
        if high >= low:

            mid = (high + low) // 2

            # If element is present at the middle itself
            if arr[mid] == x:
                return mid

            # If element is smaller than mid, then it can only
            # be present in left subarray
            elif arr[mid][0] > x[0]:
                return self.str_binary_search(arr, low, mid - 1, x)

            # Else the element can only be present in right subarray
            else:
                return self.str_binary_search(arr, mid + 1, high, x)

        else:
            # Element is not present in the array
            return -1

    def get_vec_sentence(self):
        return self.processed_target_list
