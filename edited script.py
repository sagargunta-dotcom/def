import pandas as pd
import re
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog  # FIX #12: added filedialog
from tkinter.font import Font
import threading

# Compound word mappings
COMPOUND_WORD_MAPPINGS = {
    'barcode scanner': ['bar code scanner', 'barcode scanner', 'bar-code scanner'],
    'barcode': ['bar code', 'barcode', 'bar-code'],
    'toolkit': ['tool kit', 'toolkit', 'tool-kit'],
    'airbrush': ['air brush', 'airbrush', 'air-brush'],
    'database': ['data base', 'database', 'data-base'],
    'workstation': ['work station', 'workstation', 'work-station'],
    'smartphone': ['smart phone', 'smartphone', 'smart-phone'],
    'worksheet': ['work sheet', 'worksheet', 'work-sheet'],
    'whiteboard': ['white board', 'whiteboard', 'white-board'],
    'hardcover': ['hard cover', 'hardcover', 'hard-cover'],
    'wallpaper': ['wall paper', 'wallpaper', 'wall-paper'],
    'headphone': ['head phone', 'headphone', 'head-phone'],
    'keyboard': ['key board', 'keyboard', 'key-board'],
    'bookshelf': ['book shelf', 'bookshelf', 'book-shelf'],
    'tabletop': ['table top', 'tabletop', 'table-top'],
    'handheld': ['hand held', 'handheld', 'hand-held'],
    'touchscreen': ['touch screen', 'touchscreen', 'touch-screen'],
    'backpack': ['back pack', 'backpack', 'back-pack'],
    'flashlight': ['flash light', 'flashlight', 'flash-light'],
    'thumbtack': ['thumb tack', 'thumbtack', 'thumb-tack'],
    'pushpin': ['push pin', 'pushpin', 'push-pin'],
    'bodychain': ['body chain', 'bodychain', 'body-chain'],
    'flowmeter': ['flow meter', 'flowmeter', 'flow-meter']
}

# FIX #11: Removed COMPOUND_WORD_REVERSE — logic consolidated into get_word_variations()


def get_word_variations(search_term):
    """FIX #4: Exact match only — 'bar' no longer matches 'barcode' variants."""
    variations = set()
    search_term_lower = search_term.lower().strip()
    variations.add(search_term_lower)

    for normalized, variants in COMPOUND_WORD_MAPPINGS.items():
        all_forms = {normalized.lower()} | {v.lower() for v in variants}
        if search_term_lower in all_forms:
            variations.update(all_forms)
            break  # Each term belongs to at most one group

    return variations


class ProductSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Search Tool")

        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.attributes('-zoomed', True)  # Linux fallback

        # Configure fonts
        self.default_font = Font(family="Helvetica", size=10)
        self.bold_font = Font(family="Helvetica", size=10, weight="bold")

        # FIX #3: Track active search thread
        self._search_thread = None
        self._cancel_search = False

        # FIX #1: Stop init if databases fail to load
        if not self.load_databases():
            return

        self.create_widgets()

    # ------------------------------------------------------------------ #
    #  Database loading                                                    #
    # ------------------------------------------------------------------ #

    def load_databases(self):
        """FIX #1 & #12: Returns False on failure; file-picker fallback."""
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

        required_files = {
            'db1': 'Definition CSV.csv',
            'db2': 'with outt.csv',
            'db3': 'Cheat codes csv.csv',
        }

        try:
            for attr, filename in required_files.items():
                filepath = os.path.join(desktop_path, filename)

                # FIX #12: Fallback to file picker if not on Desktop
                if not os.path.exists(filepath):
                    filepath = filedialog.askopenfilename(
                        title=f"Select '{filename}'",
                        filetypes=[("CSV files", "*.csv")],
                    )
                    if not filepath:
                        messagebox.showerror("Error", f"'{filename}' is required.")
                        self.root.destroy()
                        return False

                setattr(self, attr, pd.read_csv(filepath))

            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load databases: {str(e)}")
            self.root.destroy()
            return False

    # ------------------------------------------------------------------ #
    #  GUI construction                                                    #
    # ------------------------------------------------------------------ #

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)

        # Main frame (left)
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Cheat codes frame (right)
        self.cheat_codes_frame = ttk.LabelFrame(self.root, text="Cheat Codes", padding="5")
        self.cheat_codes_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.cheat_codes_frame.grid_rowconfigure(0, weight=1)
        self.cheat_codes_frame.grid_columnconfigure(0, weight=1)

        self.create_search_frame()
        self.create_results_frame()
        self.create_cheat_codes_area()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=5)

    def create_search_frame(self):
        search_frame = ttk.LabelFrame(self.main_frame, text="Search", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Product:").grid(row=0, column=0, padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # FIX #10: Cap input length
        self.search_var.trace_add("write", self._limit_input_length)

        self.search_button = ttk.Button(search_frame, text="Search", command=self.start_search)
        self.search_button.grid(row=0, column=2, padx=5)

        # FIX #9: Cancel button
        self.cancel_button = ttk.Button(
            search_frame, text="Cancel", command=self.cancel_search, state=tk.DISABLED
        )
        self.cancel_button.grid(row=0, column=3, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(search_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)

        self.search_entry.bind('<Return>', lambda e: self.start_search())

    def create_results_frame(self):
        results_frame = ttk.LabelFrame(self.main_frame, text="Main Results", padding="5")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = scrolledtext.ScrolledText(
            results_frame, wrap=tk.WORD, width=80, height=20, font=self.default_font
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")

        self.results_text.tag_configure("bold", font=self.bold_font)
        self.results_text.tag_configure("heading", font=self.bold_font)
        self.results_text.tag_configure("exclusion_heading", font=self.bold_font, foreground="red")

    def create_cheat_codes_area(self):
        self.cheat_codes_text = scrolledtext.ScrolledText(
            self.cheat_codes_frame, wrap=tk.WORD, width=40, height=20, font=self.default_font
        )
        self.cheat_codes_text.grid(row=0, column=0, sticky="nsew")

        self.cheat_codes_text.tag_configure("bold", font=self.bold_font)
        self.cheat_codes_text.tag_configure("heading", font=self.bold_font)

    # ------------------------------------------------------------------ #
    #  Thread-safe GUI helpers (FIX #2)                                    #
    # ------------------------------------------------------------------ #

    def _set_status(self, text):
        """FIX #2: Thread-safe status update."""
        self.root.after(0, self.status_var.set, text)

    def _set_progress(self, value):
        """FIX #2: Thread-safe progress update."""
        self.root.after(0, self.progress_var.set, value)

    def _limit_input_length(self, *_args):
        """FIX #10: Enforce max 200 character input."""
        current = self.search_var.get()
        if len(current) > 200:
            self.search_var.set(current[:200])

    # ------------------------------------------------------------------ #
    #  Search control                                                      #
    # ------------------------------------------------------------------ #

    def start_search(self):
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term")
            return

        # FIX #3: Block if a search is already running
        if self._search_thread and self._search_thread.is_alive():
            messagebox.showinfo("Info", "A search is already in progress.")
            return

        self._cancel_search = False
        self.search_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.status_var.set("Searching...")
        self.progress_var.set(0)
        self.results_text.delete(1.0, tk.END)
        self.cheat_codes_text.delete(1.0, tk.END)

        self._search_thread = threading.Thread(
            target=self.perform_search, args=(search_term,), daemon=True
        )
        self._search_thread.start()

    def cancel_search(self):
        """FIX #9: Signal the worker thread to stop."""
        self._cancel_search = True
        self._set_status("Cancelling...")

    def perform_search(self, search_term):
        try:
            main_results = []
            exclusion_results = []
            cheat_code_results = []

            # --- Cheat Codes ---
            if self._cancel_search:
                self._on_search_cancelled()
                return
            self._set_status("Searching Cheat Codes...")
            self._set_progress(30)
            found3, results3 = self.search_database3(search_term)
            if found3:
                cheat_code_results.extend(results3)

            # --- Definition Database ---
            if self._cancel_search:
                self._on_search_cancelled()
                return
            self._set_status("Searching Definition Database...")
            self._set_progress(60)
            found1, results1, exclusions = self.search_database1(search_term)
            if found1:
                main_results.extend(results1)
            if exclusions:
                exclusion_results.extend(exclusions)

            # --- ITK Database ---
            if self._cancel_search:
                self._on_search_cancelled()
                return
            self._set_status("Searching ITK Database...")
            self._set_progress(90)
            found2, results2 = self.search_database2(search_term)
            if found2:
                main_results.extend(results2)

            self._set_progress(100)

            if self._cancel_search:
                self._on_search_cancelled()
                return

            self.root.after(
                0, self.display_results,
                main_results, exclusion_results, cheat_code_results, search_term,
            )

        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Search failed: {str(e)}")
            self.root.after(0, self.reset_search_state)

    def _on_search_cancelled(self):
        self._set_status("Search cancelled.")
        self._set_progress(0)
        self.root.after(0, self.reset_search_state)

    # ------------------------------------------------------------------ #
    #  Database search methods                                             #
    # ------------------------------------------------------------------ #

    def search_database1(self, search_term):
        """Search Definition Database with vectorized pre-filter (FIX #7)."""
        variations = get_word_variations(search_term)
        found_results = []
        exclusion_results = []

        # FIX #7: Pre-filter with vectorized str.contains before row iteration
        pattern = '|'.join(re.escape(v) for v in variations)
        definitions = self.db1['Definition'].astype(str)
        mask = definitions.str.contains(pattern, case=False, na=False)
        filtered = self.db1[mask]

        for _, row in filtered.iterrows():
            if self._cancel_search:
                break

            definition = str(row['Definition'])
            category = str(row['Category'])

            # Check inclusions
            for inclusion_text in re.findall(r'<inclusion>(.*?)</inclusion>', definition, re.DOTALL):
                inclusion_lower = inclusion_text.lower()
                if any(v in inclusion_lower for v in variations):
                    for sentence in (s.strip() for s in inclusion_text.split('.') if s.strip()):
                        if any(v in sentence.lower() for v in variations):
                            found_results.append({
                                'source': 'Definition',
                                'category': category,
                                'context': sentence,
                            })

            # Check exclusions
            for exclusion_text in re.findall(r'<exclusion>(.*?)</exclusion>', definition, re.DOTALL):
                exclusion_lower = exclusion_text.lower()
                if any(v in exclusion_lower for v in variations):
                    for sentence in (s.strip() for s in exclusion_text.split('.') if s.strip()):
                        if any(v in sentence.lower() for v in variations):
                            exclusion_results.append({
                                'source': 'Exclusion',
                                'category': category,
                                'context': sentence,
                            })

        return len(found_results) > 0, found_results, exclusion_results

    def search_database2(self, search_term):
        """Search ITK Database — FIX #5: Use column names, FIX #7: vectorized pre-filter."""
        variations = get_word_variations(search_term)
        found_results = []

        # FIX #5: Dynamic column names instead of positional iloc
        col_search = self.db2.columns[0]
        col_result = self.db2.columns[1]

        # FIX #7: Vectorized pre-filter
        pattern = '|'.join(re.escape(v) for v in variations)
        mask = self.db2[col_search].astype(str).str.contains(pattern, case=False, na=False)
        filtered = self.db2[mask]

        for _, row in filtered.iterrows():
            if self._cancel_search:
                break
            found_results.append({
                'source': 'ITK',
                'result': row[col_result],
                'matched_term': row[col_search],
            })

        return len(found_results) > 0, found_results

    def search_database3(self, search_term):
        """Search Cheat Codes — FIX #6: proper NaN handling, FIX #7: vectorized pre-filter."""
        variations = get_word_variations(search_term)
        found_results = []

        # FIX #7: Vectorized pre-filter
        pattern = '|'.join(re.escape(v) for v in variations)
        mask = self.db3['Scenario'].astype(str).str.contains(pattern, case=False, na=False)
        filtered = self.db3[mask]

        for _, row in filtered.iterrows():
            if self._cancel_search:
                break
            try:
                result = {
                    'source': 'Cheat Code',
                    'scenario': row['Scenario'],
                    'trex_id': str(row['TRexID to follow']),
                }

                # FIX #6: Use pd.notna() instead of string 'nan' comparison
                if pd.notna(row['Exclusion']):
                    result['exclusion'] = str(row['Exclusion'])

                found_results.append(result)

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        return len(found_results) > 0, found_results

    # ------------------------------------------------------------------ #
    #  Display methods                                                     #
    # ------------------------------------------------------------------ #

    def display_search_header(self, search_term, has_exclusions):
        self.results_text.insert(tk.END, f"Search Results for '{search_term}'\n", "heading")
        if has_exclusions:
            self.results_text.insert(tk.END, "   (Exclusions Found)\n", "exclusion_heading")
        self.results_text.insert(tk.END, "=" * 80 + "\n\n")

    def display_definition_results(self, results):
        self.results_text.insert(tk.END, "\nResults from Definition Database:\n", "heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, "TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['category']}\n")
            self.results_text.insert(tk.END, "Context: ", "bold")
            self.results_text.insert(tk.END, f"{result['context']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_itk_results(self, results):
        self.results_text.insert(tk.END, "\nResults from ITK Database:\n", "heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, "Matched term: ", "bold")
            self.results_text.insert(tk.END, f"{result['matched_term']}\n")
            self.results_text.insert(tk.END, "TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['result']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_exclusion_results(self, results):
        self.results_text.insert(tk.END, "\nExclusions:\n", "exclusion_heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, "TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['category']}\n")
            self.results_text.insert(tk.END, "Context: ", "bold")
            self.results_text.insert(tk.END, f"{result['context']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_results(self, main_results, exclusion_results, cheat_code_results, search_term):
        # --- Right panel: Cheat Codes ---
        if cheat_code_results:
            self.cheat_codes_text.insert(tk.END, f"Cheat Codes for '{search_term}'\n", "heading")
            self.cheat_codes_text.insert(tk.END, "=" * 40 + "\n\n")
            for result in cheat_code_results:
                self.cheat_codes_text.insert(tk.END, "Scenario: ", "bold")
                self.cheat_codes_text.insert(tk.END, f"{result['scenario']}\n")
                self.cheat_codes_text.insert(tk.END, "TRexID: ", "bold")
                self.cheat_codes_text.insert(tk.END, f"{result['trex_id']}\n")
                if 'exclusion' in result:
                    self.cheat_codes_text.insert(tk.END, "Exclusion: ", "bold")
                    self.cheat_codes_text.insert(tk.END, f"{result['exclusion']}\n")
                self.cheat_codes_text.insert(tk.END, "-" * 40 + "\n")

        # --- Left panel: Main results ---
        if not main_results and not exclusion_results:
            self.results_text.insert(tk.END, f"No main results found for '{search_term}'\n")
        else:
            self.display_search_header(search_term, bool(exclusion_results))

            variations = get_word_variations(search_term)
            if len(variations) > 1:
                self.results_text.insert(tk.END, "Included variations in search:\n")
                for var in sorted(variations):
                    if var != search_term.lower():
                        self.results_text.insert(tk.END, f"- {var}\n")
                self.results_text.insert(tk.END, "-" * 80 + "\n\n")

            definition_results = [r for r in main_results if r['source'] == 'Definition']
            itk_results = [r for r in main_results if r['source'] == 'ITK']

            if definition_results:
                self.display_definition_results(definition_results)
            if itk_results:
                self.display_itk_results(itk_results)
            if exclusion_results:
                self.display_exclusion_results(exclusion_results)

        total = len(main_results) + len(exclusion_results) + len(cheat_code_results)
        self.status_var.set(f"Found {total} total results")
        self.reset_search_state()

    def reset_search_state(self):
        self.search_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.search_entry.focus()


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductSearchGUI(root)
    root.mainloop()