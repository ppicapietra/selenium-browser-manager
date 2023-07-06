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
    
    def extend_current_keyword(self):
        if self._current_keyword is None:
            raise Exception("Current keyword is None")
        
        new_keywords = [self._current_keyword + letter for letter in self._alphabet]
        for new_keyword in reversed(new_keywords):
            self._dictionary.insert(0, new_keyword)

    def get_next_keyword(self):
        if self._dictionary:
            self._current_keyword = self._dictionary.pop(0)
            return self._current_keyword
        else:
            return None
    
    def init_from(self, word: str):
        """
        Initialize the dictionary from a given word.
        The method will recreate the operations needed to arrive to the given word,
        removing all the words that are lexicographically less than the given word.

        Args:
            word (str): The word to start from. All characters in the word should be in the predefined alphabet.

        Raises:
            ValueError: If the word contains characters not in the predefined alphabet.

        """
        # Check that all characters in the word are in the predefined alphabet
        if not all(char in self._alphabet for char in word):
            raise ValueError(f"Word contains invalid characters: {word}")
        if len(word) < len(self._dictionary[0]) or word < self._dictionary[0]:
            raise ValueError(f"Word length is minor than minimum word length limit")

        # Make a copy of the alphabet
        aux_alphabet = self._alphabet[:]

        # Define a prefix variable
        prefix = ""

        # Iterate through each character in the word
        for char in word:
            # Add the character to the prefix
            prefix += char
            
            # If the prefix has more than one character
            if len(prefix) > 1:
                # Remove the first letter from the auxiliary alphabet
                letter_to_be_extended = aux_alphabet.pop(0)

                # Generate new keywords by appending each character in the alphabet to the letter_to_be_extended
                # Only include the new keywords that are lexicographically equal or larger than the prefix
                # The new keywords are inserted at the beginning of the auxiliary alphabet
                for new_keyword in reversed([letter_to_be_extended + letter for letter in self._alphabet if prefix <= letter_to_be_extended + letter]):
                    aux_alphabet.insert(0, new_keyword)

            # If the prefix has only one character, update the auxiliary alphabet to only include characters that are lexicographically equal or larger than the character
            else:    
                aux_alphabet = [c for c in aux_alphabet if c >= char]

        self._dictionary = aux_alphabet
