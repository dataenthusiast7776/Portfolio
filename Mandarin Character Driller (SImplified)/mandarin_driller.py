import json, os, random, re, shutil, time
import tkinter as tk
import tkinter.font as tkfont
from collections import Counter
from datetime import date, timedelta
from tkinter import ttk, messagebox

# ---------------------------------------------------------------- config
DIR = os.path.dirname(os.path.abspath(__file__))   # always next to this script
DATA_FILE = os.path.join(DIR, "characters.json")
META_FILE = os.path.join(DIR, "meta.json")
BACKUP_DIR = os.path.join(DIR, "backups")

BG, CARD, CARD2 = "#0f1219", "#181d29", "#232a3a"
TEXT, MUTED, ACCENT, HOVER = "#f2f4f8", "#8b95a9", "#6c8cff", "#3a4662"
GREEN, RED, YELLOW = "#4ade80", "#f87171", "#facc15"
TILES = ["#2a3040", "#b91c1c", "#c2410c", "#ca8a04", "#65a30d", "#16a34a", "#22c55e"]


# ---------------------------------------------------------------- safe storage
def load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as err:
        shutil.copy(path, path + ".corrupt")
        messagebox.showerror("Could not read " + os.path.basename(path),
                             f"{err}\n\nA copy was kept as .corrupt. The app will close so nothing is overwritten.")
        raise SystemExit


def write_atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)          # never leaves a half-written file


def backup():
    if not os.path.exists(DATA_FILE):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"characters_{date.today()}.json")
    if not os.path.exists(dst):
        shutil.copy(DATA_FILE, dst)
    for old in sorted(os.listdir(BACKUP_DIR))[:-14]:
        os.remove(os.path.join(BACKUP_DIR, old))


characters = load(DATA_FILE, {})
meta = load(META_FILE, {})
meta.setdefault("days", {}); meta.setdefault("goal", 30); meta.setdefault("sprint_best", 0)


def save():
    write_atomic(DATA_FILE, characters)
    write_atomic(META_FILE, meta)


def day_streak():
    d = date.today()
    if not meta["days"].get(str(d)):
        d -= timedelta(days=1)
    n = 0
    while meta["days"].get(str(d)):
        n += 1; d -= timedelta(days=1)
    return n


# ---------------------------------------------------------------- pinyin
VOW = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "v": "ǖǘǚǜ"}
TONE_MARKS = {m: (b, i + 1) for b, ms in VOW.items() for i, m in enumerate(ms)}


def normalize_pinyin(text):
    text = text.strip().lower().replace("ü", "v").replace(" ", "")
    m = re.search(r"([0-5])$", text)
    if m:
        t = int(m.group(1))
        return text[:-1], (0 if t == 5 else t)
    for mark, (base, t) in TONE_MARKS.items():
        if mark in text:
            return text.replace(mark, base), t
    return text, None


def grade_pinyin(user, e):
    """'ok', 'tone' (right syllable, wrong tone) or 'no'."""
    base, tone = normalize_pinyin(user)
    if base != e["pinyin"].lower():
        return "no"
    want = e.get("tone")
    if want in (0, None):
        return "ok" if tone in (None, 0) else "tone"
    return "ok" if tone == want else "tone"


def display_pinyin(e):
    p, t = e["pinyin"], e.get("tone")
    if not t:
        return p.replace("v", "ü")
    i = -1
    for c in ("a", "e"):
        if c in p:
            i = p.index(c); break
    else:
        if "ou" in p:
            i = p.index("o")
        else:
            for k in range(len(p) - 1, -1, -1):
                if p[k] in "iouv":
                    i = k; break
    return p if i < 0 else p[:i] + VOW[p[i]][t - 1] + p[i + 1:]


def soundalikes(ch):
    p = characters[ch]["pinyin"]
    return [f"{c} {display_pinyin(e)}" for c, e in characters.items() if c != ch and e["pinyin"] == p]


