from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from search.models import Genesis, GenesisFootnotes, EngLXX, LITV
from django.db.models import Q
from django.utils.html import escape
from django.contrib.auth.decorators import login_required

import re
import sqlite3
from search.views import get_results
from translate.morph_decode import decode_code
from translate.translator import *
import pythonbible as bible

# /translate/edit_footnote/
@login_required
def edit_footnote(request):

    if request.method == 'GET':
        footnote_id = request.GET.get('footnote')
        chapter_ref, verse_ref, footnote_ref = footnote_id.split('-')
        results = GenesisFootnotes.objects.filter(footnote_id=footnote_id)

    # Update footnote with new text if posted
    elif request.method == 'POST':
        footnote_id = request.POST.get('footnote_id')
        chapter_ref, verse_ref, footnote_ref = footnote_id.split('-')
        results = GenesisFootnotes.objects.filter(footnote_id=footnote_id)
        footnote_html = request.POST.get('footnote_edit')
        results.update(footnote_html=footnote_html)

    # Get results
    verse_results = Genesis.objects.filter(
        chapter=chapter_ref, verse=verse_ref).values('html')
    hebrew_result = Genesis.objects.filter(
        chapter=chapter_ref, verse=verse_ref).values('hebrew')

    hebrew = hebrew_result[0]['hebrew']
    verse_html = verse_results[0]['html']
  
    footnote_ref = footnote_id.split('-')[2]

    footnote_edit = results[0].footnote_html
    footnote_html = results[0].footnote_html

    context = {'hebrew': hebrew, 'verse_html': verse_html, 'footnote_ref': footnote_ref, 'footnote_html': footnote_html, 'footnote_edit': footnote_edit,
            'results': results, 'footnote_id': footnote_id, 'chapter_ref': chapter_ref, 'verse_ref': verse_ref, }
    return render(request, 'edit_footnote.html', context)


# /translate/edit/
# for editing the RBT translation in the model
@login_required
def edit(request):

    query = request.GET.get('q')
    book = request.GET.get('book')
    chapter_num = request.GET.get('chapter')
    verse_num = request.GET.get('verse')

    if request.method == 'POST':
        
        edited_content = request.POST.get('edited_content')
        record_id = request.POST.get('record_id') 
        book = request.POST.get('book')
        chapter_num = request.POST.get('chapter')
        verse_num = request.POST.get('verse')

        record = Genesis.objects.get(id=record_id)
        record.html = edited_content
        record.save()
        
        results = get_results(book, chapter_num, verse_num)

        record_id = results['record_id']
        hebrew = results['hebrew']
        rbt = results['rbt']
        esv = results['esv']
        litv = results['litv']
        eng_lxx = results['eng_lxx']
        previous_verse = results['prev_ref']
        next_verse = results['next_ref']
        footnote_contents = results['footnote_content'] # footnote html rows

        footnotes_content = ' '.join(footnote_contents)
        footnotes_content = footnotes_content.replace('?footnote=', '/RBT/translate/edit_footnote/?footnote=')
        footnotes_content = f'<table><tbody>{footnotes_content}</tbody></table>'

        edit_result = f'<div class="notice-bar"><p><span class="icon"><i class="fas fa-check-circle"></i></span>Updated verse successfully!</p></div>'
        
        context = {'record_id': record_id, 'previous_verse': previous_verse, 'next_verse': next_verse, 'footnotes': footnotes_content, 'book': book,
                   'chapter_num': chapter_num, 'verse_num': verse_num, 'edit_result': edit_result, 'esv': esv, 'rbt': rbt, 'eng_lxx': eng_lxx, 'litv': litv, 'hebrew': hebrew}

        return render(request, 'edit_verse.html', context)

    if query:

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

    elif book and chapter_num and verse_num:
        
        results = get_results(book, chapter_num, verse_num)

        record_id = results['record_id']
        hebrew = results['hebrew']
        rbt = results['rbt']
        esv = results['esv']
        litv = results['litv']
        eng_lxx = results['eng_lxx']
        previous_verse = results['prev_ref']
        next_verse = results['next_ref']
        footnote_contents = results['footnote_content'] # footnote html rows

        footnotes_content = ' '.join(footnote_contents)
        footnotes_content = footnotes_content.replace('?footnote=', '/RBT/translate/edit_footnote/?footnote=')
        footnotes_content = f'<table><tbody>{footnotes_content}</tbody></table>'

        context = {'record_id': record_id, 'previous_verse': previous_verse, 'next_verse': next_verse, 'footnotes': footnotes_content, 'book': book,
                   'chapter_num': chapter_num, 'verse_num': verse_num, 'esv': esv, 'rbt': rbt, 'eng_lxx': eng_lxx, 'litv': litv, 'hebrew': hebrew}

        return render(request, 'edit_verse.html', context)
    
    # displays whole chapter
    elif chapter_num:
        results = get_results(book, chapter_num)
        html = ""
        
        for result in results:
            # Replace all '?footnote=xxx' references with '/edit_footnote/?footnote=xxx'
            modified_html = result.html.replace('?footnote=', '/RBT/edit_footnote/?footnote=')

            if '</p><p>' in modified_html:
                parts = modified_html.split('</p><p>')
                html += f'{parts[0]}</p><p>¶¶<span class="verse_ref"><b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{parts[1]}'
            
            elif modified_html.startswith('<p>'):
                html += f'<p>¶<span class="verse_ref"><b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{modified_html[3:]}'
            
            else:
                html += f'<span class="verse_ref">¶<b><a href="?book={book}&chapter={result.chapter}&verse={result.verse}">{result.verse}</a> </b></span>{modified_html}'

        context = {'html': html, 'book': book, 'chapter_num': chapter_num}
        return render(request, 'edit_chapter.html', context)

    
    else:
        return render(request, 'edit_input.html')


