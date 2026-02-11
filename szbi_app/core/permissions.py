"""
Predefiniowane uprawnienia w systemie SZBI.
Te uprawnienia są ładowane do bazy danych przez migrację.
"""


PERMISSIONS = [

    # ============== DEKLARACJE ZGODNOŚCI ==============
    {
        'category': 'compliance',
        'name': 'Administrator deklaracji zgodności',
        'description': 'Przeglądanie wszystkich deklaracji zgodności i zmiana ich właścicieli'
    },
    {
        'category': 'compliance',
        'name': 'Właściciel deklaracji zgodności',
        'description': 'Pełne uprawnienia do tworzenia, edycji i zarządzania cyklem życia deklaracji zgodności'
    },
    {
        'category': 'compliance',
        'name': 'Menedżer deklaracji zgodności',
        'description': 'Zarządzanie przypisanymi deklaracjami zgodności - edycja, aktualizacja statusu i przesyłanie do zatwierdzenia'
    },
    {
        'category': 'compliance',
        'name': 'Zatwierdzający deklaracje zgodności',
        'description': 'Uprawnienia do zatwierdzania i odrzucania deklaracji zgodności przesyłanych do akceptacji'
    },
    
    # ============== DOKUMENTY ==============
    {
        'category': 'documents',
        'name': 'Administrator dokumentów',
        'description': 'Przeglądanie wszystkich dokumentów i zmiana ich właścicieli'
    },
    {
        'category': 'documents',
        'name': 'Właściciel dokumentów',
        'description': 'Pełne uprawnienia do tworzenia, edycji, usuwania i zarządzania cyklem życia dokumentów'
    },
    {
        'category': 'documents',
        'name': 'Menedżer dokumentów',
        'description': 'Zarządzanie przypisanymi dokumentami, edycja, aktualizacja statusu i przesyłanie do zatwierdzenia'
    },
    {
        'category': 'documents',
        'name': 'Zatwierdzający dokumenty',
        'description': 'Uprawnienia do zatwierdzania i odrzucania dokumentów przesyłanych do akceptacji'
    },
    {
        'category': 'documents',
        'name': 'Podpisujący dokumenty',
        'description': 'Uprawnienia do podpisywania dokumentów'
    },
    {
        'category': 'documents',
        'name': 'Weryfikujący podpisy elektroniczne',
        'description': 'Uprawnienia do weryfikacji podpisów elektronicznych w module dokumentów'
    },
    
    # ============== DZIENNIK ZDARZEŃ ==============
    {
        'category': 'activity_log',
        'name': 'Przeglądanie dziennika zdarzeń',
        'description': 'Przeglądanie wszystkich zdarzeń w rejestrze'
    },
    
    # ============== INCYDENTY BEZPIECZEŃSTWA ==============
    {
        'category': 'incidents',
        'name': 'Przeglądanie wszystkich incydentów bezpieczeństwa',
        'description': 'Dostęp do przeglądania wszystkich incydentów bezpieczeństwa bez możliwości ich edycji'
    },
    {
        'category': 'incidents',
        'name': 'Przeglądanie moich incydentów bezpieczeństwa',
        'description': 'Dostęp do przeglądania incydentów bezpieczeństwa, które zostały przez mnie zgłoszone'
    },
    {
        'category': 'incidents',
        'name': 'Administrator incydentów bezpieczeństwa',
        'description': 'Przeglądanie wszystkich incydentów bezpieczeństwa i zmiana ich właścicieli'
    },
    {
        'category': 'incidents',
        'name': 'Zarządzanie przypisanymi incydentami bezpieczeństwa',
        'description': 'Pełne zarządzanie incydentami bezpieczeństwa, do których jestem przypisany jako właściciel lub menedżer'
    },
    
    # ============== REJESTR AKTYWÓW ==============
    {
        'category': 'assets',
        'name': 'Administrator rejestru aktywów',
        'description': 'Przeglądanie wszystkich aktywów i zmiana ich właścicieli, tworzenie grup aktywów'
    },
    {
        'category': 'assets',
        'name': 'Właściciel rejestru aktywów',
        'description': 'Pełne uprawnienia do tworzenia, edycji, usuwania i zarządzania aktywami w rejestrze'
    },
    {
        'category': 'assets',
        'name': 'Przeglądanie rejestru aktywów',
        'description': 'Przeglądanie wszystkich aktywów w rejestrze bez możliwości edycji'
    },
    
    # ============== WYMAGANIA STANDARDÓW I PRZEPISÓW ==============
    {
        'category': 'dictionary',
        'name': 'Zarządzanie słownikami wymagań norm i przepisów',
        'description': 'Pełne uprawnienia do tworzenia, edycji i usuwania słowników wymagań norm i przepisów'
    },
]


# Słownik kategorii do wyświetlania
CATEGORY_LABELS = {
    'compliance': 'Deklaracje zgodności',
    'documents': 'Dokumenty',
    'activity_log': 'Dziennik zdarzeń',
    'incidents': 'Incydenty bezpieczeństwa',
    'assets': 'Rejestr aktywów',
    'dictionary': 'Wymagania standardów i przepisów',
}


def get_permissions_by_category():
    """Zwraca uprawnienia pogrupowane według kategorii"""
    grouped = {}
    for perm in PERMISSIONS:
        cat = perm['category']
        if cat not in grouped:
            grouped[cat] = {
                'label': CATEGORY_LABELS.get(cat, cat),
                'permissions': []
            }
        grouped[cat]['permissions'].append(perm)
    return grouped
