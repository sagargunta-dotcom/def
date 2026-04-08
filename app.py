from flask import Flask, render_template, request, jsonify
import pandas as pd
import re
import os
import webbrowser
import threading
import time

app = Flask(__name__)

# ------------------------------------------------------------------ #
#  Compound word mappings                                              #
# ------------------------------------------------------------------ #
COMPOUND_WORD_MAPPINGS = {
    'barcode scanner': ['bar code scanner', 'barcode scanner', 'bar-code scanner'],
    'barcode':         ['bar code', 'barcode', 'bar-code'],
    'toolkit':         ['tool kit', 'toolkit', 'tool-kit'],
    'airbrush':        ['air brush', 'airbrush', 'air-brush'],
    'database':        ['data base', 'database', 'data-base'],
    'workstation':     ['work station', 'workstation', 'work-station'],
    'smartphone':      ['smart phone', 'smartphone', 'smart-phone'],
    'worksheet':       ['work sheet', 'worksheet', 'work-sheet'],
    'whiteboard':      ['white board', 'whiteboard', 'white-board'],
    'hardcover':       ['hard cover', 'hardcover', 'hard-cover'],
    'wallpaper':       ['wall paper', 'wallpaper', 'wall-paper'],
    'headphone':       ['head phone', 'headphone', 'head-phone'],
    'keyboard':        ['key board', 'keyboard', 'key-board'],
    'bookshelf':       ['book shelf', 'bookshelf', 'book-shelf'],
    'tabletop':        ['table top', 'tabletop', 'table-top'],
    'handheld':        ['hand held', 'handheld', 'hand-held'],
    'touchscreen':     ['touch screen', 'touchscreen', 'touch-screen'],
    'backpack':        ['back pack', 'backpack', 'back-pack'],
    'flashlight':      ['flash light', 'flashlight', 'flash-light'],
    'thumbtack':       ['thumb tack', 'thumbtack', 'thumb-tack'],
    'pushpin':         ['push pin', 'pushpin', 'push-pin'],
    'bodychain':       ['body chain', 'bodychain', 'body-chain'],
    'flowmeter':       ['flow meter', 'flowmeter', 'flow-meter'],
}


def get_word_variations(search_term):
    variations = set()
    search_term_lower = search_term.lower().strip()
    variations.add(search_term_lower)
    for normalized, variants in COMPOUND_WORD_MAPPINGS.items():
        all_forms = {normalized.lower()} | {v.lower() for v in variants}
        if search_term_lower in all_forms:
            variations.update(all_forms)
            break
    return variations


def split_sentences(text):
    return [s.strip() for s in text.split('.') if s.strip()]


# ------------------------------------------------------------------ #
#  Global databases                                                    #
# ------------------------------------------------------------------ #
db1 = db2 = db3 = None
db_error = None


def load_databases():
    global db1, db2, db3, db_error
    search_dirs = [
        os.path.join(os.path.expanduser('~'), 'Desktop'),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
    ]
    files = {
        'db1': 'Definition CSV.csv',
        'db2': 'with outt.csv',
        'db3': 'Cheat codes csv.csv',
    }
    dbs = {}
    for key, filename in files.items():
        found = False
        for d in search_dirs:
            fp = os.path.join(d, filename)
            if os.path.exists(fp):
                dbs[key] = pd.read_csv(fp)
                print(f"  ✓ Loaded '{filename}' from {d}")
                found = True
                break
        if not found:
            db_error = f"'{filename}' not found. Place it on your Desktop or next to app.py."
            print(f"  ✗ {db_error}")
            return False

    db1, db2, db3 = dbs['db1'], dbs['db2'], dbs['db3']

    # Validate columns
    checks = [
        (db1, {'TrexID', 'Definition-Exclusion', 'Definition-Inclusion'}, 'Definition CSV.csv'),
        (db2, {'Category', 'TrexID'},                                      'with outt.csv'),
        (db3, {'Scenario', 'TRexID to follow', 'Exclusion'},               'Cheat codes csv.csv'),
    ]
    for df, required, name in checks:
        missing = required - set(df.columns)
        if missing:
            db_error = f"'{name}' is missing columns: {missing}"
            print(f"  ✗ {db_error}")
            return False

    return True