# /translate/
# for editing the hebrew in hebrewdata table
@login_required
def translate(request):

    # Funtion to return count of lexemes found
    def lexeme_search(num, lex):
            where_clause = f"{num} = ?"
            parameter = (f'{lex}',)  
            query = f"""
                SELECT COUNT(*) FROM hebrewdata
                WHERE {where_clause};
            """

            cursor.execute(query, parameter)
            search_count = cursor.fetchone()[0]
            return search_count

    # Function to save edited content to database
    updates = []
    def save_unique_to_database(id, column, data):
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()

        # if data:
        #     update = f'Updated ID: {id} in {column} with "{data}"'
        #     print(update)
        #     updates.append(update)

        cursor.execute(f"""
            UPDATE hebrewdata
            SET {column} = ?
            WHERE id = ?;
        """, (data, id))

        connection.commit()
        connection.close()

    def save_edit_to_database(use_niqqud, heb, column, data):
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()
        excluded_rows_count = 0  # Initialize a count for excluded rows
        print('use niqqud:', use_niqqud)
        if data:
            if use_niqqud == 'true':
                niq = 'with'
                query = f"""
                    UPDATE hebrewdata
                    SET {column} = ?
                    WHERE combined_heb_niqqud = ? AND uniq = '0';
                """

            else:
                niq = 'without'
                query = f"""
                    UPDATE hebrewdata
                    SET {column} = ?
                    WHERE combined_heb = ? AND uniq = '0';
                """

            cursor.execute(query, (data, heb,))
            updated_count = cursor.rowcount
            
            if use_niqqud == 'true':
                cursor.execute("SELECT COUNT(*) FROM hebrewdata WHERE uniq = '1' AND combined_heb_niqqud = ?;", (heb,))
                excluded_rows_count = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM hebrewdata WHERE uniq = '1' AND combined_heb = ?;", (heb,))
                excluded_rows_count = cursor.fetchone()[0]

            excluded_rows = str(excluded_rows_count)
            
            update = f'Updated column  {column} with "{data}" for {updated_count} rows where {heb} {niq} niqqud matches. Excluded {excluded_rows} unique rows.'
            print(update)
            updates.append(update)

            connection.commit()
        connection.close()

    def save_html_to_database(verse_id, html):
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()

        if html:
            update = f'Updated ID: {verse_id} in html with "{html}"'
            print(update)
            updates.append(update)
        cursor.execute(f"""
            UPDATE hebrewdata
            SET html = ?
            WHERE Ref = ?;
        """, (html, verse_id))

        
        connection.commit()
        connection.close()

    def save_footnote_to_database(verse_id, text):

        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()
        
        cursor.execute(f"""
            UPDATE hebrewdata
            SET footnote = ?
            WHERE id = ?;
        """, (text, verse_id))

        connection.commit()
        connection.close()

        update = f'Updated ID: {verse_id} in footnote with "{text}"'
        print(update)
        updates.append(update)

    def save_color_to_database(color_id, color_data):
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT combined_heb
                FROM hebrewdata WHERE id = ?;
            """, (color_id,))
            combined_heb = cursor.fetchone()[0]
            
            cursor.execute(f"""
                UPDATE hebrewdata
                SET color = ?
                WHERE combined_heb = ? AND uniq = '0';
            """, (color_data, combined_heb))
            updated_count = cursor.rowcount

            if color_data:
                update = f'Updated {combined_heb} in color with "{color_data}" for {updated_count} rows.'
                print(update)
                updates.append(update)

            connection.commit()
        except sqlite3.Error as e:
            # Handle any potential errors here
            print("SQLite error:", e)
        finally:
            connection.close()

    log_file = 'replacements.log'

    def find_replace(find_text, replace_text):
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()

        # Update the 'html' column in your database where html text matches 'find_text'.
        cursor.execute("""
            UPDATE hebrewdata
            SET html = REPLACE(html, ?, ?)
            WHERE html LIKE ?;
        """, (find_text, replace_text, f"%{find_text}%"))

        connection.commit()
        connection.close()

        # Get the count of replaced rows and append it to updates.
        updated_count = cursor.rowcount
        updates.append(f'Replaced {updated_count} occurrences of "{find_text}" with "{replace_text}".')
        log_entry = f'Replaced {updated_count} occurrences of "{find_text}" with "{replace_text}".\n'
        with open(log_file, 'a') as log:
            log.write(log_entry)
        return updated_count

    def undo_replacements():
        with open(log_file, 'r') as log:
            log_entries = log.readlines()

        # Undo only the last entry
        if log_entries:
            last_entry = log_entries[-1]
            matches = re.findall(r'"([^"]+)"', last_entry)
            if len(matches) == 2:
                find_text = matches[0]
                replace_text = matches[1]
                updated_count = find_replace(replace_text, find_text)

                if updated_count > 0:
                    updates.append(f'Undid {updated_count} occurrences of "{replace_text}" with "{find_text}".')

        # Remove the last entry from the log file
        with open(log_file, 'w') as log:
            log.writelines(log_entries[:-1])


    ####### POST EDIT

    if request.method == 'POST':
        # Get the list of 'id' and 'eng_data' from the form data
        #eng_id_list = request.POST.getlist('eng_id')
        eng_data_list = request.POST.getlist('eng_data')
        original_eng_data_list = request.POST.getlist('original_eng')
        unique_data_list = request.POST.getlist('unique')
        unique_id_list = request.POST.getlist('unique_id')
        color_id_list = request.POST.getlist('color_id')
        color_data_list = request.POST.getlist('color')
        color_old_list = request.POST.getlist('color_old')
        combined_heb_list = request.POST.getlist('combined_heb')
        combined_heb_niqqud_list = request.POST.getlist('combined_heb_niqqud')
        
        
        use_niqqud = request.POST.get('use_niqqud')
        html = request.POST.get('html')
        verse_id = request.POST.get('verse_id')
        undo = request.POST.get('undo')
        find_text = request.POST.get('find_text')
        replace_text = request.POST.get('replace_text')

        eng_data_list = ['' if item == 'None' else item for item in eng_data_list]
        original_eng_data_list = ['' if item == 'None' else item for item in original_eng_data_list]
        combined_eng_pairs = zip(original_eng_data_list, eng_data_list)
        combined_heb_eng_data_pairs = zip(combined_heb_list, eng_data_list)
        combined_heb_niqqud_eng_data_pairs = zip(combined_heb_niqqud_list, eng_data_list)

        unique_data_list = ['0' if item == 'false' else '1' for item in unique_data_list]
        unique_id_unique_data_pairs = zip(unique_id_list, unique_data_list)
        
        color_data_list = ['f' if item == 'f' else 'm' if item == 'm' else '0' for item in color_data_list]
        combined_old_new_color_pairs = zip(color_old_list, color_data_list)
        color_id_color_data_pairs = zip(color_id_list, color_data_list)
        
        for id, unique_data in unique_id_unique_data_pairs:
            save_unique_to_database(id, 'uniq', unique_data)

        color_change = []
        for old_color, new_color in combined_old_new_color_pairs:
            if old_color != new_color:
                color_change.append((new_color))

        if color_change:
            for id, color_data in color_id_color_data_pairs:
                if color_data in color_change:
                    save_color_to_database(id, color_data)

        eng_change = []
        for old, new in combined_eng_pairs:
            if old != new:
                eng_change.append((new))
        if eng_change:

            if use_niqqud == 'true':

                for heb, eng_data in combined_heb_niqqud_eng_data_pairs:
                    if eng_data in eng_change:
                        save_edit_to_database(use_niqqud, heb, 'Eng', eng_data)
            else:
                for heb, eng_data in combined_heb_eng_data_pairs:
                    if eng_data in eng_change:
                        save_edit_to_database(use_niqqud, heb, 'Eng', eng_data)

        save_html_to_database(verse_id, html)

        if replace_text:
            find_replace(find_text, replace_text)
        if undo == 'true':
            undo_replacements()

        footnotes_data = {}
        old_footnotes_data = {}
        updated_footnotes = {}
        for key, value in request.POST.items():
            if key.startswith('footnote-'):
                footnote_number = key.split('-')[1]
                footnotes_data[footnote_number] = value
        for key, value in request.POST.items():
            if key.startswith('old_footnote-'):
                footnote_number = key.split('-')[1]
                old_footnotes_data[footnote_number] = value
        
        for key in old_footnotes_data:
            # Check if the values don't match between old and new footnotes
            if old_footnotes_data[key] != footnotes_data.get(key):
                updated_footnotes[key] = footnotes_data.get(key)

        for key, text in updated_footnotes.items():
            num = int(key) - 1
            id = color_id_list[num]

            save_footnote_to_database(id, text)


    ###############

    query = request.GET.get('q')
    book = request.GET.get('book')
    chapter_num = request.GET.get('chapter')
    verse_num = request.GET.get('verse')
    page_title = f'{book} {chapter_num}:{verse_num}'
    
    if book == "Genesis":
        results = get_results(book, chapter_num, verse_num)

        record_id = results['record_id']
        hebrew = results['hebrew']
        rbt = results['rbt']
        esv = results['esv']
        litv = results['litv']
        footnote_contents = results['footnote_content'] # footnote html rows
    else:
        rbt = None

    # Convert references to 'Gen.1.1-' format
    if book in book_abbreviations:
        book_abbrev = book_abbreviations[book]
        rbt_heb_ref = f'{book_abbrev}.{chapter_num}.{verse_num}-'
        rbt_heb_chapter = f'{book_abbrev}.{chapter_num}.'
    else:
        rbt_heb_ref = f'{book}.{chapter_num}.{verse_num}-'
        rbt_heb_chapter = f'{book}.{chapter_num}.'

    invalid_verse = ''
    if book is None:
        if query:
            reference = bible.get_references(query)
            if reference:
                ref = reference[0]
                book = ref.book.name
                book = book.title()
                chapter_num = ref.start_chapter
                verse_num = ref.start_verse
                book_abbrev = book_abbreviations[book]
                rbt_heb_ref = f'{book_abbrev}.{chapter_num}.{verse_num}-'
                rbt_heb_chapter = f'{book_abbrev}.{chapter_num}.'
                invalid_verse = ''
            else:
                rbt_heb_ref = 'Gen.1.1-'
                rbt_heb_chapter = 'Gen.1.'
                book = 'Genesis'
                chapter_num = '1'
                verse_num = '1'
                invalid_verse = '<font style="color: red;">Invalid Verse!</font>'

        else:

            rbt_heb_ref = 'Gen.1.1-'
            rbt_heb_chapter = 'Gen.1.'
            book = 'Genesis'
            chapter_num = '1'
            verse_num = '1'
            invalid_verse = ''
    
    
    # results = get_results(book, chapter_num, verse_num)
    # hebrew = results['hebrew']
    # rbt = results['rbt']
    # esv = results['esv']
    # litv = results['litv']
    # eng_lxx = results['eng_lxx']
    # previous_verse = results['prev_ref']
    # next_verse = results['next_ref']
    # footnote_contents = results['footnote_content']
    
    # Get Hebrew from hebrewdata table
    connection = sqlite3.connect('rbt_hebrew.sqlite3')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, Ref, Eng, Heb1, Heb2, Heb3, Heb4, Heb5, Heb6, Morph, uniq, Strongs, color, html, heb1_n, heb2_n, heb3_n, heb4_n, heb5_n, heb6_n, combined_heb, combined_heb_niqqud, footnote
        FROM hebrewdata WHERE ref LIKE ?;
    """, (f'{rbt_heb_ref}%',))
    rows_data = cursor.fetchall()

    cursor.execute("""
        SELECT Ref, html
        FROM hebrewdata WHERE ref LIKE ?;
    """, (f'{rbt_heb_chapter}%',))
    html_rows = cursor.fetchall()

    id = rows_data[0][0]
    ref = rows_data[0][1]
    ref = ref[:-2]
    prev_ref, next_ref = get_prev_next_references(id, ref, cursor)

    verse_id = rbt_heb_ref + '01'
    cursor.execute("""
        SELECT html
        FROM hebrewdata WHERE Ref = ?;
    """, (f'{verse_id}',))
    html = cursor.fetchone()[0]
    
    
    ########## Hebrew Reader at TOP
    # Initialize rows for English and Hebrew
    english_rows = []
    hebrew_rows = []
    morph_rows = []
    strong_rows = []
    
    chapter_reader = ""

    for row in html_rows:
        
        html_verse = row[1]
        if html_verse is not None:
            vrs = row[0].split('.')[2].split('-')[0]
            
            if '<p>' in html_verse:
                html_verse = html_verse.replace('<p>', '').replace('</p>', '')
                html_verse = f'<p><span class="verse_ref"><b>{vrs}</b></span> {html_verse}</p>'
                chapter_reader += html_verse + ' '
                
            else:
                html_verse = f'<span class="verse_ref"><b>{vrs}</b></span> {html_verse}'
                chapter_reader += html_verse + ' '

    # Build the Hebrew row
    for index, row_data in enumerate(rows_data):
        id, ref, eng, heb1, heb2, heb3, heb4, heb5, heb6, morph, unique, strong, color, html_list, heb1_n, heb2_n, heb3_n, heb4_n, heb5_n, heb6_n, combined_heb, combined_heb_niqqud, footnote = row_data

        decoded_morph = decode_code(morph)

        parts = strong.split('/')

        strong_refs = []
        for part in parts:
            subparts = part.split('=')

            for subpart in subparts:
                if subpart.startswith('H'):
                    strong_refs.append(subpart)

            if subparts[0] == 'H9005' or subparts[0] == 'H9001' or subparts[0] == 'H9002' or subparts[0] == 'H9003' or subparts[0] == 'H9004' or subparts[0] == 'H9006':
                    heb1 = f'<span style="color: blue;">{heb1}</span>'
                    
        # Get the definitions for each Strong's reference
        definitions = []
        lemmas = []
        derivations = []
        strong_links = []
        strongs_references = []
        hayah = False
        
        for strong_ref in strong_refs:

            if len(strong_ref) == 6:
                last_character = strong_ref[-1]
            else:
                last_character = '' 

            strong_number = re.sub(r'[^0-9]', '', strong_ref)
            strong_number = int(strong_number)
            strong_number = str(strong_number)
            strong_ref = strong_number + last_character
            if strong_ref == '1961':
                hayah = True
            strong_link = f'<a href="https://biblehub.com/hebrew/{strong_ref}.htm" target="_blank">{strong_ref}</a>'
            
            strong_number = 'H' + strong_number
            cursor.execute("SELECT lemma, xlit, derivation, strongs_def, description FROM strongs_hebrew_dictionary WHERE strong_number = ?", (strong_number,))
            result = cursor.fetchone()
   
            if result is not None:
                lemma = result[0]
                xlit = result[1]
                derivation = result[2]
                definition = result[3]
                description = result[4]
            else:
                definition = 'Definition not found'
                lemma = ''
                derivation = ''
                xlit = ''
                description = ''
            
            single_ref = f'<div class="popup-container">{strong_link}<div class="popup-content"><font size="14">{lemma}</font><br>{xlit}<br><b>Definition: </b>{definition}<br><b>Root: </b>{derivation}<br><b>Exhaustive: </b>{description}</div></div>'
            strongs_references.insert(0, single_ref)

        strongs_references = ' | '.join(strongs_references)

        
        #combined_hebrew = f"{heb1 or ''} {heb2 or ''} {heb3 or ''} {heb4 or ''} {heb5 or ''} {heb6 or ''}".replace(' ', '')
        combined_hebrew = f"{heb1 or ''} {heb2 or ''} {heb3 or ''} {heb4 or ''} {heb5 or ''} {heb6 or ''}"


        at_list = [
            'אָתֶ', 'אֹתִ', 'אתֹ', 'אֹתֵ', 'אֶתֶּ', 'אֵתֻ', 'אַתֵ', 'אתִ', 'אֵתֵ', 'אָתֻ', 'אֵתֶּ', 'אַתִ', 'אֻתֵ', 'אַתּ',
            'את', 'אַת', 'אָתֶּ', 'אתֶ', 'אֵת', 'אֻתַ', 'אתֵ', 'אֹתֻ', 'אִתּ', 'אֵתָ', 'אתֻ', 'אתֶּ', 'אֻתֶּ', 'אֶת', 'אּתֹ',
            'אתּ', 'אּתֻ', 'אֶתֻ', 'אֹת', 'אֹתֶ', 'אֶתָ', 'אּת', 'אָתִ', 'אִתֹ', 'אֹתָ', 'אֻתּ', 'אַתֶּ', 'אָת', 'אֶתּ',
            'אַתֻ', 'את', 'אֹתּ', 'אָתָ', 'אַתָ', 'אַתַ', 'אָתּ', 'אֶתֵ', 'אּתֶּ', 'אּתֵ', 'אִתֶּ', 'אּתִ', 'אֻתָ', 'אֵתִ',
            'אִתֵ', 'אּתָ', 'אֻתֻ', 'אֻת', 'אֻתִ', 'אּתּ', 'אֶתֹ', 'אָתֹ', 'אֵתֶ', 'אֶתִ', 'אִתִ', 'אַתֶ', 'אִתֶ', 'אֵתֹ',
            'אּתַ', 'אֵתּ', 'אָתַ', 'אֶתַ', 'אֶתֶ', 'אָתֵ', 'אִתַ', 'אֹתֶּ', 'אֻתֶ', 'אִתֻ', 'אֻתֹ', 'אַתֹ', 'אֵתַ', 'אתָ',
            'אתַ', 'אֹתֹ', 'אֹתַ', 'אִת', 'אּתֶ', 'אִתָ'
        ]

        # Iterate through the words in the at_list
        for at in at_list:
            # Check if the word exists in the Hebrew text
            if at in combined_hebrew:
                # Replace the word with the same word wrapped in HTML tags for highlighting
                combined_hebrew = combined_hebrew.replace(at, f'<span style="color: #f00;">{at}</span>')

        strong_cell = f'<td style="font-size: 10px;" class="strong-cell">{strongs_references}</td>'
        if hayah == True:
            eng = f'<span class="hayah">{eng}</span>'
        english_cell = f'<td style="font-size: 16px;">{eng}</td>'
        hebrew_cell = f'<td style="font-size: 26px;">{combined_hebrew}</td>'
        morph_cell = f'<td style="font-size: 10px;" class="morph-cell">{decoded_morph}<div class="morph-popup">{morph}</div></td>'

        # Append cells to current row
        strong_rows.append(strong_cell)
        english_rows.append(english_cell)
        hebrew_rows.append(hebrew_cell)
        morph_rows.append(morph_cell)

    # Reverse the order 
    strong_rows.reverse()
    english_rows.reverse()
    hebrew_rows.reverse()
    morph_rows.reverse()

    strong_row = '<tr class="strongs">' + ''.join(strong_rows) + '</tr>'
    english_row = '<tr class="eng_reader">' + ''.join(english_rows) + '</tr>'
    hebrew_row = '<tr class="hebrew_reader">' + ''.join(hebrew_rows) + '</tr>'
    morph_row = '<tr class="morph_reader" style="word-wrap: break-word;">' + ''.join(morph_rows) + '</tr>'


    ######### EDIT TABLE / ENGLISH READER
    edit_table_data = []
    english_verse = []
    footnote_num = 1

    for row_data in rows_data:
        id, ref, eng, heb1, heb2, heb3, heb4, heb5, heb6, morph, unique, strong, color, html_list, heb1_n, heb2_n, heb3_n, heb4_n, heb5_n, heb6_n, combined_heb, combined_heb_niqqud, footnote = row_data

        english_verse.append(eng)


        # Combined pieces search and count
        search_conditions_query1 = []
        parameters_query1 = []
        
        niqqud_translation = str.maketrans('', '', 'ְֱֲֳִֵֶַָֹֻּ')

        for i, heb in enumerate([heb1, heb2, heb3, heb4, heb5, heb6], start=1):
            if heb:
                search_conditions_query1.append(f"Heb{i} = ?")
                parameters_query1.append(f'{heb}')
            else:
                search_conditions_query1.append(f"Heb{i} IS NULL")

        # Join the search conditions using 'AND' and build the final query
        where_clause_query1 = " AND ".join(search_conditions_query1)
        query1 = f"""
            SELECT COUNT(*) FROM hebrewdata
            WHERE {where_clause_query1};
        """

        parameters_query2 = f'{combined_heb}'
        query2 = f"""
            SELECT COUNT(*) FROM hebrewdata
            WHERE combined_heb = ?;
        """

        cursor.execute(query1, parameters_query1)
        search_count = cursor.fetchone()[0]
        search_count = f'<a href="../search/word/?word={ref}">{search_count}</a>'

        cursor.execute(query2, (parameters_query2,))
        search_count2 = cursor.fetchone()[0]
        search_count2 = f'<a href="../search/word/?word={ref}&niqqud=no">{search_count2}</a>'


        # Search and count each individual lexeme
        individual_counts = []
        
        for i, heb in enumerate([heb1_n, heb2_n, heb3_n, heb4_n, heb5_n, heb6_n], start=1):
            
            if heb != '':
                count = lexeme_search(f"heb{i}_n", heb)
                if heb is not None:
                    count = f"{count} <span class='heb'>{heb}</span>"
                if count == 0: count = ''
                individual_counts.append(count if count is not None else '')
            else:   
                individual_counts.append('')

        # Fetch 'Morph' data for the current row
        morph_query = f"""
            SELECT Morph FROM hebrewdata
            WHERE id = ?;
        """
        cursor.execute(morph_query, (id,))
        morph = cursor.fetchone()[0]

        combined_hebrew = f"{heb1 or ''} {heb2 or ''} {heb3 or ''} {heb4 or ''} {heb5 or ''} {heb6 or ''}"

        # Set true or false for unique hebrew words
        if unique == 1:
            unique = f'<select name="unique" autocomplete="off"><option value="true" selected>Unique</option><option value="false">Not Unique</option></select><input type="hidden" name="unique_id" value="{id}">'
        else:
            unique = f'<select name="unique" autocomplete="off"><option value="true">Unique</option><option value="false" selected>Not Unique</option></select><input type="hidden" name="unique_id" value="{id}">'
    

        # Set word color
        if color == 'm':
            color_old = 'm'
            color = f'''<td style="background-color: blue;"><select name="color" autocomplete="off">
                <option name="color" value="m" selected>masc</option>
                <option name="color" value="f">fem</option>
                <option name="color" value="0">none</option>
                </select>
                <input type="hidden" name="color_old" value="{color_old}">
                <input type="hidden" name="color_id" value="{id}"></td>
            '''
        elif color =='f':
            color_old = 'f'
            color = f'''<td style="background-color: #FF1493;"><select name="color" autocomplete="off">
                <option name="color" value="m">masc</option>
                <option name="color" value="f" selected>fem</option>
                <option name="color" value="0">none</option>
                </select>
                <input type="hidden" name="color_old" value="{color_old}">
                <input type="hidden" name="color_id" value="{id}"></td>
                '''
        else:
            color_old = '0'
            color = f'''<td><select name="color" autocomplete="off">
                <option name="color" value="m">masc</option>
                <option name="color" value="f">fem</option>
                <option name="color" value="0" selected>none</option>
                </select>
                <input type="hidden" name="color_old" value="{color_old}">
                <input type="hidden" name="color_id" value="{id}"></td>
                '''

        f = str(footnote_num)

        if footnote:
            footnote_btn = f'''
                <button class="toggleButton" data-target="footnotes-{f}" type="button" style="background-color: #808080; padding: 3px; width: 28px; height: 28px; vertical-align: middle;" onclick="toggleFootnote(this)">
                    &#9662;
                </button>
            '''
        else:
            footnote_btn = f'''
                <button class="toggleButton" data-target="footnotes-{f}" type="button" style="background-color: #808080; padding: 3px; width: 28px; height: 28px; vertical-align: middle;" onclick="toggleFootnote(this)">
                </button>
            '''

        footnote = f'''
        <td colspan="14" class="footnotes-{f}" style="display: none;">
            {footnote}<br>
            <textarea name="footnote-{f}" id="footnote-{f}" autocomplete="off" style="width: 100%;" rows="6">{footnote}</textarea><br>
            <input type="hidden" name="old_footnote-{f}" value="{footnote}">
            <button type="button" style="background-color: #808080; padding: 3px; width: 28px; height: 28px; vertical-align: middle;" onclick="wrapWithHeader('footnote-{f}')">
                <i>H</i>
            </button>
            <button type="button" style="background-color: #808080; padding: 3px; width: 28px; height: 28px; vertical-align: middle;" onclick="wrapTextWithItalics('footnote-{f}')">
                <i>I</i>
            </button>
        </td>
    '''
        # Append all data to edit_table_data
        edit_table_data.append((id, ref, eng, unique, combined_hebrew, color, search_count, search_count2, *individual_counts, morph, combined_heb_niqqud, combined_heb, footnote_btn, footnote))
        
        footnote_num += 1

    cursor.close()
    connection.close()

    english_verse = ' '.join(filter(None, english_verse))
    english_verse = english_verse.replace("אֵת- ", "אֵת-")

  
    if html is not None:
        english_reader = html
    else:
        english_reader = english_verse

    def convert_to_book_chapter_verse(input_verse):
        
        # Split the input string at the '.' character
        parts = input_verse.split('.')

        # Extract the book, chapter, and verse parts
        book = parts[0]
        chapter = parts[1]
        verse = parts[2]
        verse = verse[:-1] # Remove the dash

        # Format the output as 'Book Chapter:Verse'
        formatted_output = f"{book} {chapter}:{verse}"

        return formatted_output

    verse = convert_to_book_chapter_verse(rbt_heb_ref)
    
    context = {'verse': verse, 
               'prev_ref': prev_ref,
               'next_ref': next_ref,
               'rbt': rbt,
               'english_reader': english_reader,
               'english_verse': english_verse,
               'strong_row': strong_row,
               'english_row': english_row, 
               'hebrew_row': hebrew_row,
               'morph_row': morph_row,
               'edit_table_data': edit_table_data,
               'updates': updates,
               'verse_id': verse_id,
               'chapter_reader': chapter_reader,
               'invalid_verse': invalid_verse,
               }
    
    return render(request, 'hebrew.html', {'page_title': page_title, **context})


