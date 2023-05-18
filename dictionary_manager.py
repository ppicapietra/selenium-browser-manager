import itertools

class DictionaryManager:
    
    def __init__(self, keyword_length: int, alphabet: list = None):
        """
        Initializes the object with a given keyword length and an optional alphabet.
        
        Args:
            keyword_length (int): The length of the keyword to use.
            alphabet (list, optional): A list of literals to use as the alphabet. 
                If not provided, a default alphabet (English lowercase letters) is used.
        """
        if alphabet is None:
            alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        
        self._alphabet = alphabet
        self._dictionary = [''.join(comb) for comb in itertools.product(self._alphabet, repeat=keyword_length)]
        self._current_keyword = None

    @property
    def current_keyword(self):
        return self._current_keyword
    
    def extend_keyword(self, keyword):
        new_keywords = [keyword + letter for letter in self._alphabet]
        for new_keyword in reversed(new_keywords):
            self._dictionary.insert(0, new_keyword)

    def get_next_keyword(self):
        if self._dictionary:
            self._current_keyword = self._dictionary.pop(0)
            return self._current_keyword
        else:
            return None
