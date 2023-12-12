from django.http import HttpResponse
from django.shortcuts import render, redirect
from search.models import Genesis, GenesisFootnotes, EngLXX, LITV
from django.db.models import Q, Max, Min
from django.http import JsonResponse
import json

import re
# import pythonbible as bible
import requests
import sqlite3
from translate.translator import *

GPT_API_KEY = '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'


def home(request):
    return HttpResponse("You're at the home page.")

import requests
from django.http import JsonResponse

def paraphrase(request):
    if request.method == 'POST':
        try:
            # Your input_text extraction code here
            #input_text = request.POST.get('text', '')
            input_text = request.POST.get('text', '').encode('utf-8').decode('utf-8')

            endpoint = "https://api.openai.com/v1/chat/completions"
            prompt = "Edit the following text to paraphrase without removing the Hebrew:"

            # Specify the model
            model = "gpt-3.5-turbo-0613"

            # Create the conversation with the prompt
            conversation = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt} {input_text}"},
            ]

            # Make the API request
            response = requests.post(
                endpoint,
                json={
                    "messages": conversation,
                    "model": model,
                    "max_tokens": 70,
                },
                headers={
                    "Authorization": f"Bearer {GPT_API_KEY}",
                    "Content-Type": "application/json",
                },
            )

            # Check if the request was successful
            if response.status_code == 200:
                # Get the rewritten text from the response
                data = response.json()
                re_paraphrase = data["choices"][0]["message"]["content"]
                return JsonResponse({'paraphrasedText': re_paraphrase})
            
            elif response.status_code == 429:
                # Handle rate limit exceeded error
                return JsonResponse({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
            elif response.status_code == 503:
                # Handle service unavailable error
                return JsonResponse({'error': 'Service is currently unavailable. Please try again later.'}, status=503)
            else:
                return JsonResponse({'error': f'Request failed with status code {response.status_code}'}, status=500)

        except Exception as e:
            # Handle any exceptions and return an error response
            return JsonResponse({'error': str(e)}, status=400)

    # Handle other HTTP methods or return an error response
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Retrieve and format each footnote into a table row
def get_footnote(footnote_id):
    results = GenesisFootnotes.objects.filter(
        footnote_id=footnote_id).values('footnote_html')

    # Split the footnote_id by '-' and get the last slice
    footnote_parts = footnote_id.split('-')
    footnote_ref = footnote_parts[-1]
    chapter = footnote_parts[0]
    verse = footnote_parts[1]

    footnote_html = results[0]['footnote_html']

    # Create an HTML table with two columns
    table_html = f'<tr><td style="border-bottom: 1px solid #d2d2d2;"><a href="?footnote={chapter}-{verse}-{footnote_ref}">{footnote_ref}</a></td><td style="border-bottom: 1px solid #d2d2d2;">{footnote_html}</td></tr>'

    return table_html

def get_results(book, chapter_num, verse_num=None):

    # RBT DATABASE (uses django database. Temporary until rbt_hebrew.db is completed)
    rbt_book_model_map = {
        'Genesis': Genesis,
        # 'Isaiah': Isaiah,
        # Add more book names and model names as needed
    }

    rbt_table = rbt_book_model_map.get(book)
    rbt = rbt_table.objects.filter(chapter=chapter_num)  # run first filter

    if verse_num is not None:
        rbt = rbt.filter(verse=verse_num)
        # corresponds the html column to the verse
        rbt_text = rbt.values_list('text', flat=True).first()
        rbt_html = rbt.values_list('html', flat=True).first()
        rbt_ai = rbt.values_list('rbt_reader', flat=True).first()
        rbt_heb = rbt.values_list('hebrew', flat=True).first()
        record_id_tuple = rbt.values_list('id').first()
        record_id = record_id_tuple[0] if record_id_tuple else None

        rbt_html = rbt_html.replace('</p><p>', '')


        # Generate a list of footnote references found in the verse
        footnote_references = re.findall(r'href="\?footnote=(\d+-\d+-\d+)"', rbt_html)
        footnote_list = footnote_references

        # Create a list to store footnote contents using get_footnote function
        footnote_contents = []
        for footnote_id in footnote_list:
            footnote_content = get_footnote(footnote_id) # get_footnote function
            footnote_contents.append(footnote_content)
        
        
        # Get the previous and next row verse references
        current_row_id = rbt.values_list('id', flat=True).first()

        prev_row_id = rbt_table.objects.filter(id__lt=current_row_id).aggregate(max_id=Max('id'))['max_id']
        prev_ref = rbt_table.objects.filter(id=prev_row_id)
        prev_chapter = prev_ref.values_list('chapter', flat=True).first()
        prev_verse = prev_ref.values_list('verse', flat=True).first()

        next_row_id = rbt_table.objects.filter(id__gt=current_row_id).aggregate(min_id=Min('id'))['min_id']
        next_ref = rbt_table.objects.filter(id=next_row_id)
        next_chapter = next_ref.values_list('chapter', flat=True).first()
        next_verse = next_ref.values_list('verse', flat=True).first()
        
        if prev_chapter is None:
            prev_ref = f'?book={book}&chapter={chapter_num}&verse={verse_num}'
        else:
            prev_ref = f'?book={book}&chapter={prev_chapter}&verse={prev_verse}'
        if next_chapter is None:
            next_ref = f'?book={book}&chapter={chapter_num}&verse={verse_num}'
        else:
            next_ref = f'?book={book}&chapter={next_chapter}&verse={next_verse}'


        ESV_API_PARAMS = {
            'q': f'{book} {chapter_num}:{verse_num}',
            'include-headings': False,
            'include-footnotes': False,
            'include-verse-numbers': False,
        }

        # ESV API
        ESV_API_KEY = '30d1be39f66d44ce5be5a511dc31c949099cd21e'
        ESV_API_URL = 'https://api.esv.org/v3/passage/text/'
        esv_headers = {'Authorization': f'Token {ESV_API_KEY}'}
        esv_response = requests.get(
            ESV_API_URL, params=ESV_API_PARAMS, headers=esv_headers)

        if esv_response.status_code == 200:
            esv_verse_data = esv_response.json()
            esv_verse_text = esv_verse_data['passages'][0]
            index = esv_verse_text.find('\n\n')
            esv_verse_text = esv_verse_text[index + 3:]
            # remove (ESV) from end of verse
            esv_verse_text = esv_verse_text[:-5]
            esv = f'<div class="single_verse"><strong>ESV Translation:</strong><br> {esv_verse_text}</div>'
        else:
            esv = '<div class="single_verse"><strong>ESV Translation:</strong><br> Error retrieving verse.</div>'

        # BRENTON SEPTUAGINT in English Updated
        englxx_dict = {'Genesis': 'GEN', 'Exodus': 'EXO', 'Leviticus': 'LEV', 'Numbers': 'NUM', 'Deuteronomy': 'DEU', 'Joshua': 'JOS', 'Judges': 'JDG', 'Ruth': 'RUT', '1 Samuel': '1SA', '2 Samuel': '2SA', '1 Kings': '1KI', '2 Kings': '2KI', '1 Chronicles': '1CH', '2 Chronicles': '2CH', 'Ezra': 'EZR', 'Job': 'JOB', 'Psalms': 'PSA', 'Proverbs': 'PRO', 'Ecclesiastes': 'ECC', 'Song of Solomon': 'SNG', 'Isaiah': 'ISA', 'Jeremiah': 'JER', 'Lamentations': 'LAM', 'Ezekiel': 'EZK', 'Hosea': 'HOS', 'Joel': 'JOL',
               'Amos': 'AMO', 'Obadiah': 'OBA', 'Jonah': 'JON', 'Micah': 'MIC', 'Nahum': 'NAM', 'Habakkuk': 'HAB', 'Zephaniah': 'ZEP', 'Haggai': 'HAG', 'Zechariah': 'ZEC', 'Malachi': 'MAL', 'Tobit': 'TOB', 'Judith': 'JDT', 'Esther': 'ESG', 'Wisdom': 'WIS', 'Sirach': 'SIR', 'Baruch': 'BAR', 'Letter of Jeremiah': 'LJE', 'Susanna': 'SUS', 'Bel and the Dragon': 'BEL', '1 Maccabees': '1MA', '2 Maccabees': '2MA', '1 Esdras': '1ES', 'Prayer of Manasseh': 'MAN', '3 Maccabees': '3MA', '4 Maccabees': '4MA', 'Daniel': 'DAG'}
        englxx_book = englxx_dict.get(book, 'Unknown')
        eng_lxx = EngLXX.objects.filter(
            book=englxx_book)  # run book filter
        eng_lxx = eng_lxx.filter(chapter=chapter_num) # run chapter filter
        eng_lxx = eng_lxx.filter(startVerse=verse_num)  # run verse filter
        eng_lxx = eng_lxx.values_list('verseText', flat=True).first()
        eng_lxx = f'<div class="single_verse"><strong>Brenton Septuagint Translation:</strong><br> {eng_lxx}</div>'

        # LITV Translation
        litv = LITV.objects.filter(book=book)
        litv = litv.filter(chapter=chapter_num)
        litv = litv.filter(verse=verse_num)
        litv = litv.values_list('text', flat=True).first()
        litv = f'<div class="single_verse"><strong>LITV Translation:</strong><br> {litv}</div>'

        #return rbt, esv, litv, eng_lxx, 
        return {
            'esv': esv,
            'litv': litv,
            'eng_lxx': eng_lxx,
            'rbt_text': rbt_text,
            'rbt': rbt_html,
            'rbt_ai': rbt_ai,
            'hebrew': rbt_heb,
            'footnote_content': footnote_contents,
            'next_ref': next_ref,
            'prev_ref': prev_ref,
            'record_id': record_id
        }
    
    else:
        return rbt

# /RBT/ root home

def search(request):
    query = request.GET.get('q')  # keyword search form used
    chapter_num = request.GET.get('chapter')
    book = request.GET.get('book')
    verse_num = request.GET.get('verse')
    footnote_id = request.GET.get('footnote')

    #  KEYWORD SEARCH
    if query:
        print('Query:', query)
        results = Genesis.objects.filter(html__icontains=query)
        # Strip only paragraph tags from results
        for result in results:
            result.html = result.html.replace('<p>', '').replace('</p>', '')  # strip the paragraph tags

            
            # Apply bold to search query
            result.html = re.sub(
                f'({re.escape(query)})',
                r'<strong>\1</strong>',
                result.html,
                flags=re.IGNORECASE
            )

        # Count the number of results
        rbt_result_count = len(results)

       # Search the hebrew or greek databases
        nt_books = [
            'Mat', 'Mar', 'Luk', 'Joh', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph',
            'Phi', 'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jam',
            '1Pe', '2Pe', '1Jo', '2Jo', '3Jo', 'Jud', 'Rev'
        ]
        ot_books = [
                'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', 'Rut', '1Sa', '2Sa',
                '1Ki', '2Ki', '1Ch', '2Ch', 'Ezr', 'Neh', 'Est', 'Job', 'Psa', 'Pro',
                'Ecc', 'Sng', 'Isa', 'Jer', 'Lam', 'Eze', 'Dan', 'Hos', 'Joe', 'Amo',
                'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal'
            ]
        

        if book == 'all':
            ot_table_query = ' OR '.join([f"Ref LIKE '%{bookref}%'" for bookref in ot_books])
            nt_table_query = ' OR '.join([f"verse LIKE '%{bookref}%'" for bookref in nt_books])

            conn_ot = sqlite3.connect('rbt_hebrew.sqlite3')
            cursor_ot = conn_ot.cursor()
            cursor_ot.execute(f"""
                SELECT * FROM hebrewdata
                WHERE {ot_table_query};
            """)
            ot_rows = cursor_ot.fetchall()
            ot_column_names = [desc[0] for desc in cursor_ot.description]

            conn_nt = sqlite3.connect('rbt_greek.sqlite3')
            cursor_nt = conn_nt.cursor()
            cursor_nt.execute(f"""
                SELECT * FROM strongs_greek
                WHERE {nt_table_query};
            """)
            nt_rows = cursor_nt.fetchall()
            nt_column_names = [desc[0] for desc in cursor_nt.description]
            
    
        elif book == 'NT':
            tablequery = ' OR '.join([f"verse LIKE '%{bookref}%'" for bookref in nt_books])
            conn = sqlite3.connect('rbt_greek.sqlite3')
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM strongs_greek
                WHERE {tablequery};
            """)
            book_rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

        elif book == 'OT':
            tablequery = ' OR '.join([f"Ref LIKE '%{bookref}%'" for bookref in ot_books])
            conn = sqlite3.connect('rbt_hebrew.sqlite3')
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM hebrewdata
                WHERE {tablequery};
            """)
            book_rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

        elif book in ot_books:
            conn = sqlite3.connect('rbt_hebrew.sqlite3')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM hebrewdata
                WHERE Ref LIKE ?;
            """, ('%' + book + '%',)) # 'book' is already abbreviated
            book_rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
        
        else:
            conn = sqlite3.connect('rbt_greek.sqlite3')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM strongs_greek
                WHERE verse LIKE ?;
            """, ('%' + book + '%',)) # 'book' is already abbreviated

            book_rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

        query_count = 0
        links = []

        if book == 'NT' or book in nt_books:
            index = column_names.index('english')
            for row in book_rows:
            # Check if index is not None and 'query' exists in the column (case-insensitive)
                if row[index] and query.lower() in row[index].lower():
                    query_count += 1
                    verse = row[1]
                    bookref = verse[:3]
                    bookref = convert_book_name(bookref)
                    bookref = bookref.lower()
                    bookref = bookref.replace(' ', '_')
                    verse1 = verse[:-3]
                    verse = verse1[4:]
                    verse = verse.replace('.', '-')
                    
                    link = f'<a href="https://biblehub.com/{bookref}/{verse}.htm">{verse1}</a>'
                    links.append(link)

            conn.close()

        elif book == 'OT' or book in ot_books:
            index = column_names.index('Strongs')
            for row in book_rows:
            # Check if index is not None and 'query' exists in the column (case-insensitive)
                if row[index] and query.lower() in row[index].lower():
                    query_count += 1
                    verse = row[1]
                    bookref = verse[:3]
                    bookref = convert_book_name(bookref)
                    bookref = bookref.lower()
                    bookref = bookref.replace(' ', '_')
                    verse1 = verse[:-3]
                    verse = verse1[4:]
                    verse = verse.replace('.', '-')
                    link = f'<a href="https://biblehub.com/{bookref}/{verse}.htm">{verse1}</a>'
                    links.append(link)

        elif ot_rows is not None:
            index_ot = ot_column_names.index('Strongs')
            index_nt = nt_column_names.index('english')

            for row in ot_rows:
                # Check if index is not None and 'query' exists in the column (case-insensitive)
                if row[index_ot] and query.lower() in row[index_ot].lower():
                    query_count += 1
                    verse = row[1]
                    bookref = verse[:3]
                    bookref = convert_book_name(bookref)
                    bookref = bookref.lower()
                    bookref = bookref.replace(' ', '_')
                    verse1 = verse[:-3]
                    verse = verse1[4:]
                    verse = verse.replace('.', '-')
                    link = f'<a href="https://biblehub.com/{bookref}/{verse}.htm">{verse1}</a>'
                    links.append(link)

            for row in nt_rows:
                # Check if index is not None and 'query' exists in the column (case-insensitive)
                if row[index_nt] and query.lower() in row[index_nt].lower():
                    query_count += 1
                    verse = row[1]
                    bookref = verse[:3]
                    bookref = convert_book_name(bookref)
                    bookref = bookref.lower()
                    bookref = bookref.replace(' ', '_')
                    verse1 = verse[:-3]
                    verse = verse1[4:]
                    verse = verse.replace('.', '-')
                    link = f'<a href="https://biblehub.com/{bookref}/{verse}.htm">{verse1}</a>'
                    links.append(link)


        # if individual book is searched convert the full to the abbrev
        if book not in ['NT', 'OT', 'all']:
            book2 = convert_book_name(book)
            book = book2.lower()  
        else:
            book2 = book

        page_title = f'Search results for "{query}"'
        context = {'results': results, 
                   'query': query, 
                   'rbt_result_count': rbt_result_count, 
                   'links': links, 
                   'query_count': query_count,
                   'book2': book2, 
                   'book': book }
        return render(request, 'search_results.html', {'page_title': page_title, **context})


    # SINGLE VERSE
    elif book and chapter_num and verse_num:

        results = get_results(book, chapter_num, verse_num)

        hebrew = results['hebrew']
        rbt = results['rbt']
        rbt_text = results['rbt_text']
        rbt_ai = results['rbt_ai']
        esv = results['esv']
        litv = results['litv']
        eng_lxx = results['eng_lxx']
        previous_verse = results['prev_ref']
        next_verse = results['next_ref']
        footnote_contents = results['footnote_content']

        footnotes_content = "<p> ".join(footnote_contents)
        footnotes_content = f'<div style="font-size: 12px;">{footnotes_content}</div>'

        rbt_paraphrase = rbt_ai

        #rbt = highlight_rbt_lex(rbt)

        rbt = f'<strong>RBT Translation:</strong><div>{rbt}</div>'

        context = {'previous_verse': previous_verse, 
                   'next_verse': next_verse, 
                   'footnotes': footnotes_content, 
                   'book': book,
                   'chapter_num': chapter_num, 
                   'verse_num': verse_num, 
                   'esv': esv, 
                   'rbt': rbt,
                   'rbt_text': rbt_text,
                   'rbt_paraphrase': rbt_paraphrase, 
                   'englxx': eng_lxx, 
                   'litv': litv, 
                   'hebrew': hebrew
                   }
        page_title = f'{book} {chapter_num}:{verse_num}'
        return render(request, 'verse.html', {'page_title': page_title, **context})

    # SINGLE CHAPTER
    elif book and chapter_num:

        results = get_results(book, chapter_num)

        html = ""
        for result in results:

            if '</p><p>' in result.html:
                # Split html into two parts using '</p><p>' as separator
                # and add result.verse in between
                parts = result.html.split('</p><p>')
                html += f'{parts[0]}</p><p><span class="verse_ref"><b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{parts[1]}'
            elif result.html.startswith('<p>'):
                # If HTML starts with '<p>', replace it with the verse_ref link
                html += f'<p><span class="verse_ref"><b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{result.html[3:]}'  # Remove the first '<p>'
            else:
                html += f'<span class="verse_ref"><b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{result.html}'
        
        page_title = f'{book} {chapter_num}'
        context = {'html': html, 'book': book, 'chapter_num': chapter_num}
        return render(request, 'chapter.html', {'page_title': page_title, **context})

    # SINGLE FOOTNOTE
    elif footnote_id:

        chapter_ref, verse_ref, footnote_ref = footnote_id.split('-')

        # book selection
        footnote_html = get_footnote(footnote_id)
        footnote_html = f'<table><tbody>{footnote_html}</tbody></table>'

        verse_results = Genesis.objects.filter(
            chapter=chapter_ref, verse=verse_ref).values('html')
        hebrew_result = Genesis.objects.filter(
            chapter=chapter_ref, verse=verse_ref).values('hebrew')

        hebrew = hebrew_result[0]['hebrew']

        verse_html = verse_results[0]['html']
        verse_html = re.sub(r'#(sdfootnote(\d+)sym)',
                            rf'?footnote={chapter_ref}-{verse_ref}-\g<2>', verse_html)
        verse_results[0]['html'] = verse_html

        context = {'hebrew': hebrew, 
                   'verse_html': verse_html, 
                   'footnote_html': footnote_html,
                   'footnote': footnote_id, 
                   'chapter_ref': chapter_ref, 
                   'verse_ref': verse_ref, 
                   }
        return render(request, 'footnote.html', context)

    else:
        return render(request, 'search_input.html')

