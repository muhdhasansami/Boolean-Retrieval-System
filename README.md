# Boolean IR System — Trump Speeches

A Python-based Information Retrieval system built on a corpus of 56 Trump speeches. Supports Boolean queries and proximity search using an inverted index and positional index, with both a CLI and a PyQt5 GUI.

---

## Features

- Boolean queries: `AND`, `OR`, `NOT`, with parentheses support
- Proximity queries: find two terms within `k` words of each other
- Inverted index for fast document lookup
- Positional index for proximity search
- Text preprocessing: lowercasing, punctuation removal, stopword filtering, Porter stemming
- Indexes are persisted to disk as JSON and reloaded on subsequent runs
- PyQt5 GUI with a card-based results view

---

## Project Structure

```
i230710-IR-Assignment-1/
├── Trump Speechs/          # 56 speech documents (speech_0.txt ... speech_55.txt)
├── main.py                 # Index building, query processing, CLI entry point
├── gui.py                  # PyQt5 GUI
├── inverted_index.json     # Persisted inverted index (auto-generated)
├── positional_index.json   # Persisted positional index (auto-generated)
├── Stopword-List.txt       # Stopword list used during preprocessing
└── requirements.txt        # Python dependencies
```

---

## Installation

```bash
pip install -r requirements.txt
```

You also need to have NLTK data available. If you get a missing resource error, run:

```python
import nltk
nltk.download('punkt')
```

---

## Usage

### CLI

```bash
# Run with cached indexes (builds on first run)
python main.py

# Force rebuild of indexes
python main.py --rebuild
```

### GUI

```bash
python gui.py
```

The GUI loads the index in a background thread and displays all documents as cards. Enter a query in the search bar and press Enter or click Search.

---

## Query Syntax

| Type | Example | Description |
|------|---------|-------------|
| AND | `economy AND jobs` | Documents containing both terms |
| OR | `immigration OR border` | Documents containing either term |
| NOT | `NOT tax` | Documents not containing the term |
| Combined | `economy AND NOT tax` | Chained boolean logic |
| Parentheses | `(economy OR jobs) AND america` | Grouped sub-expressions |
| Proximity | `economy jobs / 3` | Both terms within 3 words of each other |

---

## How It Works

**Preprocessing** — each document is lowercased, stripped of punctuation and numbers, filtered for stopwords, and stemmed with the NLTK Porter Stemmer.

**Inverted Index** — maps each stemmed term to the set of document IDs it appears in. Used for all Boolean queries.

**Positional Index** — maps each stemmed term to a list of raw token positions per document. Used for proximity queries.

**Proximity matching** — two terms match in a document if there exist positions `p1` and `p2` such that `|p1 - p2| == k + 1`.

**Index persistence** — both indexes are serialized to `inverted_index.json` and `positional_index.json` after the first build, and loaded from disk on subsequent runs.

---

## Dependencies

| Package | Version |
|---------|---------|
| nltk | 3.9.4 |
| PyQt5 | 5.15.11 |
