from flask import Flask, render_template, request, jsonify
import os, re, json, webbrowser, threading, time
import pandas as pd

app = Flask(__name__)

# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════
FOLDER_NAME = "Script related"   # ← Folder name on your Desktop

TREX_FILES = {
    'pk':    'Keywords CSV',
    'incl':  'Definition - Inclusion CSV',
    'excl':  'Definition - Exclusion CSV',
    'cheat': 'Cheat codes CSV',
    'ambi':  'Ambiguous CSV',
}
T2F_FEES_FILE = 'Fees Percentage csv'
# ════════════════════════════════════════════════════════════════

# ── In-memory stores ─────────────────────────────────────────────
_trex   = {'pk': [], 'incl': [], 'excl': [], 'cheat': [], 'ambi': []}
_t2f    = {}   # { 'US': {'headers':[...], 'data':[{...},...]} }
_fees   = {}   # { 'US': {category: pct} }
_status = {}   # { filename: 'status string' }

DATA_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
SETTINGS_PATH = os.path.join(DATA_DIR, 'settings.json')

def save_settings(d):
    with open(SETTINGS_PATH, 'w') as f: json.dump(d, f)

def load_settings():
    try:
        with open(SETTINGS_PATH) as f: return json.load(f)
    except: return {}

def get_folder():
    return os.path.join(os.path.expanduser('~'), 'Desktop', FOLDER_NAME)

def try_read(folder, base):
    """Try reading file with .csv / .xlsx / no extension."""
    for ext in ['', '.csv', '.xlsx', '.xls']:
        path = os.path.join(folder, base + ext)
        if os.path.exists(path):
            try:
                if path.lower().endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(path, dtype=str, keep_default_na=False)
                else:
                    df = pd.read_csv(path, dtype=str, keep_default_na=False,
                                     encoding='utf-8-sig')
                return df, None
            except Exception as e:
                return None, str(e)
    return None, 'File not found'

def detect_mp_files(folder):
    """Find files matching {MARKETPLACE}_{8-digit-date} pattern."""
    pat = re.compile(r'^(.+?)_(\d{8})(\..+)?$', re.IGNORECASE)
    result = {}
    try:
        for fn in os.listdir(folder):
            m = pat.match(fn)
            if m:
                mp   = m.group(1).strip()
                base = os.path.splitext(fn)[0]
                result[mp] = base
    except: pass
    return result

def load_all():
    global _trex, _t2f, _fees, _status
    folder  = get_folder()
    _status = {}

    if not os.path.isdir(folder):
        _status['_folder'] = f"❌ Folder '{FOLDER_NAME}' not found on Desktop"
        print(f"\n  ❌ Folder not found: {folder}\n")
        return

    # ── TRexID files ─────────────────────────────────────────────
    for key, base in TREX_FILES.items():
        df, err = try_read(folder, base)
        if err:
            _status[base] = f"❌ {err}"
            _trex[key] = []
        else:
            _trex[key] = df.values.tolist()
            _status[base] = f"✓ {len(df):,} rows"

    # ── T2F marketplace files ─────────────────────────────────────
    _t2f = {}
    for mp, base in sorted(detect_mp_files(folder).items()):
        df, err = try_read(folder, base)
        if err:
            _status[base] = f"❌ {err}"
        else:
            _t2f[mp] = {'headers': list(df.columns), 'data': df.to_dict('records')}
            _status[base] = f"✓ {len(df):,} rows"

    # ── Fees ─────────────────────────────────────────────────────
    df, err = try_read(folder, T2F_FEES_FILE)
    if err:
        _status[T2F_FEES_FILE] = f"❌ {err}"
        _fees = {}
    else:
        _fees = {}
        for _, row in df.iterrows():
            mp  = str(row.iloc[0]).strip().upper()
            cat = str(row.iloc[1]).strip()
            pct = str(row.iloc[2]).strip()
            if mp and cat and pct:
                _fees.setdefault(mp, {})[cat] = pct
        _status[T2F_FEES_FILE] = f"✓ {len(df):,} rows"

    ok  = sum(1 for s in _status.values() if s.startswith('✓'))
    bad = sum(1 for s in _status.values() if s.startswith('❌'))
    print(f"\n📁 '{FOLDER_NAME}' — {ok} loaded, {bad} failed:")
    for n, s in _status.items():
        print(f"   {s}  —  {n}")
    print()

# ── Routes ────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    mps  = sorted(_t2f.keys())
    s    = load_settings()
    last = s.get('last_mp', mps[0] if mps else '')
    if last not in mps and mps:
        last = mps[0]
    ok  = sum(1 for v in _status.values() if v.startswith('✓'))
    bad = sum(1 for v in _status.values() if v.startswith('❌'))
    return jsonify({
        'folder':       FOLDER_NAME,
        'folder_ok':    os.path.isdir(get_folder()),
        'files':        _status,
        'marketplaces': mps,
        'last_mp':      last,
        'ok_count':     ok,
        'err_count':    bad,
    })

@app.route('/api/reload', methods=['POST'])
def api_reload():
    load_all()
    mps  = sorted(_t2f.keys())
    ok   = sum(1 for v in _status.values() if v.startswith('✓'))
    bad  = sum(1 for v in _status.values() if v.startswith('❌'))
    return jsonify({
        'ok':           True,
        'status':       _status,
        'marketplaces': mps,
        'ok_count':     ok,
        'err_count':    bad,
    })