def word_view(request):
    rbt_heb_ref = request.GET.get('word')
    use_niqqud = request.GET.get('niqqud')

    if use_niqqud == 'no':
        field = 'combined_heb'
    else:
        field = 'combined_heb_niqqud'

    connection = sqlite3.connect('rbt_hebrew.sqlite3')
    cursor = connection.cursor()
    query = f"""
        SELECT id, Ref, {field}
        FROM hebrewdata WHERE ref = ?;
    """
    cursor.execute(query, (f'{rbt_heb_ref}',))
    rows_data = cursor.fetchall()
    
    id, ref, heb = rows_data[0]
    parameters = (heb,) 
    query = f"""
        SELECT ref, COUNT(*) as count
        FROM hebrewdata
        WHERE {field} = ?
        GROUP BY ref;
    """
    cursor.execute(query, parameters)
    search_results = cursor.fetchall()

    html = '<ol>'
    count = 0
    for result in search_results:
        reference = result[0]  # 'ref' column
        reference = reference.split('-')
        reference = reference[0]
        verse = reference.split('.')
        
        bookref = verse[0]
        bookref = convert_book_name(bookref)
        bookref = bookref.lower()
        bookref = bookref.replace(' ', '_')

        chapter = verse[1]
        verse = verse[2]
        
        link = f'<a href="https://biblehub.com/{bookref}/{chapter}-{verse}.htm">{reference}</a>'
    
        html += f'<li style="margin-top: 0px; font-size: 12px;">{link}</li>'
        count += 1

    html = f'{html}</ol>'
    count = str(count)
    context = {'occurrences': html, 'count': count, 'heb_word': heb }
    
    return render(request, 'word.html', context)