# ---------------------------------------------------------------- learning model
def tier(e):
    if not (e.get("correct", 0) + e.get("incorrect", 0)):
        return "New"
    s = e.get("strength", 0)
    return "Seedling" if s <= 3 else "Growing" if s <= 7 else "Mastered"


def tile_color(e):
    if tier(e) == "New":
        return TILES[0]
    return TILES[1 + min(5, e.get("strength", 0) // 2)]


def weight(e):
    if not (e.get("correct", 0) + e.get("incorrect", 0)):
        return 12
    w = max(1, 12 - e.get("strength", 0)) + e.get("incorrect", 0) * 1.5
    return max(1, w - min(e.get("streak", 0) * 0.2, 3))


def choose_character(last=None):
    chars = list(characters)
    w = [weight(characters[c]) for c in chars]
    if len(chars) > 1 and last in chars:
        w[chars.index(last)] *= 0.05
    return random.choices(chars, weights=w, k=1)[0]


def update_character(ch, result, typed=""):
    e = characters[ch]
    if result == "ok":
        e["correct"] = e.get("correct", 0) + 1
        e["streak"] = e.get("streak", 0) + 1
        e["strength"] = min(10, e.get("strength", 0) + 1)
    else:
        e["incorrect"] = e.get("incorrect", 0) + 1
        e["streak"] = 0
        e["strength"] = max(0, e.get("strength", 0) - (1 if result == "tone" else 3))
        if typed:
            w = e.setdefault("wrong", {})
            w[typed[:24]] = w.get(typed[:24], 0) + 1     # remembers *how* you get it wrong
    day = str(date.today())
    meta["days"][day] = meta["days"].get(day, 0) + 1
    save()


# ---------------------------------------------------------------- app
class App:
    def __init__(self, root):
        self.root = root
        root.title("中文 Character Driller"); root.geometry("980x800"); root.minsize(880, 720)
        root.configure(bg=BG)
        fams = set(tkfont.families())
        self.cjk = next((f for f in ("Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "SimHei") if f in fams), "TkDefaultFont")
        self.ui = next((f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Helvetica") if f in fams), "TkDefaultFont")
        self.pending, self.clock, self.queue, self.end_time = [], None, None, None
        st = ttk.Style(); st.theme_use("clam")
        st.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, rowheight=34,
                     borderwidth=0, font=(self.cjk, 12))
        st.configure("Treeview.Heading", background=CARD2, foreground=TEXT, font=(self.ui, 11, "bold"), borderwidth=0)
        st.map("Treeview", background=[("selected", ACCENT)])
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self.home()

    # ---- widgets
    def L(self, parent, text, size=11, color=TEXT, bold=False, font=None, **kw):
        return tk.Label(parent, text=text, bg=kw.pop("bg", parent["bg"]), fg=color,
                        font=(font or self.ui, size, "bold" if bold else "normal"), **kw)

    def B(self, parent, text, cmd, primary=False, width=24):
        bg = ACCENT if primary else CARD2
        b = tk.Button(parent, text=text, command=cmd, width=width, pady=9, bg=bg, fg="white" if primary else TEXT,
                      activebackground=HOVER, activeforeground="white", relief="flat", bd=0,
                      font=(self.ui, 12, "bold"), cursor="hand2")
        b.bind("<Enter>", lambda e: b.config(bg=HOVER)); b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def entry(self, parent, size=16, font=None, width=22):
        return tk.Entry(parent, font=(font or self.ui, size), bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat",
                        width=width, highlightthickness=2, highlightbackground=CARD2, highlightcolor=ACCENT)

    def later(self, ms, fn):
        self.pending.append(self.root.after(ms, fn))

    def clear(self, keep_clock=False):
        for i in self.pending:
            self.root.after_cancel(i)
        self.pending = []
        if self.clock and not keep_clock:
            self.root.after_cancel(self.clock); self.clock = None
        for k in ("<Return>", "<Escape>", "<Key-1>", "<Key-2>", "<Key-3>", "<Key-4>"):
            self.root.unbind(k)
        for w in self.root.winfo_children():
            w.destroy()

    def title(self, text, sub=None):
        self.L(self.root, text, 28, bold=True).pack(pady=(26, 2))
        if sub:
            self.L(self.root, sub, 11, MUTED).pack(pady=(0, 10))

    def menu_btn(self, parent=None):
        self.B(parent or self.root, "← Main Menu", self.home, width=18).pack(pady=16)

    def quit(self):
        save(); self.root.destroy()

    # ---- home
    def home(self):
        self.clear()
        self.title("中文 Character Driller", "Grow your characters — don't just flip cards")
        today, goal = meta["days"].get(str(date.today()), 0), max(1, meta["goal"])
        row = tk.Frame(self.root, bg=BG); row.pack(pady=(6, 4))
        self.L(row, f"Today {today}/{goal}", 11, bold=True).pack(side="left", padx=10)
        bar = tk.Canvas(row, width=300, height=10, bg=CARD2, highlightthickness=0); bar.pack(side="left")
        bar.create_rectangle(0, 0, 300 * min(1, today / goal), 10, fill=GREEN if today >= goal else ACCENT, width=0)
        self.L(row, f"🔥 {day_streak()}-day streak", 11, YELLOW, True).pack(side="left", padx=16)
        self.garden()
        g = tk.Frame(self.root, bg=BG); g.pack(pady=8)
        btns = [("▶  Pinyin Drill", lambda: self.start("pinyin"), True),
                ("◉  Meaning Quiz", lambda: self.start("meaning"), True),
                ("⚡  60s Sprint", lambda: self.start("sprint"), True),
                ("＋  Add Character", self.add, False), ("☷  Character Bank", self.bank, False),
                ("▣  Insights", self.insights, False)]
        for i, (t, c, p) in enumerate(btns):
            self.B(g, t, c, p, 26).grid(row=i // 3, column=i % 3, padx=6, pady=6)

    def garden(self):
        box = tk.Frame(self.root, bg=CARD, padx=16, pady=12); box.pack(padx=40, pady=12, fill="x")
        self.L(box, f"YOUR GARDEN  ·  {len(characters)} characters", 9, MUTED, True).pack(anchor="w", pady=(0, 6))
        items, size, gap, W = list(characters.items()), 34, 5, 860
        cols = W // (size + gap)
        rows = max(1, -(-len(items) // cols))
        cv = tk.Canvas(box, width=W, height=rows * (size + gap), bg=CARD, highlightthickness=0); cv.pack()
        for i, (c, e) in enumerate(items):
            x, y = (i % cols) * (size + gap), (i // cols) * (size + gap)
            cv.create_rectangle(x, y, x + size, y + size, fill=tile_color(e), width=0)
            cv.create_text(x + size / 2, y + size / 2, text=c, fill="white", font=(self.cjk, 14))
        info = self.L(box, "Hover a tile  ·  grey = new · red = weak · green = strong", 10, MUTED)
        info.pack(anchor="w", pady=(8, 0))

        def hover(ev):
            i = (ev.y // (size + gap)) * cols + ev.x // (size + gap)
            if 0 <= i < len(items):
                c, e = items[i]
                info.config(text=f"{c}  {display_pinyin(e)}  ·  {e['meaning']}  ·  {tier(e)} (strength {e.get('strength', 0)})")
        cv.bind("<Motion>", hover)

    # ---- drill
    def start(self, mode, pool=None):
        need = 4 if mode == "meaning" else 1
        if len(characters) < need:
            messagebox.showwarning("Not enough characters", f"This mode needs at least {need} characters."); return
        self.mode, self.last, self.missed = mode, None, []
        self.q = self.ok = self.streak = self.best = 0
        self.queue = random.sample(pool, len(pool)) if pool else None
        self.end_time = time.time() + 60 if mode == "sprint" else None
        self.next_q()

    def tick(self):
        left = self.end_time - time.time()
        if left <= 0:
            return self.summary()
        try:
            self.timer_lbl.config(text=f"⏱ {left:.0f}s")
        except (tk.TclError, AttributeError):
            pass
        self.clock = self.root.after(200, self.tick)

    def next_q(self):
        self.clear(keep_clock=True)
        if self.end_time and time.time() >= self.end_time:
            return self.summary()
        if self.queue is not None:
            if not self.queue:
                return self.summary()
            ch = self.queue.pop()
        else:
            ch = choose_character(self.last)
        self.cur = self.last = ch; self.answered = False
        e = characters[ch]
        top = tk.Frame(self.root, bg=BG); top.pack(fill="x", padx=36, pady=(22, 0))
        acc = 100 * self.ok / self.q if self.q else 0
        self.L(top, f"{self.ok}/{self.q} correct  ·  {acc:.0f}%", 11, MUTED).pack(side="left")
        self.L(top, "Esc = finish", 10, MUTED).pack(side="right")
        self.L(top, f"🔥 {self.streak}   ", 12, YELLOW if self.streak else MUTED, True).pack(side="right")
        if self.end_time:
            self.timer_lbl = self.L(top, "", 12, ACCENT, True); self.timer_lbl.pack(side="right", padx=14)
        self.L(self.root, ch, 120, font=self.cjk).pack(expand=True)
        self.L(self.root, tier(e).upper(), 9, MUTED, True).pack()

        if self.mode == "meaning":
            others = list({v["meaning"] for v in characters.values() if v["meaning"] != e["meaning"]})
            opts = random.sample(others, min(3, len(others))) + [e["meaning"]]
            random.shuffle(opts)
            box = tk.Frame(self.root, bg=BG); box.pack(pady=10)
            self.opt_btns = {}
            for i, o in enumerate(opts):
                b = self.B(box, f"{i + 1}   {o[:30]}", lambda o=o: self.pick(o), False, 36)
                b.grid(row=i // 2, column=i % 2, padx=6, pady=5); self.opt_btns[o] = b
                self.root.bind(f"<Key-{i + 1}>", lambda ev, o=o: self.pick(o))
        else:
            self.ent = self.entry(self.root, 22, width=18); self.ent.pack(pady=(10, 4), ipady=6); self.ent.focus()
            self.L(self.root, "pinyin + tone   ·   xué  /  xue2  /  de5  (neutral tone: just 'de')", 10, MUTED).pack()
            self.root.bind("<Return>", lambda ev: self.submit())
        self.fb = self.L(self.root, "", 16, bold=True); self.fb.pack(pady=(14, 2))
        self.detail = self.L(self.root, "", 11, MUTED, justify="center"); self.detail.pack()
        self.nav = tk.Frame(self.root, bg=BG); self.nav.pack(pady=14)
        self.root.bind("<Escape>", lambda ev: self.summary())
        if self.end_time and not self.clock:
            self.tick()

    def submit(self):
        t = self.ent.get().strip()
        if t and not self.answered:
            self.grade(grade_pinyin(t, characters[self.cur]), t)

    def pick(self, choice):
        if self.answered:
            return
        want = characters[self.cur]["meaning"]
        self.grade("ok" if choice == want else "no", choice)
        for o, b in self.opt_btns.items():
            b.unbind("<Enter>"); b.unbind("<Leave>")
            b.config(bg="#166534" if o == want else "#991b1b" if o == choice else CARD2)

    def grade(self, res, typed):
        self.answered = True; self.q += 1
        e = characters[self.cur]
        update_character(self.cur, res, typed)
        if res == "ok":
            self.ok += 1; self.streak += 1; self.best = max(self.best, self.streak)
            self.fb.config(text=f"✓ Correct   {display_pinyin(e)}", fg=GREEN)
        else:
            self.streak = 0
            if self.cur not in self.missed:
                self.missed.append(self.cur)
            if res == "tone":
                self.fb.config(text=f"◐ Right sound, wrong tone  →  {display_pinyin(e)}", fg=YELLOW)
            else:
                self.fb.config(text=f"✗ {display_pinyin(e)}", fg=RED)
        twins = soundalikes(self.cur)
        self.detail.config(text=e["meaning"] + ("\nSound-alikes:  " + "    ".join(twins[:5]) if twins else ""))
        if self.mode != "meaning":
            self.ent.config(state="disabled")
        if self.end_time:
            self.later(250 if res == "ok" else 1400, self.next_q)
        else:
            self.root.bind("<Return>", lambda ev: self.next_q())
            self.B(self.nav, "Next  →", self.next_q, True, 16).pack()

    def summary(self):
        self.clear()
        acc = 100 * self.ok / self.q if self.q else 0
        record = ""
        if self.mode == "sprint" and self.ok > meta["sprint_best"]:
            meta["sprint_best"] = self.ok; save(); record = "  🏆 New record!"
        self.title("Session Complete", "Nice work." + record)
        card = tk.Frame(self.root, bg=CARD, padx=60, pady=30); card.pack(pady=14)
        rows = [("Questions", self.q), ("Correct", self.ok), ("Accuracy", f"{acc:.0f}%"), ("Best streak", f"🔥 {self.best}")]
        if self.mode == "sprint":
            rows.append(("Sprint record", meta["sprint_best"]))
        for k, v in rows:
            r = tk.Frame(card, bg=CARD); r.pack(fill="x", pady=6)
            self.L(r, k, 12, MUTED, width=20, anchor="w").pack(side="left")
            self.L(r, str(v), 13, bold=True).pack(side="right")
        if self.missed:
            self.L(self.root, "Missed:  " + "  ".join(f"{c} {display_pinyin(characters[c])}" for c in self.missed[:10]),
                   13, RED, font=self.cjk).pack(pady=6)
            m = "pinyin" if self.mode == "sprint" else self.mode
            self.B(self.root, f"Retry {len(self.missed)} missed", lambda: self.start(m, list(self.missed)), True, 22).pack(pady=5)
        self.B(self.root, "Drill again", lambda: self.start(self.mode), False, 22).pack(pady=5)
        self.menu_btn()

    # ---- add
    def add(self, msg=""):
        self.clear()
        self.title("Add Character", "Include the tone in the pinyin: xue2, xué, or de0 for neutral")
        card = tk.Frame(self.root, bg=CARD, padx=40, pady=26); card.pack(pady=8)
        ents = {}
        for i, (k, lab, f) in enumerate([("c", "Character", self.cjk), ("p", "Pinyin", self.ui), ("m", "Meaning", self.ui)]):
            self.L(card, lab, 11, MUTED, True).grid(row=i, column=0, sticky="w", pady=10)
            ents[k] = self.entry(card, 18, f, 20); ents[k].grid(row=i, column=1, padx=18, ipady=4)
        ents["c"].focus()
        self.L(self.root, msg, 12, GREEN).pack(pady=6)

        def go(*_):
            c, p, m = (ents[k].get().strip() for k in "cpm")
            if not (c and p and m):
                return messagebox.showwarning("Missing info", "Fill in all three fields.")
            if c in characters:
                return messagebox.showwarning("Already exists", f"{c} is already in your bank.")
            base, tone = normalize_pinyin(p)
            if tone is None:
                return messagebox.showwarning("Add a tone", "Use xue2, xué, or de0 for neutral tone.")
            characters[c] = {"pinyin": base, "tone": tone, "meaning": m, "strength": 0,
                             "correct": 0, "incorrect": 0, "streak": 0}
            save(); self.add(f"✓ Added {c}")
        self.root.bind("<Return>", go)
        self.B(self.root, "Add Character", go, True, 18).pack(pady=6)
        self.menu_btn()

    # ---- bank
    def bank(self):
        self.clear()
        self.title("Character Bank", f"{len(characters)} characters")
        var = tk.StringVar()
        self.entry(self.root, 13, width=30).pack(pady=(0, 8), ipady=3)
        s = self.root.winfo_children()[-1]; s.config(textvariable=var)
        frame = tk.Frame(self.root, bg=BG); frame.pack(fill="both", expand=True, padx=40)
        cols = {"Character": 90, "Pinyin": 110, "Meaning": 290, "Stage": 100, "✓": 60, "✗": 60}
        tree = ttk.Treeview(frame, columns=list(cols), show="headings", selectmode="extended")
        for c, w in cols.items():
            tree.heading(c, text=c); tree.column(c, width=w, anchor="w" if c == "Meaning" else "center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")

        def fill(*_):
            tree.delete(*tree.get_children())
            q = var.get().strip().lower()
            for c, e in characters.items():
                row = (c, display_pinyin(e), e["meaning"], tier(e), e.get("correct", 0), e.get("incorrect", 0))
                if q in " ".join(map(str, row)).lower():
                    tree.insert("", "end", iid=c, values=row)

        def delete():
            sel = tree.selection()
            if sel and messagebox.askyesno("Delete", f"Delete {len(sel)} character(s)? Their progress is lost."):
                for c in sel:
                    characters.pop(c, None)
                save(); fill()
        var.trace_add("write", fill); fill()
        bar = tk.Frame(self.root, bg=BG); bar.pack(pady=12)
        self.B(bar, "Delete selected", delete, False, 18).pack(side="left", padx=6)
        self.B(bar, "← Main Menu", self.home, False, 18).pack(side="left", padx=6)

    # ---- insights
    def insights(self):
        self.clear()
        self.title("Insights", "Where you're growing — and where you keep slipping")
        cs = list(characters.values())
        ok, bad = sum(e.get("correct", 0) for e in cs), sum(e.get("incorrect", 0) for e in cs)
        t = Counter(tier(e) for e in cs)
        card = tk.Frame(self.root, bg=CARD, padx=40, pady=18); card.pack(pady=6)
        rows = [("Characters", len(cs)), ("Answers", ok + bad), ("Accuracy", f"{100 * ok / (ok + bad):.0f}%" if ok + bad else "–"),
                ("Mastered / Growing", f"{t['Mastered']} / {t['Growing']}"), ("Seedlings / New", f"{t['Seedling']} / {t['New']}"),
                ("Sprint record", meta["sprint_best"])]
        for k, v in rows:
            r = tk.Frame(card, bg=CARD); r.pack(fill="x", pady=4)
            self.L(r, k, 12, MUTED, width=24, anchor="w").pack(side="left")
            self.L(r, str(v), 13, bold=True).pack(side="right")
        self.L(self.root, "LAST 14 DAYS", 9, MUTED, True).pack(pady=(14, 2))
        cv = tk.Canvas(self.root, width=580, height=110, bg=BG, highlightthickness=0); cv.pack()
        days = [date.today() - timedelta(days=13 - i) for i in range(14)]
        vals = [meta["days"].get(str(d), 0) for d in days]
        mx = max(vals + [meta["goal"]])
        for i, (d, v) in enumerate(zip(days, vals)):
            x, h = i * 41 + 6, v / mx * 80
            cv.create_rectangle(x, 90 - h, x + 30, 90, fill=GREEN if v >= meta["goal"] else ACCENT, width=0)
            cv.create_text(x + 15, 101, text=d.strftime("%d"), fill=MUTED, font=(self.ui, 8))
        self.L(self.root, "TROUBLE SPOTS", 9, MUTED, True).pack(pady=(14, 4))
        worst = sorted(characters.items(), key=lambda kv: -kv[1].get("incorrect", 0))[:5]
        for c, e in worst:
            if not e.get("incorrect"):
                continue
            w = e.get("wrong", {})
            often = f"  ·  you often said “{max(w, key=w.get)}”" if w else ""
            self.L(self.root, f"{c}  {display_pinyin(e)}  —  missed {e['incorrect']}×{often}", 13, MUTED, font=self.cjk).pack(pady=2)
        self.menu_btn()


if __name__ == "__main__":
    backup()
    root = tk.Tk()
    App(root)
    root.mainloop()
