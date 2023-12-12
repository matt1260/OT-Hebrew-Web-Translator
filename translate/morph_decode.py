def decode_morpheme(piece, lang):
    decoded = []
    
    # Initialize dictionaries
    noun_types = {
        'c': 'Common',
        'g': 'Gentilic',
        'p': 'Name',
    }

    adjective_types = {
        'a': 'Adj',
        'c': 'cardinal number',
        'g': 'Gentilic',
        'o': 'ordinal number',
    }

    pronoun_types = {
        'd': 'demonstrative',
        'f': 'indefinite',
        'i': 'Interrog',
        'p': 'personal',
        'r': 'relative',
    }

    preposition_types = {
        'd': 'definite article',
    }

    suffix_types = {
        'd': 'directional he',
        'h': 'paragogic he',
        'n': 'paragogic nun',
        'p': 'pronominal',
    }
    
    particle_types = {
        'a': 'affirmation',
        'd': 'Art',
        'e': 'exhortation',
        'i': 'Interrog',
        'j': 'interjection',
        'm': 'demonstrative',
        'n': 'Negative',
        'o': 'DirObjM',
        'r': 'relative',
    }

    gender = {
        'b': 'neut', # noun
        'c': 'common', # verb
        'f': 'fem',
        'm': 'masc',
    }
    
    person = {
        '1': '1',
        '2': '2',
        '3': '3',
    }

    number = {
        'd': 'dual',
        'p': 'pl',
        's': 'sing',
    }

    state = {
        'a': 'abs',
        'c': 'const',
        'd': 'deter',
    }

    verb_stems_hebrew = {
    'q': 'Qal',
    'N': 'Nifal', # Niphal
    'p': 'Piel',
    'P': 'Pual',
    'h': 'Hifil', # Hiphil
    'H': 'Hofal',
    't': 'Hitpael',
    'o': 'Polel',
    'O': 'Polal',
    'r': 'Hitpolel',
    'm': 'Poel',
    'M': 'Poal',
    'k': 'Palel',
    'K': 'Pulal',
    'Q': 'Qal Passive',
    'l': 'Pilpel',
    'L': 'Polpal',
    'f': 'Hitpalpel',
    'D': 'Nitpael',
    'j': 'Pealal',
    'i': 'Pilel',
    'u': 'Hotpaal',
    'c': 'Tiphil',
    'v': 'Hishtaphel',
    'w': 'Nitpalel',
    'y': 'Nitpoel',
    'z': 'Hitpoel',
    }

    verb_conjugation_types_hebrew = {
        'p': 'Perf', # (qatal)
        'q': 'ConsecPerf ', # (weqatal)
        'i': 'Imperf',  # (yiqtol)
        'w': 'ConsecImperf', #(wayyiqtol)
        'h': 'cohort',
        'j': 'Imperf.Jus',
        'v': 'Imp',
        'r': 'Prtcpl active',
        's': 'Prtcpl passive',
        'a': 'infinitive absolute',
        'c': 'infinitive construct',
    }

    verb_stems_aramaic = {
        'q': 'peal',
        'Q': 'peil',
        'u': 'hithpeel',
        'p': 'pael',
        'P': 'ithpaal',
        'M': 'hithpaal',
        'a': 'aphel',
        'h': 'haphel',
        's': 'saphel',
        'e': 'shaphel',
        'H': 'hophal',
        'i': 'ithpeel',
        't': 'hishtaphel',
        'v': 'ishtaphel',
        'w': 'hithaphel',
        'o': 'polel',
        'z': 'ithpoel',
        'r': 'hithpolel',
        'f': 'hithpalpel',
        'b': 'hephal',
        'c': 'tiphel',
        'm': 'poel',
        'l': 'palpel',
        'L': 'ithpalpel',
        'O': 'ithpolel',
        'G': 'ittaphal',
    }

    verb_conjugation_types_aramaic = {
        'p': 'perfect (qatal)',
        'q': 'sequential perfect (weqatal)',
        'i': 'imperfect (yiqtol)',
        'w': 'sequential imperfect (wayyiqtol)',
        'h': 'cohortative',
        'j': 'jussive',
        'v': 'imperative',
        'r': 'participle active',
        's': 'participle passive',
        'a': 'infinitive absolute',
        'c': 'infinitive construct',
    }


    piece_type = piece[0]
    if piece[0] == 'H':
        piece_type = piece[1]
    
    if lang == 'H' and piece[0] == 'A':
        piece_type = 'A'

    elif piece[0] == 'A':
        piece_type = piece[1]

    if piece == 'HD' or piece == 'D':
        decoded.append('Adv')

    elif piece_type in 'Cc':
        decoded.append('Conj-w')
    
    elif piece_type in 'HL':
        decoded.append('Prep-l')
    
    elif piece_type in 'HM':
        decoded.append('Prep-m')

    elif piece_type in 'HK':
        decoded.append('Prep-k')

    elif piece_type in 'HB':
        decoded.append('Prep-b')

    elif piece_type == 'N':
        decoded.append('noun')
    

        if piece == 'HNpm':
            decoded.append(noun_types.get(piece[2], ''))
            decoded.append(gender[piece[3]])

        elif piece == 'HNpl':
            decoded.append(noun_types.get(piece[2], ''))
            decoded.append('place')

        elif piece == 'HNpt':
            decoded.append(noun_types.get(piece[2], ''))
            decoded.append('YHWH')
        
        elif piece[0] == 'H' or piece[0] == 'A':
            decoded.append(noun_types.get(piece[2], ''))
            
            for letter in piece[3:5]: 
                if letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])

            for letter in piece[5:]:
                if letter in state:
                    decoded.append(state[letter])
        
        else:
            decoded.append(noun_types.get(piece[1], ''))
             
            for letter in piece[2:4]: 
                if letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])

            for letter in piece[4:]:
                if letter in state:
                    decoded.append(state[letter])

    elif piece_type == 'A':
        decoded.append('adjective')
        
        if lang == 'H' and piece_type[0] == 'A':
            if piece[1] != 'a':
                decoded.append(adjective_types.get(piece[1], ''))

            for letter in piece[2:4]:
                if letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])
            for letter in piece[4:]:
                    if letter in number:
                        decoded.append(number[letter])
                    elif letter in state:
                        decoded.append(state[letter])

        elif piece[0] == 'H' or piece[0] == 'A':
            decoded.append(adjective_types.get(piece[2], ''))
            for letter in piece[3:4]:
                if letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])
            for letter in piece[5:]:
                    decoded.append(state[letter])
        else:
            decoded.append(adjective_types.get(piece[1], ''))
            for letter in piece[2:3]:
                if letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])
            for letter in piece[4:]:
                    decoded.append(state[letter])

    elif piece_type == 'P':
        decoded.append('pronoun')
        decoded.append(pronoun_types.get(piece[1], ''))
        for letter in piece[2:]:
            if letter in gender:
                decoded.append(gender[letter])
            elif letter in number:
                decoded.append(number[letter])
            elif letter in state:
                decoded.append(state[letter])

    elif piece_type == 'S':
        decoded.append('suffix')
        decoded.append(suffix_types.get(piece[1], ''))
        for letter in piece[3:]:
            if letter in person:
                decoded.append(person[letter])
            elif letter in gender:
                decoded.append(gender[letter])
            elif letter in number:
                decoded.append(number[letter])

    elif piece_type == 'R':
        decoded.append('Prep')

    elif piece_type == 'T':
        
        if piece[0] == 'H' or piece[0] == 'A':
            for letter in piece[2:]:
                if letter in particle_types:
                    decoded.append(particle_types[letter])
                elif letter == 'c':
                    decoded.append('Conj')

        else: 
            particle_code = piece[1] # if it is the second piece, i.e Tc
            if particle_code in particle_types:
                decoded.append(particle_types[particle_code])
            elif particle_code == 'c':
                decoded.append('Conj')

    elif piece_type == 'V':
        decoded.append('verb')
        if lang == 'H': # Hebrew Verbs
            
            if len(piece) == 7:
                decoded.append(verb_stems_hebrew.get(piece[2], ''))
                decoded.append(verb_conjugation_types_hebrew.get(piece[3], ''))
                for letter in piece[3:]:
                    if letter in number:
                        decoded.append(number[letter])
                    elif letter in person:
                        decoded.append(person[letter])
                    elif letter in gender:
                        decoded.append(gender[letter])
                    elif letter in state:
                        decoded.append(state[letter])

            elif len(piece) == 6:
                decoded.append(verb_stems_hebrew.get(piece[1], ''))
                decoded.append(verb_conjugation_types_hebrew.get(piece[2], ''))
                for letter in piece[2:]:
                    if letter in number:
                        decoded.append(number[letter])
                    elif letter in person:
                        decoded.append(person[letter])
                    elif letter in gender:
                        decoded.append(gender[letter])
            
            elif len(piece) == 5:
                
                decoded.append(verb_stems_hebrew.get(piece[2], ''))
                for letter in piece[3:4]:
                    if letter in person:
                        decoded.append(person[letter])
                    elif letter in gender:
                        decoded.append(gender[letter])
                for letter in piece[4:]:
                    if letter in number:
                        decoded.append(number[letter])
                    if letter in state:
                        decoded.append(state[letter])

            elif len(piece) == 4:
                
                decoded.append(verb_stems_hebrew.get(piece[1], ''))
                for letter in piece[2:3]:
                    if letter in person:
                        decoded.append(person[letter])
                    elif letter in gender:
                        decoded.append(gender[letter])
                for letter in piece[3:]:
                    if letter in number:
                        decoded.append(number[letter])
                    if letter in state:
                        decoded.append(state[letter])
            else:
            #     decoded.append(verb_conjugation_types_hebrew.get(piece[2], ''))

                for letter in piece[4:]:
                    if letter in person:
                        decoded.append(person[letter])
                    elif letter in gender:
                        decoded.append(gender[letter])
                    elif letter in number:
                        decoded.append(number[letter])


        elif lang == 'A': # Aramaic Verbs
            decoded.append(verb_stems_aramaic.get(piece[2], ''))
            if len(piece) == 6:
                decoded.append(verb_conjugation_types_aramaic.get(piece[3], ''))
            else:
                decoded.append(verb_conjugation_types_aramaic.get(piece[2], ''))
            for letter in piece[4:]:
                if letter in person:
                    decoded.append(person[letter])
                elif letter in gender:
                    decoded.append(gender[letter])
                elif letter in number:
                    decoded.append(number[letter])
    
    return ' | '.join(decoded)

def decode_code(code):
    
    if code and '/' in code:
        pieces = code.split('/')
        decoded_morphemes = [decode_morpheme(piece, 'H') if code[0] == 'H' else decode_morpheme(piece, 'A') for piece in pieces]
        return ' - '.join(decoded_morphemes)

    else:
        lang = 'H' if code[0] == 'H' else 'A'
        return decode_morpheme(code, lang)

