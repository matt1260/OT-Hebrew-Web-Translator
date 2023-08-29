from django.http import HttpResponse
from django.shortcuts import render, redirect
from search.models import Genesis, GenesisFootnotes, EngLXX, LITV
from django.db.models import Q, Max, Min
import re
# import pythonbible as bible
import requests
import sqlite3

def home(request):
    return HttpResponse("You're at the home page.")

# /chapter/ (not used)
# def chapter(request):
#     chapter_num = request.GET.get('chapter')
#     book = request.GET.get('book')
#     if not chapter_num:
#         return render(request, 'search_input.html')

#     results = Genesis.objects.filter(chapter=chapter_num)
#     text = ''.join([result.text for result in results])

#     context = {'text': text, 'book': book, 'chapter_num': chapter_num}
#     return render(request, 'chapter.html', context)

# Retrieve and format each footnote into a table
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
        rbt_html = rbt.values_list('html', flat=True).first()
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
            esv = f'<p><strong>ESV Translation:</strong><br> {esv_verse_text}</p>'
        else:
            esv = '<p><strong>ESV Translation:</strong><br> Error retrieving verse.</p>'

        # BRENTON SEPTUAGINT in English Updated
        englxx_dict = {'Genesis': 'GEN', 'Exodus': 'EXO', 'Leviticus': 'LEV', 'Numbers': 'NUM', 'Deuteronomy': 'DEU', 'Joshua': 'JOS', 'Judges': 'JDG', 'Ruth': 'RUT', '1 Samuel': '1SA', '2 Samuel': '2SA', '1 Kings': '1KI', '2 Kings': '2KI', '1 Chronicles': '1CH', '2 Chronicles': '2CH', 'Ezra': 'EZR', 'Job': 'JOB', 'Psalms': 'PSA', 'Proverbs': 'PRO', 'Ecclesiastes': 'ECC', 'Song of Solomon': 'SNG', 'Isaiah': 'ISA', 'Jeremiah': 'JER', 'Lamentations': 'LAM', 'Ezekiel': 'EZK', 'Hosea': 'HOS', 'Joel': 'JOL',
               'Amos': 'AMO', 'Obadiah': 'OBA', 'Jonah': 'JON', 'Micah': 'MIC', 'Nahum': 'NAM', 'Habakkuk': 'HAB', 'Zephaniah': 'ZEP', 'Haggai': 'HAG', 'Zechariah': 'ZEC', 'Malachi': 'MAL', 'Tobit': 'TOB', 'Judith': 'JDT', 'Esther': 'ESG', 'Wisdom': 'WIS', 'Sirach': 'SIR', 'Baruch': 'BAR', 'Letter of Jeremiah': 'LJE', 'Susanna': 'SUS', 'Bel and the Dragon': 'BEL', '1 Maccabees': '1MA', '2 Maccabees': '2MA', '1 Esdras': '1ES', 'Prayer of Manasseh': 'MAN', '3 Maccabees': '3MA', '4 Maccabees': '4MA', 'Daniel': 'DAG'}
        englxx_book = englxx_dict.get(book, 'Unknown')
        eng_lxx = EngLXX.objects.filter(
            book=englxx_book)  # run book filter
        eng_lxx = eng_lxx.filter(chapter=chapter_num) # run chapter filter
        eng_lxx = eng_lxx.filter(startVerse=verse_num)  # run verse filter
        eng_lxx = eng_lxx.values_list('verseText', flat=True).first()
        eng_lxx = f'<p><strong>Brenton Septuagint Translation:</strong><br> {eng_lxx}</p>'

        # LITV Translation
        litv = LITV.objects.filter(book=book)
        litv = litv.filter(chapter=chapter_num)
        litv = litv.filter(verse=verse_num)
        litv = litv.values_list('text', flat=True).first()
        litv = f'<p><strong>LITV Translation:</strong><br> {litv}</p>'

        #return rbt, esv, litv, eng_lxx, 
        return {
            'esv': esv,
            'litv': litv,
            'eng_lxx': eng_lxx,
            'rbt': rbt_html,
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
    query = request.GET.get('q')  # search form used
    chapter_num = request.GET.get('chapter')
    book = request.GET.get('book')
    verse_num = request.GET.get('verse')
    footnote_id = request.GET.get('footnote')

    if query:  # search query currently only searches the Genesis table

        results = Genesis.objects.filter(html__icontains=query)

        # Strip only paragraph tags from results
        for result in results:
            result.html = result.html.replace('<p>', '').replace(
                '</p>', '')  # strip the paragraph tags
            
            # Replace all hashtag links with query parameters
            result.html = re.sub(
                r'#(sdfootnote(\d+)sym)', rf'?footnote={result.chapter}-{result.verse}-\g<2>', result.html)
            
            # apply bold to search query
            result.html = re.sub(
                f'({re.escape(query)})',
                r'<strong>\1</strong>',
                result.html,
                flags=re.IGNORECASE
            )

        context = {'results': results, 'query': query}
        return render(request, 'search_results.html', context)

    # SINGLE VERSE
    elif book and chapter_num and verse_num:

        results = get_results(book, chapter_num, verse_num)

        hebrew = results['hebrew']
        rbt = results['rbt']
        esv = results['esv']
        litv = results['litv']
        eng_lxx = results['eng_lxx']
        previous_verse = results['prev_ref']
        next_verse = results['next_ref']
        footnote_contents = results['footnote_content']

        footnotes_content = "<p> ".join(footnote_contents)
        footnotes_content = f'<div style="font-size: 12px;">{footnotes_content}</div>'

        rbt = f'<strong>RBT Translation:</strong><br> {rbt}</p>'

        context = {'previous_verse': previous_verse, 'next_verse': next_verse, 'footnotes': footnotes_content, 'book': book,
                   'chapter_num': chapter_num, 'verse_num': verse_num, 'esv': esv, 'rbt': rbt, 'englxx': eng_lxx, 'litv': litv, 'hebrew': hebrew}

        return render(request, 'verse.html', context)

    # SINGLE CHAPTER
    elif book and chapter_num:

        results = get_results(book, chapter_num)

        html = ""
        for result in results:

            # Replace all hashtag footnote links with query parameters
            # result.html = re.sub(
            #     r'#(sdfootnote(\d+)sym)', rf'?footnote={result.chapter}-{result.verse}-\g<2>', result.html)

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
            
        context = {'html': html, 'book': book, 'chapter_num': chapter_num}
        return render(request, 'chapter.html', context)

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

        context = {'hebrew': hebrew, 'verse_html': verse_html, 'footnote_html': footnote_html,
                   'footnote': footnote_id, 'chapter_ref': chapter_ref, 'verse_ref': verse_ref, }
        return render(request, 'footnote.html', context)

    else:
        return render(request, 'search_input.html')
