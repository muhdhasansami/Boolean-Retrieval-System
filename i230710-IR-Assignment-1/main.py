"""
Boolean Information Retrieval System
Implements Inverted Index + Positional Index with Boolean & Proximity Query support.
Uses NLTK Porter Stemmer.
"""

import re          # FOR PROCESSING REGULAR EXPRESSIONS (EG. TO EXTRACT DOC ID FROM FILENAME)
import json        # FOR CREATING JSON BASED INDEXES ON DISK
import os          # FOR FILE HANDLING 
import nltk        # FOR PORTER STEMMER
from nltk.stem import PorterStemmer

# GLOBAL VARIABLES - FILE NAMES
FOLDER_NAME   = "Trump Speechs"
STOPWORDS_FILE = "Stopword-List.txt"
INV_INDEX_FILE = "inverted_index.json"
POS_INDEX_FILE = "positional_index.json"

# INITIALISE STEMMER
stemmer = PorterStemmer()


# HELPER FUNCTION: load stop words
def loadStopWords(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return set(line.strip().lower() for line in f if line.strip())
    

# PREPROCESSING
def preprocess(text, stopwords):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text) # replace anything thats NOT a word or a space
    
    words = text.split()
    tokens = []
    
    for word in words:
        if word not in stopwords:       # remove stop words
            if len(word) > 1:
                word = stemmer.stem(word)
                tokens.append(word)
    
    return tokens


# HELPER FUNCTION THAT EXTRACTS DOCUMENT ID FROM FILE NAME
def extract_docID(filename):
    match = re.search(r'\d+', filename)
    if match:
        return int(match.group())
    else:
        return 0