def search_footnotes(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get("query", "")
        results = []

        # Perform the search in your SQLite database
        footnotes = GenesisFootnotes.objects.filter(footnote_html__icontains=query)

        # Initialize a counter for results
        result_count = 0

        # Create an empty list to store the table rows
        table_rows = []

        # Iterate through footnotes
        for footnote in footnotes:
            # Increment the result count for each footnote
            result_count += 1

            # Split the footnote_id by dashes and get the last slice as the anchor text
            footnote_id_parts = footnote.footnote_id.split('-')
            chapter = footnote_id_parts[0]
            verse = footnote_id_parts[1]
            ref_num = footnote_id_parts[-1]

            # Highlight the matching search term
            highlighted_footnote = footnote.footnote_html.replace(
                query,
                f'<span class="highlighted-search-term">{escape(query)}</span>'
            )

            # Create a table row for the current result
            table_row = f'<tr><td style="vertical-align: top;"><span class="result_verse_header"><a href="/translate/edit/?book=Genesis&chapter={chapter}&verse={verse}">Gen {chapter}:{verse}</a></span><p><a href="/translate/edit_footnote/?footnote={chapter}-{verse}-{ref_num}">#{ref_num}</a></p></td><td>{highlighted_footnote}</td></tr>'

            # Append the table row to the list
            table_rows.append(table_row)

        # Add the result count at the top
        results.append(f"Total results: {result_count}")

        # Create the HTML table
        result_table = f'<table>{"".join(table_rows)}</table>'

        # Add the table to the results
        results.append(result_table)

        return JsonResponse({"results": results})

    return JsonResponse({}, status=400)

@login_required
def find_replace_view(request):
    if request.method == 'POST':
        find_text = request.POST.get('find_text')
        print(find_text)
        replace_text = request.POST.get('replace_text')

        # Query the database to get all GenesisFootnotes records
        footnotes = GenesisFootnotes.objects.all()

        # Perform find and replace for each footnote's footnotes_html field
        replacement_count = 0
        for footnote in footnotes:
            original_content = footnote.footnote_html

            # Save the original content into original_footnotes_html
            footnote.original_footnotes_html = original_content
            updated_content = original_content.replace(find_text, replace_text)

            # Update the database with the modified content
            footnote.footnote_html = updated_content
            footnote.save()
            replacement_count += original_content.count(find_text)

        return render(request, 'find_replace_result.html', {'replacement_count': replacement_count})

    return render(request, 'find_replace.html')

@login_required
def undo_replacements_view(request):

    if request.method == 'POST':
        # Revert the changes by reloading the original content
        footnotes = GenesisFootnotes.objects.all()
        for footnote in footnotes:
            footnote.footnote_html = footnote.original_footnotes_html  # Assuming you have an 'original_footnotes_html' field
            footnote.save()

        # Redirect back to the find and replace page
        return redirect('find_replace')

    return render(request, 'undo_replacements.html')

@login_required
def edit_search(request):
    query = request.GET.get('q')  # keyword search form used
    book = request.GET.get('book')
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
        return render(request, 'edit_search_results.html', {'page_title': page_title, **context})

    if footnote_id:

        redirect_url = f'/RBT/edit_footnote/?footnote={footnote_id}'
        context = {'redirect_url': redirect_url, }
        return render(request, 'footnote_redirect.html', context)
        
    else:
        return render(request, 'edit_input.html')