# ── T2F ──────────────────────────────────────────────────────────
@app.route('/api/t2f/mp_info')
def t2f_mp_info():
    mp = request.args.get('mp', '').strip()
    if mp not in _t2f:
        return jsonify({'headers': [], 'has_fees': False, 'rows': 0})
    s = load_settings(); s['last_mp'] = mp; save_settings(s)
    return jsonify({
        'headers':  _t2f[mp]['headers'],
        'has_fees': mp in _fees and bool(_fees[mp]),
        'rows':     len(_t2f[mp]['data']),
    })

VALID_FEE_COLS = [
    'seller facing fee category', 'seller-facing-fee-category',
    'current seller facing fee category', 'current-seller facing fee category',
    'current seller facing fee category(effective until sept 30)',
    'current-seller-facing-fee-category',
]

def get_fee(headers, mp, row):
    if len(headers) < 3: return 'N/A'
    col = headers[2].lower().strip()
    if not any(p in col for p in VALID_FEE_COLS): return 'N/A'
    cat = (row.get(headers[2], '') or '').strip()
    for k, v in _fees.get(mp, {}).items():
        if k.lower() == cat.lower(): return v
    return 'N/A'

@app.route('/api/t2f/search', methods=['POST'])
def t2f_search():
    b  = request.get_json(silent=True) or {}
    mp = b.get('mp', '').strip()
    sv = b.get('search_values', [])
    fs = b.get('fees_search', '').strip().lower()

    if mp not in _t2f:
        return jsonify({'headers': [], 'rows': [], 'total': 0})

    headers  = _t2f[mp]['headers']
    has_fees = mp in _fees and bool(_fees[mp])
    while len(sv) < len(headers): sv.append('')

    out = []
    for row in _t2f[mp]['data']:
        ok = True
        for i, h in enumerate(headers):
            q = sv[i].lower() if i < len(sv) else ''
            if q and q not in (row.get(h, '') or '').lower():
                ok = False; break
        if ok and has_fees and fs:
            if fs not in get_fee(headers, mp, row).lower():
                ok = False
        if ok:
            r = {h: row.get(h, '') for h in headers}
            if has_fees: r['Fees%'] = get_fee(headers, mp, row)
            out.append(r)

    return jsonify({
        'headers': headers + (['Fees%'] if has_fees else []),
        'rows':    out,
        'total':   len(out),
    })

# ── TRexID ────────────────────────────────────────────────────────
@app.route('/api/trex/search', methods=['POST'])
def trex_search():
    b    = request.get_json(silent=True) or {}
    pk_q = b.get('product', '').lower().strip()
    tx_q = b.get('trexid',  '').lower().strip()
    if not pk_q and not tx_q:
        return jsonify({'pk': [], 'cheat': [], 'defs': []})

    def cell(r, i): return (r[i] if i < len(r) else '').lower()

    pk_res = [
        {'keyword': r[0] if r else '', 'trexid': r[1] if len(r) > 1 else ''}
        for r in _trex['pk']
        if (not pk_q or pk_q in cell(r, 0)) and (not tx_q or tx_q in cell(r, 1))
    ]

    cheat_res = [
        {'scenario': r[0] if r else '',
         'trexid':   r[1] if len(r) > 1 else '',
         'exclusion':r[2] if len(r) > 2 else ''}
        for r in _trex['cheat']
        if (not pk_q or pk_q in cell(r, 0)) and (not tx_q or tx_q in cell(r, 1))
    ]

    def_map = {}
    for r in _trex['incl']:
        tid, defn = (r[0] if r else ''), (r[1] if len(r) > 1 else '')
        if (pk_q and pk_q in defn.lower()) or (tx_q and tx_q in tid.lower()):
            def_map[tid] = {'incl': defn}
    for r in _trex['excl']:
        tid, defn = (r[0] if r else ''), (r[1] if len(r) > 1 else '')
        if (pk_q and pk_q in defn.lower()) or (tx_q and tx_q in tid.lower()):
            def_map.setdefault(tid, {})['excl'] = defn

    defs = [{'trexid': k, 'incl': v.get('incl', ''), 'excl': v.get('excl', '')}
            for k, v in def_map.items()]
    return jsonify({'pk': pk_res, 'cheat': cheat_res, 'defs': defs})

@app.route('/api/trex/ambi')
def trex_ambi():
    return jsonify([{
        'asin':        r[0] if r else '',
        'description': r[1] if len(r) > 1 else '',
        'trexid':      r[2] if len(r) > 2 else '',
        'comments':    r[3] if len(r) > 3 else '',
        'decision':    r[4] if len(r) > 4 else '',
    } for r in _trex['ambi']])

# ── Launch ────────────────────────────────────────────────────────
if __name__ == '__main__':
    load_all()
    def _open():
        time.sleep(1.2)
        webbrowser.open('http://127.0.0.1:5000')
    threading.Thread(target=_open, daemon=True).start()
    print('🌐 http://127.0.0.1:5000\n')
    app.run(debug=False, port=5000, use_reloader=False)