# ------------------------------------------------------------------ #
#  Search functions                                                    #
# ------------------------------------------------------------------ #
def search_database1(search_term):
    variations = get_word_variations(search_term)
    found_results, exclusion_results = [], []

    INCL_COL, EXCL_COL, TREX_COL = 'Definition-Inclusion', 'Definition-Exclusion', 'TrexID'
    pattern = '|'.join(re.escape(v) for v in variations)

    incl_mask = db1[INCL_COL].astype(str).str.contains(pattern, case=False, na=False)
    excl_mask = db1[EXCL_COL].astype(str).str.contains(pattern, case=False, na=False)

    for _, row in db1[incl_mask | excl_mask].iterrows():
        trex_id = str(row[TREX_COL])

        incl_text = str(row[INCL_COL])
        if any(v in incl_text.lower() for v in variations):
            for s in split_sentences(incl_text):
                if any(v in s.lower() for v in variations):
                    found_results.append({'source': 'Definition', 'category': trex_id, 'context': s})

        excl_text = str(row[EXCL_COL])
        if any(v in excl_text.lower() for v in variations):
            for s in split_sentences(excl_text):
                if any(v in s.lower() for v in variations):
                    exclusion_results.append({'source': 'Exclusion', 'category': trex_id, 'context': s})

    return found_results, exclusion_results


def search_database2(search_term):
    variations = get_word_variations(search_term)
    found_results = []
    pattern = '|'.join(re.escape(v) for v in variations)
    mask = db2['Category'].astype(str).str.contains(pattern, case=False, na=False)
    for _, row in db2[mask].iterrows():
        found_results.append({'source': 'ITK', 'result': str(row['TrexID']), 'matched_term': str(row['Category'])})
    return found_results


def search_database3(search_term):
    variations = get_word_variations(search_term)
    found_results = []
    pattern = '|'.join(re.escape(v) for v in variations)
    mask = db3['Scenario'].astype(str).str.contains(pattern, case=False, na=False)
    for _, row in db3[mask].iterrows():
        try:
            result = {'source': 'Cheat Code', 'scenario': str(row['Scenario']), 'trex_id': str(row['TRexID to follow'])}
            if pd.notna(row['Exclusion']) and str(row['Exclusion']).strip():
                result['exclusion'] = str(row['Exclusion']).strip()
            found_results.append(result)
        except Exception:
            continue
    return found_results


# ------------------------------------------------------------------ #
#  Routes                                                              #
# ------------------------------------------------------------------ #
@app.route('/')
def index():
    return render_template('index.html', db_error=db_error)


@app.route('/search', methods=['POST'])
def search():
    if db1 is None:
        return jsonify({'error': db_error or 'Databases not loaded.'}), 500

    data = request.get_json(silent=True) or {}
    search_term = str(data.get('search_term', '')).strip()[:200]

    if not search_term:
        return jsonify({'error': 'Please enter a search term.'}), 400

    try:
        definition_results, exclusion_results = search_database1(search_term)
        itk_results      = search_database2(search_term)
        cheat_results    = search_database3(search_term)
        variations       = list(get_word_variations(search_term))

        return jsonify({
            'definition_results': definition_results,
            'exclusion_results':  exclusion_results,
            'itk_results':        itk_results,
            'cheat_code_results': cheat_results,
            'variations':         variations,
            'total': len(definition_results) + len(exclusion_results) + len(itk_results) + len(cheat_results),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #
if __name__ == '__main__':
    print("\n🚀 Product Search Tool")
    print("─" * 40)
    load_databases()
    print("─" * 40)

    def _open():
        time.sleep(1.2)
        webbrowser.open('http://127.0.0.1:5000')

    threading.Thread(target=_open, daemon=True).start()
    print("🌐 Opening at http://127.0.0.1:5000\n")
    app.run(debug=False, port=5000, use_reloader=False)