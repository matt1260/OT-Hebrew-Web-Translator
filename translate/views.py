from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from search.models import Genesis, GenesisFootnotes, EngLXX, LITV
from django.db.models import Q
from django.utils.html import escape
from django.contrib.auth.decorators import login_required

import re
# import pythonbible as bible
import requests
import sqlite3
from search.views import get_results


# /translate/edit_footnote/
@login_required
def edit_footnote(request):

    footnote_id = request.GET.get('footnote')
    chapter_ref, verse_ref, footnote_ref = footnote_id.split('-')
    results = GenesisFootnotes.objects.filter(footnote_id=footnote_id)

    # Update footnote with new text if posted
    if request.method == 'POST':
        footnote_html = request.POST['footnote_edit']
        results.update(footnote_html=footnote_html)

    # Get results
    verse_results = Genesis.objects.filter(
        chapter=chapter_ref, verse=verse_ref).values('html')
    hebrew_result = Genesis.objects.filter(
        chapter=chapter_ref, verse=verse_ref).values('hebrew')

    hebrew = hebrew_result[0]['hebrew']
    verse_html = verse_results[0]['html']
    # verse_html = re.sub(r'#(sdfootnote(\d+)sym)',
    #                     rf'?footnote={chapter_ref}-{verse_ref}-\g<2>', verse_html)
    verse_results[0]['html'] = verse_html

    footnote_edit = results[0].footnote_html
    footnote_html = results[0].footnote_html

    context = {'hebrew': hebrew, 'verse_html': verse_html, 'footnote_html': footnote_html, 'footnote_edit': footnote_edit,
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
    footnote_id = request.GET.get('footnote')

    if request.method == 'POST':
        
        edited_content = request.POST.get('edited_content')
        record_id = request.POST.get('record_id') 
        book = request.POST.get('book')
        chapter_num = request.POST.get('chapter')
        verse_num = request.POST.get('verse')
        
        print(edited_content)

        record = Genesis.objects.get(id=record_id)
        record.html = edited_content
        record.save()

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
        footnotes_content = footnotes_content.replace('?footnote=', '/translate/edit_footnote/?footnote=')
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
            modified_html = result.html.replace('?footnote=', '/translate/edit_footnote/?footnote=')

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
@login_required
def translate(request):

    def save_edited_english_to_database(id, eng_data):
        # Connect to the rbt_hebrew.sqlite3 database
        connection = sqlite3.connect('rbt_hebrew.sqlite3')
        cursor = connection.cursor()

        # Perform the UPDATE query to update the 'Eng' column for the given 'id'
        cursor.execute("""
            UPDATE hebrewdata
            SET Eng = ?
            WHERE id = ?;  -- Replace 'id' with your unique identifier field name
        """, (eng_data, id))

        # Commit the changes and close the database connection
        connection.commit()
        connection.close()

    if request.method == 'POST':
        # Get the list of 'id' and 'eng_data' from the form data
        id_list = request.POST.getlist('id')
        eng_data_list = request.POST.getlist('eng_data')

        # Pair each 'id' with its corresponding 'eng_data' using zip
        id_eng_data_pairs = zip(id_list, eng_data_list)

        # Process the id_eng_data_pairs and save the updated 'eng_data' to the database
        for id, eng_data in id_eng_data_pairs:
            # Save the 'eng_data' corresponding to the 'id' to the database
            save_edited_english_to_database(id, eng_data)
        
        #return redirect('translate')  # Redirect to the same page after processing the data

    # Get the input 'ref' from the request's GET parameters
    rbt_heb_ref = request.GET.get('ref')

    book = request.GET.get('book')
    chapter_num = request.GET.get('chapter')
    verse_num = request.GET.get('verse')

    book_abbreviations = {
        'Genesis': 'Gen',
        'Exodus': 'Exo',
        'Leviticus': 'Lev',
        'Numbers': 'Num',
        'Deuteronomy': 'Deu',
    }

    # Convert references to 'Gen.1.1-' format
    if book in book_abbreviations:
        book_abbrev = book_abbreviations[book]
        rbt_heb_ref = f'{book_abbrev}.{chapter_num}.{verse_num}-'
    else:
        rbt_heb_ref = f'{book}.{chapter_num}.{verse_num}-'

    if book is None:
        rbt_heb_ref = 'Gen.1.1-'
        book = 'Genesis'
        chapter_num = '1'
        verse_num = '1'

    results = get_results(book, chapter_num, verse_num)
    hebrew = results['hebrew']
    rbt = results['rbt']
    esv = results['esv']
    litv = results['litv']
    eng_lxx = results['eng_lxx']
    previous_verse = results['prev_ref']
    next_verse = results['next_ref']
    footnote_contents = results['footnote_content']
    
    # Get Hebrew from rbt_hebrew database
    connection = sqlite3.connect('rbt_hebrew.sqlite3')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, Ref, Eng, Heb1, Heb2, Heb3, Heb4, Heb5, Heb6
        FROM hebrewdata WHERE ref LIKE ?;
    """, (f'{rbt_heb_ref}%',))
    rows_data = cursor.fetchall()

    # Hebrew Reader at TOP
    english_row = '<tr>'
    hebrew_row = '<tr>'

    for row_data in rows_data:
        id, ref, eng, heb1, heb2, heb3, heb4, heb5, heb6 = row_data

        combined_hebrew = f"{heb1 or ''} {heb2 or ''} {heb3 or ''} {heb4 or ''} {heb5 or ''} {heb6 or ''}"

        english_row = f'<td style="font-size: 16px;">{eng}</td>' + english_row
        hebrew_row = f'<td style="font-size: 26px;">{combined_hebrew}</td>' + hebrew_row

    english_row += '</tr>'
    hebrew_row += '</tr>'

    # EDIT TABLE    
    edit_table_data = []
    for row_data in rows_data:
        id, ref, eng, heb1, heb2, heb3, heb4, heb5, heb6 = row_data
        # Create a list to store the search conditions
        
        search_conditions = []
        parameters = []
        # Check each hebrew field and build the search conditions and parameters accordingly
        if heb1:
            search_conditions.append("Heb1 LIKE ?")
            parameters.append(f'%{heb1}%')
        else:
            search_conditions.append("Heb1 IS NULL")

        if heb2:
            search_conditions.append("Heb2 LIKE ?")
            parameters.append(f'%{heb2}%')
        else:
            search_conditions.append("Heb2 IS NULL")

        if heb3:
            search_conditions.append("Heb3 LIKE ?")
            parameters.append(f'%{heb3}%')
        else:
            search_conditions.append("Heb3 IS NULL")

        if heb4:
            search_conditions.append("Heb4 LIKE ?")
            parameters.append(f'%{heb4}%')
        else:
            search_conditions.append("Heb4 IS NULL")

        if heb5:
            search_conditions.append("Heb5 LIKE ?")
            parameters.append(f'%{heb5}%')
        else:
            search_conditions.append("Heb5 IS NULL")

        if heb6:
            search_conditions.append("Heb6 LIKE ?")
            parameters.append(f'%{heb6}%')
        else:
            search_conditions.append("Heb6 IS NULL")

        # Join the search conditions using 'AND' and build the final query
        where_clause = " AND ".join(search_conditions)
        query = f"""
            SELECT COUNT(*) FROM hebrewdata
            WHERE {where_clause};
        """

        cursor.execute(query, parameters)
        search_count = cursor.fetchone()[0]


        combined_hebrew = f"{heb1 or ''} {heb2 or ''} {heb3 or ''} {heb4 or ''} {heb5 or ''} {heb6 or ''}"

        edit_table_data.append((id, ref, eng, combined_hebrew, search_count))


    cursor.close()
    connection.close()


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
    
    # Pass the fetched data and context to the template for rendering
    context = {'verse': verse, 'reference': rbt_heb_ref, 'english_row': english_row, 'hebrew_row': hebrew_row, 'edit_table_data': edit_table_data}
    return render(request, 'hebrew.html', context)

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