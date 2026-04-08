import pandas as pd
import re
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
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

# Create reverse mapping
COMPOUND_WORD_REVERSE = {}
for normalized, variants in COMPOUND_WORD_MAPPINGS.items():
    for variant in variants:
        COMPOUND_WORD_REVERSE[variant.lower()] = normalized

class ProductSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Product Search Tool")
        self.root.state('zoomed')
        
        # Configure fonts
        self.default_font = Font(family="Helvetica", size=10)
        self.bold_font = Font(family="Helvetica", size=10, weight="bold")
        
        # Load databases
        self.load_databases()
        
        # Create GUI elements
        self.create_widgets()

    def load_databases(self):
        try:
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            
            # Load databases
            self.db1 = pd.read_csv(os.path.join(desktop_path, 'Definition CSV.csv'))
            self.db2 = pd.read_csv(os.path.join(desktop_path, 'with outt.csv'))
            self.db3 = pd.read_csv(os.path.join(desktop_path, 'Cheat codes csv.csv'))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load databases: {str(e)}")
            self.root.destroy()
            return

    def create_widgets(self):
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=3)  # Main content
        self.root.grid_columnconfigure(1, weight=1)  # Cheat codes

        # Main frame (left side)
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Cheat codes frame (right side)
        self.cheat_codes_frame = ttk.LabelFrame(self.root, text="Cheat Codes", padding="5")
        self.cheat_codes_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.cheat_codes_frame.grid_rowconfigure(0, weight=1)
        self.cheat_codes_frame.grid_columnconfigure(0, weight=1)

        # Create search frame
        self.create_search_frame()
        
        # Create results frame
        self.create_results_frame()
        
        # Create cheat codes text area
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
        
        self.search_button = ttk.Button(search_frame, text="Search", command=self.start_search)
        self.search_button.grid(row=0, column=2, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(search_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        self.search_entry.bind('<Return>', lambda e: self.start_search())

    def create_results_frame(self):
        results_frame = ttk.LabelFrame(self.main_frame, text="Main Results", padding="5")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=self.default_font
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure tags
        self.results_text.tag_configure("bold", font=self.bold_font)
        self.results_text.tag_configure("heading", font=self.bold_font)
        self.results_text.tag_configure("exclusion_heading", font=self.bold_font, foreground="red")

    def create_cheat_codes_area(self):
        self.cheat_codes_text = scrolledtext.ScrolledText(
            self.cheat_codes_frame,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=self.default_font
        )
        self.cheat_codes_text.grid(row=0, column=0, sticky="nsew")
        
        # Configure tags for cheat codes area
        self.cheat_codes_text.tag_configure("bold", font=self.bold_font)
        self.cheat_codes_text.tag_configure("heading", font=self.bold_font)

    def start_search(self):
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term")
            return
        
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set("Searching...")
        self.progress_var.set(0)
        self.results_text.delete(1.0, tk.END)
        self.cheat_codes_text.delete(1.0, tk.END)
        
        threading.Thread(target=self.perform_search, args=(search_term,), daemon=True).start()

    def perform_search(self, search_term):
        try:
            main_results = []
            exclusion_results = []
            cheat_code_results = []
            
            # Search Cheat Codes Database first
            self.status_var.set("Searching Cheat Codes...")
            self.progress_var.set(30)
            found3, results3 = self.search_database3(search_term)
            if found3:
                cheat_code_results.extend(results3)
            
            # Search Definition Database
            self.status_var.set("Searching Definition Database...")
            self.progress_var.set(60)
            found1, results1, exclusions = self.search_database1(search_term)
            if found1:
                main_results.extend(results1)
            if exclusions:
                exclusion_results.extend(exclusions)
            
            # Search ITK Database
            self.status_var.set("Searching ITK Database...")
            self.progress_var.set(90)
            found2, results2 = self.search_database2(search_term)
            if found2:
                main_results.extend(results2)
            
            self.progress_var.set(100)
            
            # Display results in GUI thread
            self.root.after(0, self.display_results, main_results, exclusion_results, 
                          cheat_code_results, search_term)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Search failed: {str(e)}")
            self.root.after(0, self.reset_search_state)

    def search_database1(self, search_term):
        variations = get_word_variations(search_term)
        found_results = []
        exclusion_results = []
        
        for _, row in self.db1.iterrows():
            definition = str(row['Definition'])
            category = str(row['Category'])
            
            # Check inclusions
            inclusion_matches = re.findall(r'<inclusion>(.*?)</inclusion>', definition, re.DOTALL)
            for inclusion_text in inclusion_matches:
                inclusion_text_lower = inclusion_text.lower()
                if any(variation in inclusion_text_lower for variation in variations):
                    sentences = [s.strip() for s in inclusion_text.split('.') if s.strip()]
                    for sentence in sentences:
                        if any(variation in sentence.lower() for variation in variations):
                            found_results.append({
                                'source': 'Definition',
                                'category': category,
                                'context': sentence.strip()
                            })
            
            # Check exclusions
            exclusion_matches = re.findall(r'<exclusion>(.*?)</exclusion>', definition, re.DOTALL)
            for exclusion_text in exclusion_matches:
                exclusion_text_lower = exclusion_text.lower()
                if any(variation in exclusion_text_lower for variation in variations):
                    sentences = [s.strip() for s in exclusion_text.split('.') if s.strip()]
                    for sentence in sentences:
                        if any(variation in sentence.lower() for variation in variations):
                            exclusion_results.append({
                                'source': 'Exclusion',
                                'category': category,
                                'context': sentence.strip()
                            })
        
        return len(found_results) > 0, found_results, exclusion_results

    def search_database2(self, search_term):
        variations = get_word_variations(search_term)
        found_results = []
        
        for _, row in self.db2.iterrows():
            first_col_value = str(row.iloc[0]).lower()
            if any(variation in first_col_value for variation in variations):
                found_results.append({
                    'source': 'ITK',
                    'result': row.iloc[1],
                    'matched_term': row.iloc[0]
                })
        
        return len(found_results) > 0, found_results

    def search_database3(self, search_term):
        variations = get_word_variations(search_term)
        found_results = []
        
        for _, row in self.db3.iterrows():
            try:
                scenario = str(row['Scenario']).lower()
                trex_id = str(row['TRexID to follow'])
                exclusion = str(row['Exclusion'])
                
                if any(variation in scenario for variation in variations):
                    result = {
                        'source': 'Cheat Code',
                        'scenario': row['Scenario'],
                        'trex_id': trex_id,
                    }
                    
                    if exclusion and exclusion.lower() != 'nan':
                        result['exclusion'] = exclusion
                    
                    found_results.append(result)
                    
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        return len(found_results) > 0, found_results

    def display_search_header(self, search_term, has_exclusions):
        header_text = f"Search Results for '{search_term}'\n"
        self.results_text.insert(tk.END, header_text, "heading")
        
        if has_exclusions:
            self.results_text.insert(tk.END, "   (Exclusions Found)\n", "exclusion_heading")
        
        self.results_text.insert(tk.END, "=" * 80 + "\n\n")

    def display_definition_results(self, results):
        self.results_text.insert(tk.END, "\nResults from Definition Database:\n", "heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, f"TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['category']}\n")
            self.results_text.insert(tk.END, f"Context: ", "bold")
            self.results_text.insert(tk.END, f"{result['context']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_itk_results(self, results):
        self.results_text.insert(tk.END, "\nResults from ITK Database:\n", "heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, f"Matched term: ", "bold")
            self.results_text.insert(tk.END, f"{result['matched_term']}\n")
            self.results_text.insert(tk.END, f"TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['result']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_exclusion_results(self, results):
        self.results_text.insert(tk.END, "\nExclusions:\n", "exclusion_heading")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        for result in results:
            self.results_text.insert(tk.END, f"TRexID: ", "bold")
            self.results_text.insert(tk.END, f"{result['category']}\n")
            self.results_text.insert(tk.END, f"Context: ", "bold")
            self.results_text.insert(tk.END, f"{result['context']}\n")
            self.results_text.insert(tk.END, "-" * 80 + "\n")

    def display_results(self, main_results, exclusion_results, cheat_code_results, search_term):
        # Display cheat codes in the right panel
        if cheat_code_results:
            self.cheat_codes_text.insert(tk.END, f"Cheat Codes for '{search_term}'\n", "heading")
            self.cheat_codes_text.insert(tk.END, "=" * 40 + "\n\n")
            for result in cheat_code_results:
                self.cheat_codes_text.insert(tk.END, f"Scenario: ", "bold")
                self.cheat_codes_text.insert(tk.END, f"{result['scenario']}\n")
                self.cheat_codes_text.insert(tk.END, f"TRexID: ", "bold")
                self.cheat_codes_text.insert(tk.END, f"{result['trex_id']}\n")
                if 'exclusion' in result and result['exclusion'].lower() != 'nan':
                    self.cheat_codes_text.insert(tk.END, f"Exclusion: ", "bold")
                    self.cheat_codes_text.insert(tk.END, f"{result['exclusion']}\n")
                self.cheat_codes_text.insert(tk.END, "-" * 40 + "\n")

        # Display main results
        if not main_results and not exclusion_results:
            self.results_text.insert(tk.END, f"No main results found for '{search_term}'\n")
        else:
            self.display_search_header(search_term, bool(exclusion_results))
            
            # Display variations
            variations = get_word_variations(search_term)
            if len(variations) > 1:
                self.results_text.insert(tk.END, "Included variations in search:\n")
                for var in variations:
                    if var != search_term.lower():
                        self.results_text.insert(tk.END, f"- {var}\n")
                self.results_text.insert(tk.END, "-" * 80 + "\n\n")
            
            # Separate and display results by type
            definition_results = [r for r in main_results if r['source'] == 'Definition']
            itk_results = [r for r in main_results if r['source'] == 'ITK']
            
            if definition_results:
                self.display_definition_results(definition_results)
            
            if itk_results:
                self.display_itk_results(itk_results)
            
            if exclusion_results:
                self.display_exclusion_results(exclusion_results)

        total_results = len(main_results) + len(exclusion_results) + len(cheat_code_results)
        self.status_var.set(f"Found {total_results} total results")
        self.reset_search_state()

    def reset_search_state(self):
        self.search_button.config(state=tk.NORMAL)
        self.search_entry.focus()

def get_word_variations(search_term):
    variations = set()
    search_term_lower = search_term.lower()
    
    variations.add(search_term_lower)
    
    for normalized, variants in COMPOUND_WORD_MAPPINGS.items():
        for variant in variants:
            if search_term_lower in variant.lower() or variant.lower() in search_term_lower:
                variations.update(v.lower() for v in variants)
                variations.add(normalized.lower())
    
    if search_term_lower in COMPOUND_WORD_REVERSE:
        normalized = COMPOUND_WORD_REVERSE[search_term_lower]
        variations.update(v.lower() for v in COMPOUND_WORD_MAPPINGS[normalized])
    
    return variations


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductSearchGUI(root)
    root.mainloop()