# BUILDING INDEX
def build_indexes(FOLDER_NAME, stopwords):
    inverted_index   = {}
    positional_index = {}
    doc_map          = {}
    doc_id = 0


    files = os.listdir(FOLDER_NAME)
    files = sorted(files, key=extract_docID)

    for fname in files:
        if not fname.endswith('.txt'):
            continue
        with open(f"{FOLDER_NAME}/{fname}", 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        doc_map[doc_id] = fname
        tokens = preprocess(text, stopwords)

        # Build inverted index from preprocessed tokens
        for term in set(tokens):
            if term not in inverted_index:
                inverted_index[term] = set()
            inverted_index[term].add(doc_id)

        
        text_clean = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        raw_tokens = text_clean.split()
        for raw_pos, word in enumerate(raw_tokens):
            if len(word) <= 1 or word in stopwords or word.isdigit():
                continue  # skip but raw_pos still advances (numbers/stopwords count toward distance)

            term = stemmer.stem(word)

            if term not in positional_index:
                positional_index[term] = {}
                
            if doc_id not in positional_index[term]:
                positional_index[term][doc_id] = []
            positional_index[term][doc_id].append(raw_pos)

        doc_id += 1

    return inverted_index, positional_index, doc_map


# SAVE INDEXES TO DISK IN JSON FORMAT
def save_indexes(inverted_index, positional_index, doc_map):
    inv_serial = {term: sorted(list(docs)) for term, docs in inverted_index.items()}
    with open(INV_INDEX_FILE, 'w') as f:
        json.dump({"doc_map": {str(k): v for k, v in doc_map.items()},
                   "index": inv_serial}, f)

    pos_serial = {
        term: {str(doc_id): positions for doc_id, positions in doc_dict.items()}
        for term, doc_dict in positional_index.items()
    }
    with open(POS_INDEX_FILE, 'w') as f:
        json.dump(pos_serial, f)

    print(f"[INFO] Saved inverted index  -> {INV_INDEX_FILE}")
    print(f"[INFO] Saved positional index -> {POS_INDEX_FILE}")


# LOAD INDEXES FROM DISK
def load_indexes():
    with open(INV_INDEX_FILE, 'r') as f:
        inv_data = json.load(f)
    doc_map = {int(k): v for k, v in inv_data["doc_map"].items()}
    inverted_index = {term: set(docs) for term, docs in inv_data["index"].items()}

    with open(POS_INDEX_FILE, 'r') as f:
        pos_data = json.load(f)
    positional_index = {
        term: {int(doc_id): positions for doc_id, positions in doc_dict.items()}
        for term, doc_dict in pos_data.items()
    }

    print("[INFO] Loaded indexes from disk.")
    return inverted_index, positional_index, doc_map


# HELPER FUNCTION: GET POSTINGS OF A GIVEN TERM
def get_postings(term, inverted_index, stopwords):
    stemmed = stemmer.stem(term.lower())
    return inverted_index.get(stemmed, set())


# HELPER FUNCTION: RETURN ALL DOC IDS
def all_doc_ids(doc_map):
    return set(doc_map.keys())


# DETECT QUERY TYPE - THIS FUNCTION DECIDES WHICH OF THE NEXT 2 CORE FUNCTIONS TO USE
def process_query(query_str, inverted_index, positional_index, doc_map, stopwords):
    query_str = query_str.strip()
    if '/' in query_str:    # proximity query
        return evaluate_proximity_query(query_str, positional_index, doc_map, stopwords)
    else:                   # normal boolean query
        return evaluate_boolean_query(query_str, inverted_index, doc_map, stopwords)


# CORE FUNCTION 1: PROCESS BOOLEAN QUERY
def evaluate_boolean_query(query_str, inverted_index, doc_map, stopwords):
    ALL = all_doc_ids(doc_map)

    def resolve_tokens(tokens):
        """Evaluate a flat list of tokens (no parentheses) into a result set."""
        if len(tokens) == 1:
            return get_postings(tokens[0], inverted_index, stopwords)
        if len(tokens) == 2 and tokens[0].upper() == 'NOT':
            return ALL - get_postings(tokens[1], inverted_index, stopwords)

        operands, operators, i = [], [], 0
        while i < len(tokens):
            tok = tokens[i].upper()
            if tok in ('AND', 'OR'):
                operators.append(tok)
                i += 1
            elif tok == 'NOT':
                if i + 1 < len(tokens):
                    operands.append(('NOT', tokens[i + 1]))
                    i += 2
                else:
                    i += 1
            else:
                operands.append(('TERM', tokens[i]))
                i += 1

        def resolve(op):
            kind, val = op
            s = get_postings(val, inverted_index, stopwords)
            return (ALL - s) if kind == 'NOT' else s

        result = resolve(operands[0])
        for idx, op_str in enumerate(operators):
            if idx + 1 >= len(operands):
                break
            right = resolve(operands[idx + 1])
            result = result & right if op_str == 'AND' else result | right
        return result

    # ── Handle one level of parentheses
    import re as _re
    raw_tokens = _re.findall(r'\(|\)|[^\s()]+', query_str.strip())

    # Find the parenthesised sub-expression and evaluate it first
    if '(' in raw_tokens:
        open_i = raw_tokens.index('(')
        try:
            close_i = raw_tokens.index(')', open_i)
        except ValueError:
            raise ValueError("Mismatched parentheses in query.")

        sub_tokens = raw_tokens[open_i + 1:close_i]
        sub_result = resolve_tokens(sub_tokens)

        outer_tokens = raw_tokens[:open_i] + raw_tokens[close_i + 1:]

        # Evaluate outer with sub_result as a pre-resolved operand
        outer_operands, outer_operators, i = [], [], 0
        while i < len(outer_tokens):
            tok = outer_tokens[i].upper()
            if tok in ('AND', 'OR'):
                outer_operators.append(tok)
                i += 1
            elif tok == 'NOT':
                if i + 1 < len(outer_tokens):
                    outer_operands.append(('NOT', outer_tokens[i + 1]))
                    i += 2
                else:
                    i += 1
            else:
                outer_operands.append(('TERM', outer_tokens[i]))
                i += 1

        def resolve_outer(op):
            kind, val = op
            s = get_postings(val, inverted_index, stopwords)
            return (ALL - s) if kind == 'NOT' else s

        
        operands_before = sum(
            1 for t in raw_tokens[:open_i]
            if t.upper() not in ('AND', 'OR', 'NOT')
        )

        resolved_outer = []
        for op in outer_operands:
            resolved_outer.append(resolve_outer(op))

        # Insert sub_result at the right position
        resolved_outer.insert(operands_before, sub_result)

        if not resolved_outer:
            return sub_result

        result = resolved_outer[0]
        for idx, op_str in enumerate(outer_operators):
            if idx + 1 >= len(resolved_outer):
                break
            right = resolved_outer[idx + 1]
            result = result & right if op_str == 'AND' else result | right
        return result

    # No parentheses — plain evaluation
    return resolve_tokens(raw_tokens)


# CORE FUNCTION 2: PROCESS PROXIMITY QUERY
def evaluate_proximity_query(query_str, positional_index, doc_map, stopwords):
    parts = query_str.split('/')
    if len(parts) != 2:
        raise ValueError("Proximity query format: t1 t2 / k")

    terms = parts[0].strip().split()
    if len(terms) != 2:
        raise ValueError("Proximity query needs exactly 2 terms before '/'")

    try:
        k = int(parts[1].strip())
    except ValueError:
        raise ValueError("k must be an integer.")

    t1 = stemmer.stem(terms[0].lower())
    t2 = stemmer.stem(terms[1].lower())

    postings1 = positional_index.get(t1, {})
    postings2 = positional_index.get(t2, {})
    result = set()

    for doc_id in set(postings1.keys()) & set(postings2.keys()):
        pos1 = postings1[doc_id]
        pos2 = postings2[doc_id]
        found = False

        for p1 in pos1:
            for p2 in pos2:
                if abs(p1 - p2) == k + 1:
                    found = True
                    break
            if found:
                break

        if found:
            result.add(doc_id)

    return result


# DISPLAY RESULT ON TERMINAL 
def display_result(query_str, result_ids, doc_map):
    print(f"\nQuery: {query_str}")
    if not result_ids:
        print("No matching documents found.")
        return
    print({str(doc_id) for doc_id in result_ids})
    print(f"({len(result_ids)} document(s) matched)")


# MAIN DRIVER FUNCTION (CLI OUTPUT)
def main():
    import sys
    stopwords = loadStopWords(STOPWORDS_FILE)

    rebuild = '--rebuild' in sys.argv

    if not rebuild:
        try:
            inverted_index, positional_index, doc_map = load_indexes()
        except FileNotFoundError:
            rebuild = True

    if rebuild:
        print("[INFO] Building indexes from scratch ...")
        inverted_index, positional_index, doc_map = build_indexes(FOLDER_NAME, stopwords)
        save_indexes(inverted_index, positional_index, doc_map)
        print(f"[INFO] Indexed {len(doc_map)} documents, {len(inverted_index)} unique terms.")

    print("=================================================================")
    print("               Boolean IR System — Trump Speeches")
    print("=================================================================")
    print("Query formats:")
    print("  t1 AND t2 AND t3")
    print("  t1 OR  t2")
    print("  NOT t1")
    print("  t1 AND NOT t2")
    print("  t1 t2 / k (proximity: t1 and t2 within k words)")
    print("  Type 'exit' to quit.\n")

    while True:
        try:
            query = input("Enter query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Exiting program...")
            break

        if query.lower() in ('exit', 'quit', 'q'):
            print("Exiting program...")
            break
        if not query:
            continue

        result = process_query(query, inverted_index, positional_index, doc_map, stopwords)
        display_result(query, result, doc_map)


if __name__ == "__main__":
    main()
