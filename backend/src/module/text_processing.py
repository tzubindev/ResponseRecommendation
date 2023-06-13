from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag

import re
import nltk

import pandas as pd
from files_path import FILE_TAGS


class TextProcessing:
    def __init__(self, data_frame=None, sentence=None) -> None:
        self.df = data_frame
        self.sentence = sentence

        if data_frame is None and sentence is None:
            raise ValueError("No data frame or sentence was provided!")

        self.STOPWORDS = set(stopwords.words("english"))  # type: ignore
        self.MIN_WORDS = 3
        self.MAX_WORDS = 200
        self.PATTERN_S = re.compile("'s")  # matches `'s` from text
        self.PATTERN_RN = re.compile("\\r\\n")  # type: ignore # matches `\r` and `\n`
        self.PATTERN_PUNC = re.compile(r"[^\w\s]")  # matches all non 0-9 A-z whitespace
        self.stemmer = WordNetLemmatizer()

    def get_clean_text(self, text=None):
        """
        Clean:
            1) Uppercase
            2) Non-words char
            3) Numbers (Punc)

        Return:
            cleaned text || None if empty
        """

        if text == None:
            text = self.sentence
        text = str(text).lower()
        text = re.sub(self.PATTERN_RN, " ", text)
        text = re.sub(self.PATTERN_S, " ", text)
        text = re.sub(self.PATTERN_PUNC, " ", text)
        text = text.replace("_", " ")

        text = text.split()
        new_text = []
        for t in text:
            if (
                t not in self.STOPWORDS
                and len(t) > self.MIN_WORDS
                and len(t) < self.MAX_WORDS
            ):
                new_text.append(t)

        return " ".join(new_text)

    def tokenize(
        self,
        sentence,
        min_words=None,
        max_words=None,
        stopwords=None,
    ):
        min_words = self.MIN_WORDS if min_words == None else min_words
        max_words = self.MAX_WORDS if max_words == None else max_words
        stopwords = self.STOPWORDS if stopwords == None else stopwords

        """
        To:
            1) Lemmatize
            2) Tokenize
            3) Crop
            4) Remove Stop Words

        Params:
            1) sentence (str)
            2) min_words (int)
            3) max_words (int)
            4) stopwords (set of string)
            5) lemmatize (boolean)

        Returns:
            list of string
        """
        tags_data = pd.read_json(FILE_TAGS)["tags"]
        for key, item in tags_data.items():
            tags_data[key] = self.get_clean_text(item)
        l_tags = ["adjective", "adverb", "noun", "verb"]
        s_tags = ["a", "r", "n", "v"]

        tokens = [w for w in word_tokenize(str(sentence))]
        tokens = pos_tag(tokens)
        tokens = [[word, tags_data[tag]] for word, tag in tokens]
        new_tokens = []

        for i in range(len(tokens)):
            isFound = False
            for j in range(len(l_tags)):
                if l_tags[j] in tokens[i][1]:
                    new_tokens.append(self.stemmer.lemmatize(tokens[i][0], s_tags[j]))
                    isFound = True
                    break
            if not isFound:
                new_tokens.append(tokens[i][0])

        tokens = new_tokens
        del new_tokens

        tokens = [
            word
            for word in tokens
            if (
                len(word) >= min_words
                and len(word) <= max_words
                and word not in stopwords
            )
        ]

        return tokens

    def get_clean_sentences(self):
        """
        To:
            1) Remove irrelavant characters
            2) Lemmatize, tokenize words into list of words

        Params:
            df (dataframe)

        Returns:
            df
        """
        if self.df != None:
            df = self.df
            df["sentence"] = [str(s) for s in df["sentence"]]
            df["clean_sentence"] = [self.get_clean_text(s) for s in df["sentence"]]
            df["tok_lem_sentence"] = [self.tokenize(s) for s in df["clean_sentence"]]
            df["sentence"] = [
                " ".join(self.tokenize(s)) for s in df["tok_lem_sentence"]
            ]

            del df["clean_sentence"]
            del df["tok_lem_sentence"]
            return df
        return self.df

    def get_processed_text(self):
        return str(
            " ".join(self.tokenize(self.get_clean_text(self.sentence)))
        )  # type:ignore

    def get_processed_text_list(self):
        return self.tokenize(self.get_clean_text(self.sentence))
