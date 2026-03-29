import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QScrollArea, QFrame, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from main import (
    loadStopWords, load_indexes, build_indexes, save_indexes,
    process_query, STOPWORDS_FILE, FOLDER_NAME
)


class IndexWorker(QThread):
    done = pyqtSignal(object, object, object)
    error = pyqtSignal(str)

    def run(self):
        try:
            stopwords = loadStopWords(STOPWORDS_FILE)
            try:
                inv, pos, doc_map = load_indexes()
            except FileNotFoundError:
                inv, pos, doc_map = build_indexes(FOLDER_NAME, stopwords)
                save_indexes(inv, pos, doc_map)
            self.done.emit(inv, pos, doc_map)
        except Exception as e:
            self.error.emit(str(e))


class DocCard(QFrame):
    def __init__(self, filename, doc_id):
        super().__init__()
        self.setFixedSize(200, 70)
        self.setStyleSheet("""
            QFrame { background: white; border: 1px solid #e0e0e0; border-radius: 6px; }
            QFrame:hover { border: 1px solid #aaa; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        row = QHBoxLayout()
        row.setSpacing(8)

        icon = QLabel("🗎")
        icon.setStyleSheet("font-size: 40px; border: none;")
        icon.setFixedWidth(44)
        row.addWidget(icon, alignment=Qt.AlignVCenter)

        name = QLabel(filename)
        name.setFont(QFont("Segoe UI", 9, QFont.Bold))
        name.setStyleSheet("color: #1a1a1a; border: none;")
        name.setWordWrap(True)
        row.addWidget(name, alignment=Qt.AlignVCenter)

        layout.addLayout(row)


class IRWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Boolean IR System — Trump Speeches")
        self.setFixedSize(950, 900)
        self.setStyleSheet("QMainWindow, QWidget { background: #fafafa; }")

        self.inv_index = self.pos_index = self.doc_map = None
        self.stopwords = loadStopWords(STOPWORDS_FILE)

        root = QVBoxLayout()
        root.setContentsMargins(30, 30, 30, 20)
        root.setSpacing(16)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Enter boolean query (e.g. 'america' AND 'great' NOT 'china')")
        self.search.setFixedHeight(52)
        self.search.setStyleSheet("""
            QLineEdit {
                background: #f5f5f5; border: 1.5px solid #ccc;
                border-radius: 6px; padding: 0 16px;
                font-size: 16px; color: #222;
            }
            QLineEdit:focus { border-color: #888; background: white; }
        """)
        self.search.returnPressed.connect(self.run_query)
        search_row.addWidget(self.search)

        btn = QPushButton("Search")
        btn.setFixedSize(120, 52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background: #1a73e8; color: white; border: none; border-radius: 6px; font-size: 18px; font-weight: bold; }
            QPushButton:hover { background: #1558b0; }
            QPushButton:pressed { background: #0f3f80; }
        """)
        btn.clicked.connect(self.run_query)
        search_row.addWidget(btn)
        root.addLayout(search_row)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #d32f2f; font-size: 13px; padding: 2px 4px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        root.addWidget(self.error_label)

        # Results header
        header_row = QHBoxLayout()
        self.results_label = QLabel("All Documents")
        self.results_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.match_count = QLabel("")
        self.match_count.setStyleSheet("color: #888; font-size: 13px;")
        header_row.addWidget(self.results_label)
        header_row.addWidget(self.match_count)
        header_row.addStretch()
        root.addLayout(header_row)

        # Cards grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(14)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.grid_widget)
        root.addWidget(scroll)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self.worker = IndexWorker()
        self.worker.done.connect(self.on_index_ready)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def show_error(self, msg):
        self.error_label.setText(f"⚠  {msg}")
        self.error_label.show()

    def clear_error(self):
        self.error_label.setText("")
        self.error_label.hide()

    def on_index_ready(self, inv, pos, doc_map):
        self.inv_index, self.pos_index, self.doc_map = inv, pos, doc_map
        self.populate_grid(sorted(doc_map.keys()), "All Documents")

    def run_query(self):
        if not self.inv_index:
            self.show_error("Index not ready yet, please wait.")
            return
        self.clear_error()
        query = self.search.text().strip()
        if not query:
            self.populate_grid(sorted(self.doc_map.keys()), "All Documents")
            return
        try:
            result_ids = process_query(query, self.inv_index, self.pos_index, self.doc_map, self.stopwords)
            self.populate_grid(sorted(result_ids), "Search Results")
        except Exception as e:
            self.show_error(str(e))

    def populate_grid(self, doc_ids, label):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.results_label.setText(label)
        self.match_count.setText(f"  ({len(doc_ids)} matches)")
        for i, doc_id in enumerate(doc_ids):
            self.grid.addWidget(DocCard(self.doc_map.get(doc_id, f"doc_{doc_id}"), doc_id), i // 4, i % 4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = IRWindow()
    win.show()
    sys.exit(app.exec_())
    # Initial index loading
    def on_index_ready(self, inv, pos, doc_map):
        self.inv_index = inv
        self.pos_index = pos
        self.doc_map = doc_map
        self.show_all_docs()

    def show_all_docs(self):
        if self.doc_map:
            self.populate_grid(sorted(self.doc_map.keys()), label="All Documents")

    # process query
    def run_query(self):
        if not self.inv_index:
            self.show_error("Index not ready yet, please wait.")
            return
        self.clear_error()

        query = self.search.text().strip()
        if not query:
            self.show_all_docs()
            return
        
        try:
            result_ids = process_query(query, self.inv_index, self.pos_index, self.doc_map, self.stopwords)
            self.populate_grid(sorted(result_ids), label="Index Search Results")
        except Exception as e:
            self.show_error(str(e))

    def populate_grid(self, doc_ids, label="Index Search Results"):
        # Clear existing cards
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.results_label.setText(label)
        self.match_count.setText(f"  ({len(doc_ids)} matches)")

        # populate cards with filenames
        cols = 4
        for i, doc_id in enumerate(doc_ids):
            fname = self.doc_map.get(doc_id, f"doc_{doc_id}")
            card = DocCard(fname, doc_id)
            self.grid.addWidget(card, i // cols, i % cols)


# MAIN FUNCTION
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = IRWindow()
    win.show()
    sys.exit(app.exec_())
