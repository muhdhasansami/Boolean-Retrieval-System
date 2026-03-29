Boolean Retrieval System with Positional Indexing

A Python-based Information Retrieval (IR) system built on a collection of speeches by Donald Trump. This project demonstrates how search engines process and retrieve relevant documents using Boolean logic and positional indexing.

🚀 Features
🔍 Boolean Queries: AND, OR, NOT
📏 Proximity Queries (e.g., words within k distance)
🧠 Inverted Index for fast lookup
📍 Positional Index for accurate proximity search
🧹 Text Preprocessing:
Lowercasing
Punctuation & number removal
Stopword removal
Stemming
🏗️ Project Structure
.
├── data/                  # Folder containing speech documents
├── main.py                # Main program (query processing)
├── index.py               # Index creation (inverted + positional)
├── utils.py               # Preprocessing functions
├── README.md
⚙️ How It Works
1. Preprocessing
Text is cleaned and tokenized
Stopwords are removed
Words are stemmed
2. Indexing
Inverted Index → maps terms to documents
Positional Index → maps terms to document positions

Example:

"run": {
    1: [3, 10],
    2: [5]
}
🔍 Query Types
✅ Boolean Queries
economy AND jobs
immigration OR border
tax NOT increase
📏 Proximity Queries
"economy jobs" /3

👉 Finds words within distance k = 3
