from text_processing import TextProcessing


class TextVectorizing:
    def __init__(self, vocab=[], vec_max_length=100) -> None:
        self.vec_max_length = vec_max_length
        self.vocab = vocab

    def vectorize(self, texts_list):
        input_vectors = []
        for i in range(len(texts_list)):
            tls = TextProcessing(sentence=texts_list[i]).get_clean_text().split()
            text_vec = []
            for w in tls:
                if w not in self.vocab:
                    self.vocab.append(w)
                text_vec.append(self.vocab.index(w) + 1)
            for _ in range(self.vec_max_length - len(text_vec)):
                text_vec.append(0)
            input_vectors.append(text_vec)
        return input_vectors

    def vectorize_sentence_list(self, sentence_list):
        input_vectors = []
        for i in range(len(sentence_list)):
            tls = TextProcessing(sentence=sentence_list[i]).get_clean_text().split()
            for w in tls:
                if w not in self.vocab:
                    self.vocab.append(w)
                input_vectors.append(self.vocab.index(w) + 1)
        for _ in range(self.vec_max_length - len(input_vectors)):
            input_vectors.append(0)

        return input_vectors

    def getVocab(self):
        return self.vocab
