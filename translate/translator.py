import re
import sqlite3


book_abbreviations = {
    'Genesis': 'Gen',
    'Exodus': 'Exo',
    'Leviticus': 'Lev',
    'Numbers': 'Num',
    'Deuteronomy': 'Deu',
    'Joshua': 'Jos',
    'Judges': 'Jdg',
    'Ruth': 'Rut',
    '1 Samuel': '1Sa',
    '2 Samuel': '2Sa',
    '1 Kings': '1Ki',
    '2 Kings': '2Ki',
    '1 Chronicles': '1Ch',
    '2 Chronicles': '2Ch',
    'Ezra': 'Ezr',
    'Nehemiah': 'Neh',
    'Esther': 'Est',
    'Job': 'Job',
    'Psalms': 'Psa',
    'Proverbs': 'Pro',
    'Ecclesiastes': 'Ecc',
    'Song of Solomon': 'Sng',
    'Isaiah': 'Isa',
    'Jeremiah': 'Jer',
    'Lamentations': 'Lam',
    'Ezekiel': 'Eze',
    'Daniel': 'Dan',
    'Hosea': 'Hos',
    'Joel': 'Joe',
    'Amos': 'Amo',
    'Obadiah': 'Oba',
    'Jonah': 'Jon',
    'Micah': 'Mic',
    'Nahum': 'Nah',
    'Habakkuk': 'Hab',
    'Zephaniah': 'Zep',
    'Haggai': 'Hag',
    'Zechariah': 'Zec',
    'Malachi': 'Mal',
    'Matthew': 'Mat',
    'Mark': 'Mar',
    'Luke': 'Luk',
    'John': 'Joh',
    'Acts': 'Act',
    'Romans': 'Rom',
    '1 Corinthians': '1Co',
    '2 Corinthians': '2Co',
    'Galatians': 'Gal',
    'Ephesians': 'Eph',
    'Philippians': 'Php',
    'Colossians': 'Col',
    '1 Thessalonians': '1Th',
    '2 Thessalonians': '2Th',
    '1 Timothy': '1Ti',
    '2 Timothy': '2Ti',
    'Titus': 'Tit',
    'Philemon': 'Phm',
    'Hebrews': 'Heb',
    'James': 'Jam',
    '1 Peter': '1Pe',
    '2 Peter': '2Pe',
    '1 John': '1Jo',
    '2 John': '2Jo',
    '3 John': '3Jo',
    'Jude': 'Jud',
    'Revelation': 'Rev'
}



# take abbreviation (i.e. 'Gen') and return the next book
def get_next_book(abbreviation):
    for book, abbrev in book_abbreviations.items():
        if abbrev == abbreviation:
            books = list(book_abbreviations.keys())

            current_index = list(book_abbreviations.values()).index(abbrev)

            if current_index < len(books) - 1:
                next_book = books[current_index + 1]
                return next_book
            else:
                return None 
    return None 


def get_previous_book(abbreviation):
    for book, abbrev in book_abbreviations.items():
        if abbrev == abbreviation:
            # Get the list of book abbreviations
            abbrevs = list(book_abbreviations.values())
            
            # Find the index of the current abbreviation
            current_index = abbrevs.index(abbrev)
            
            # Get the previous abbreviation using the index
            if current_index > 0:
                previous_abbrev = abbrevs[current_index - 1]
                return previous_abbrev
            else:
                return None  # No previous abbreviation for the first one
    return None  # Abbreviation not found

# Convert book between abbreviation and full name
def convert_book_name(input_str):
    # Check if the input is an abbreviation
    if input_str == 'Ezk': input_str = 'Eze'
    if input_str == 'Nam': input_str = 'Nah'
    if input_str == 'Jol': input_str = 'Joe'

    if input_str in book_abbreviations.values():
        # Convert abbreviation to full name
        for book, abbrev in book_abbreviations.items():
            if abbrev == input_str:
                return book
    elif input_str in book_abbreviations.keys():
        # Convert full name to abbreviation
        return book_abbreviations[input_str]
    else:
        # Return None for unknown input
        return None

# Get the previous and next row verse reference
def get_prev_next_references(id, ref, cursor):
    parts = ref.split('.')
    last_verse = parts[2]
    last_verse = last_verse[:-1]
    last_verse = int(last_verse)
    next_verse = last_verse + 1
    last_verse -= 1
    last_chapter = parts[1] # use current chapter
    next_chapter = parts[1] # use current chapter
    book = parts[0]
    next_book = parts[0]
    
    if last_verse == 0:
        last_chapter = parts[1]
        last_chapter = int(last_chapter)
        last_chapter -= 1

        if last_chapter == 0:
            previous_book = get_previous_book(parts[0])
            if previous_book:
                book = previous_book
                id = int(id) - 1 # get previous row from current reference to get the previous chapter
                prev_id = str(id)

                cursor.execute("""
                    SELECT id, Ref
                    FROM hebrewdata
                    WHERE id LIKE ?;
                    """, (f'{prev_id}%',))
                row = cursor.fetchone()
                prev_ref = row[1]
                parts = prev_ref.split('.')
                last_chapter = parts[1]
                last_verse = parts[2]
                last_verse = last_verse.split('-')
                last_verse = last_verse[0]

            else:
                book = parts[0]
            
    next = ref.split('.')
    next_verse = next[2]
    next_verse = next_verse[:-1]
    next_verse = int(next_verse) + 1
    next_chapter = next[1]
    next_rbt_heb_ref = f"{next[0]}.{next_chapter}.{next_verse}-"

    # test next reference is valid
    cursor.execute("""
        SELECT Ref
        FROM hebrewdata
        WHERE Ref LIKE ?;
        """, (f'{next_rbt_heb_ref}%',))
    row = cursor.fetchone()

    # if next verse is not valid, try the next chapter
    if row is None:
        print('invalid verse')

        next_chapter = int(next_chapter) + 1
        next_chapter = str(next_chapter)
        next_verse = '1'
        next_ref = f"{next[0]}.{next_chapter}.{next_verse}-"

        cursor.execute("""
            SELECT Ref
            FROM hebrewdata
            WHERE ref LIKE ?;
            """, (f'{next_ref}%',))
        row = cursor.fetchone()
        print(row)

        if row is None: # change to next book
            
            next_book = get_next_book(next[0])
            if next_book is None:
                next_book = 'Genesis'

            book = convert_book_name(book)

            prev_ref = f'?book={book}&chapter={last_chapter}&verse={last_verse}'
            next_ref = f"?book={next_book}&chapter=1&verse=1"
            return prev_ref, next_ref
        else:   
            next_ref = row[1]
            next = next_ref.split('.')
            next_chapter = next[1]
            next_verse = next[2]
            next_verse = next_verse.split('-')
            next_verse = next_verse[0]
            
            book = convert_book_name(book)
            next_book = convert_book_name(next_book)
            
            prev_ref = f'?book={book}&chapter={last_chapter}&verse={last_verse}'
            next_ref = f'?book={next_book}&chapter={next_chapter}&verse={next_verse}'
            return prev_ref, next_ref
    else:
        next_ref = row[0]

        book = convert_book_name(book)
        next_book = convert_book_name(next_book)
        
        prev_ref = f'?book={book}&chapter={last_chapter}&verse={last_verse}'
        next_ref = f'?book={next_book}&chapter={next_chapter}&verse={next_verse}'
        return prev_ref, next_ref
 