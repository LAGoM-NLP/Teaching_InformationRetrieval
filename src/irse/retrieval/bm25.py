from typing import List, Iterable, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)

from tktkt.preparation.mappers import Lowercaser, FilterCharacters, MapperSequence, Stripper
from tktkt.preparation.instances import TraditionalPretokeniser, Preprocessor, PunctuationPretokeniser

from rank_bm25 import BM25Okapi

SimpleNormaliser = MapperSequence([
    Stripper(),
    Lowercaser(),
    FilterCharacters(PunctuationPretokeniser.buildPunctuationString())
])

class OkapiRetrieval:

    def __init__(self, corpus: Iterable[str]):
        self.pretokeniser = Preprocessor(
            uninvertible_mapping=SimpleNormaliser,
            splitter=TraditionalPretokeniser()
        )
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords  = set(stopwords.words("english"))

        self.retriever = BM25Okapi([self._preprocess(document) for document in corpus])

    def _preprocess(self, doc: str) -> List[str]:
        return [self.lemmatizer.lemmatize(t) for t in self.pretokeniser.do(doc) if t not in self.stopwords]

    def filter(self, query: str, truncate_at: int=None) -> List[Tuple[int, float]]:
        scores = self.retriever.get_scores(self._preprocess(query))
        ranking = sorted(filter(lambda x: x[1] > 0, enumerate(scores)), key=lambda x: x[1], reverse=True)
        return ranking[:truncate_at]
