"""
Walidatory haseł zgodne z rekomendacjami CERT Polska:
https://cert.pl/posts/2022/01/rekomendacje-techniczne-systemow-uwierzytelniania/

Zasady:
- Minimalna długość hasła: 14 znaków
- Maksymalna długość hasła: 64 znaki (lub więcej)
- NIE wymuszamy znaków specjalnych, cyfr, wielkich liter
- Sprawdzamy hasło na liście słabych/często używanych haseł (CERT PL wordlist)
- Sprawdzamy przewidywalne człony (nazwa firmy, usługi)
- Podajemy dokładny powód odrzucenia hasła
- NIE wymuszamy okresowej zmiany haseł
"""

import os
import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class CERTMinimumLengthValidator:
    """
    Walidator minimalnej długości hasła (CERT PL: co najmniej 14 znaków).
    """
    
    def __init__(self, min_length=14):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"Hasło jest za krótkie. Minimalna wymagana długość to {self.min_length} znaków. "
                  f"Twoje hasło ma {len(password)} znaków."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
    
    def get_help_text(self):
        return _(f"Hasło musi mieć co najmniej {self.min_length} znaków.")


class CERTMaximumLengthValidator:
    """
    Walidator maksymalnej długości hasła (CERT PL: pozwalać na co najmniej 64 znaki).
    """
    
    def __init__(self, max_length=128):
        self.max_length = max_length
    
    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _(f"Hasło jest za długie. Maksymalna dozwolona długość to {self.max_length} znaków. "
                  f"Twoje hasło ma {len(password)} znaków."),
                code='password_too_long',
                params={'max_length': self.max_length},
            )
    
    def get_help_text(self):
        return _(f"Hasło może mieć maksymalnie {self.max_length} znaków.")


class CERTPolishWeakPasswordValidator:
    """
    Walidator słabych haseł na podstawie polskiej listy CERT Polska.
    Lista zawiera ~1 mln najpopularniejszych haseł z wycieków.
    Hasła ładowane są do pamięci jako zbiór (set) przy pierwszym użyciu.
    """
    
    _passwords_cache = None
    
    def __init__(self, wordlist_path=None):
        if wordlist_path is None:
            self.wordlist_path = os.path.join(
                os.path.dirname(__file__), 'password_data', 'wordlist_pl.txt'
            )
        else:
            self.wordlist_path = wordlist_path
    
    @classmethod
    def _load_passwords(cls, path):
        """Ładuje listę słabych haseł do pamięci (cache)."""
        if cls._passwords_cache is None:
            cls._passwords_cache = set()
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word:
                            cls._passwords_cache.add(word)
            except FileNotFoundError:
                pass  # Jeśli plik nie istnieje, walidator jest pomijany
        return cls._passwords_cache
    
    def validate(self, password, user=None):
        passwords = self._load_passwords(self.wordlist_path)
        if password.lower() in passwords:
            raise ValidationError(
                _("To hasło znajduje się na liście często używanych haseł i jest łatwe do odgadnięcia. "
                  "Użyj bardziej unikalnego hasła — najlepiej pełnego zdania lub kilku niepowiązanych słów."),
                code='password_in_weak_list',
            )
    
    def get_help_text(self):
        return _("Hasło nie może znajdować się na liście popularnych/słabych haseł (lista CERT Polska).")


class CERTPredictablePatternValidator:
    """
    Walidator sprawdzający, czy hasło nie zawiera przewidywalnych członów
    (CERT PL: np. nazwa firmy, usługi, systemu).
    """
    
    def __init__(self, predictable_words=None):
        if predictable_words is None:
            self.predictable_words = [
                'szbi', 'system', 'bezpieczenstwo', 'bezpieczeństwo',
                'informacja', 'zarzadzanie', 'zarządzanie',
                'haslo', 'hasło', 'password', 'admin', 'administrator',
                'login', 'user', 'test', 'qwerty', 'abc', '123',
            ]
        else:
            self.predictable_words = predictable_words
    
    def validate(self, password, user=None):
        password_lower = password.lower()
        
        # Sprawdź czy hasło zawiera przewidywalne człony
        for word in self.predictable_words:
            if len(word) >= 4 and word.lower() in password_lower:
                raise ValidationError(
                    _(f"Hasło zawiera przewidywalny fragment \"{word}\". "
                      f"Unikaj nazw systemu, firmy lub oczywistych słów."),
                    code='password_predictable',
                    params={'predictable_word': word},
                )
        
        # Sprawdź czy hasło jest prostą sekwencją klawiatury
        keyboard_patterns = [
            'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
            'qwerty', 'asdfgh', 'zxcvbn',
            'qazwsx', 'wsxedc', '1qaz2wsx',
            'zaq1xsw2', 'qaz123', 'asd123',
        ]
        for pattern in keyboard_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("Hasło zawiera sekwencję klawiaturową, która jest łatwa do odgadnięcia. "
                      "Użyj bardziej losowego hasła."),
                    code='password_keyboard_pattern',
                )
        
        # Sprawdź czy hasło to powtórzenie jednego znaku/wzorca
        if len(set(password)) <= 2 and len(password) >= 14:
            raise ValidationError(
                _("Hasło składa się z powtarzających się znaków i jest łatwe do odgadnięcia."),
                code='password_repeating',
            )
        
        # Sprawdź dane użytkownika
        if user is not None:
            user_attrs = ['username', 'first_name', 'last_name', 'email']
            for attr in user_attrs:
                value = getattr(user, attr, None)
                if value and len(value) >= 3 and value.lower() in password_lower:
                    raise ValidationError(
                        _("Hasło nie może zawierać Twoich danych osobowych "
                          "(nazwa użytkownika, imię, nazwisko, email)."),
                        code='password_contains_user_data',
                    )
    
    def get_help_text(self):
        return _("Hasło nie może zawierać przewidywalnych fragmentów "
                 "(nazwa systemu, firmy, danych osobowych, sekwencji klawiaturowych).")


class CERTNoSequentialValidator:
    """
    Walidator sprawdzający, czy hasło nie jest prostą sekwencją numeryczną/alfabetyczną.
    """
    
    def validate(self, password, user=None):
        # Sprawdź sekwencje numeryczne (123456..., 987654...)
        if password.isdigit() and len(password) >= 6:
            digits = [int(d) for d in password]
            is_ascending = all(digits[i] == digits[i-1] + 1 for i in range(1, len(digits)))
            is_descending = all(digits[i] == digits[i-1] - 1 for i in range(1, len(digits)))
            if is_ascending or is_descending:
                raise ValidationError(
                    _("Hasło jest prostą sekwencją numeryczną i jest łatwe do odgadnięcia."),
                    code='password_sequential_numbers',
                )
        
        # Sprawdź czy hasło składa się wyłącznie z cyfr
        if password.isdigit():
            raise ValidationError(
                _("Hasło składające się wyłącznie z cyfr jest łatwe do odgadnięcia. "
                  "Dodaj litery, aby zwiększyć bezpieczeństwo."),
                code='password_only_digits',
            )
    
    def get_help_text(self):
        return _("Hasło nie może być prostą sekwencją numeryczną ani składać się wyłącznie z cyfr.")
