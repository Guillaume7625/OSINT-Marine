#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
To-Do Pro Local — Application de gestion de tâches professionnelles
Stack : Python 3, Tkinter, SQLite, OpenAI (optionnel), keyring, dateparser
Auteur : généré pour usage personnel macOS
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import json
import csv
import threading
import re
from pathlib import Path
from datetime import datetime, date, timedelta
import dateparser

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from openai import OpenAI, APIError, APITimeoutError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
APP_NAME = "To-Do Pro Local"
KEYRING_SERVICE = "todo_pro_local"
KEYRING_USERNAME = "openai_api_key"
DB_PATH = Path.home() / ".todo_pro_local" / "tasks.db"

STATUTS = ["À faire", "En cours", "En attente", "Fait", "Annulé"]

# Mots-clés qui signalent une ambiguïté temporelle nécessitant confirmation
AMBIGUOUS_KEYWORDS = [
    "semaine prochaine", "la semaine", "fin de semaine", "début de semaine",
    "début", "fin", "milieu", "courant", "bientôt", "prochainement",
    "ce mois", "le mois", "prochain mois", "mois prochain",
    "dans quelques", "dans les prochains",
]

# Expressions relatives non ambiguës (interprétation directe sans confirmation)
RELATIVE_UNAMBIGUOUS = [
    "aujourd'hui", "aujourd hui", "maintenant",
    "demain", "après-demain", "apres-demain",
    "hier",  # peu probable pour une deadline mais gérable
]

# Jours de la semaine isolés = ambigus (quelle semaine ?)
WEEKDAY_NAMES = [
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"
]

DATEPARSER_SETTINGS_FUTURE = {"PREFER_DATES_FROM": "future"}
DATEPARSER_SETTINGS_WEEKDAY = {
    "PREFER_DAY_OF_MONTH": "first",
    "PREFER_DATES_FROM": "future",
}


# ---------------------------------------------------------------------------
# BASE DE DONNÉES
# ---------------------------------------------------------------------------

def init_db():
    """Crée le répertoire et la base SQLite si absents."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sujet       TEXT NOT NULL,
            commentaire TEXT,
            deadline    TEXT,
            urgent      INTEGER DEFAULT 0,
            statut      TEXT DEFAULT 'À faire',
            cree_le     TEXT,
            modifie_le  TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


def fetch_all_tasks():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, sujet, commentaire, deadline, urgent, statut, cree_le, modifie_le
        FROM tasks
        ORDER BY
            CASE WHEN deadline IS NULL OR deadline = '' THEN 1 ELSE 0 END,
            deadline ASC,
            urgent DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def insert_task(sujet, commentaire, deadline, urgent, statut):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (sujet, commentaire, deadline, urgent, statut, cree_le, modifie_le)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sujet, commentaire, deadline, int(urgent), statut, now, now))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def update_task(task_id, sujet, commentaire, deadline, urgent, statut):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE tasks SET sujet=?, commentaire=?, deadline=?, urgent=?, statut=?, modifie_le=?
        WHERE id=?
    """, (sujet, commentaire, deadline, int(urgent), statut, now, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def mark_done(task_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tasks SET statut='Fait', modifie_le=? WHERE id=?", (now, task_id))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# GESTION CLÉ API
# ---------------------------------------------------------------------------

def get_api_key():
    if not KEYRING_AVAILABLE:
        return None
    try:
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception:
        return None


def set_api_key(key: str):
    if not KEYRING_AVAILABLE:
        return False
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
        return True
    except Exception:
        return False


def delete_api_key():
    if not KEYRING_AVAILABLE:
        return
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# LOGIQUE DE DATE
# ---------------------------------------------------------------------------

def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def interpreter_deadline(raw: str):
    """
    Interprète une saisie de deadline.
    Retourne un dict :
      {
        "date_str": "YYYY-MM-DD" ou None,
        "ambigue":  True/False,
        "question": "..." ou None,
        "raw":      raw
      }
    """
    if not raw or not raw.strip():
        return {"date_str": None, "ambigue": False, "question": None, "raw": raw}

    raw_lower = raw.strip().lower()

    # 1. Expression directement non ambiguë
    for expr in RELATIVE_UNAMBIGUOUS:
        if expr in raw_lower:
            parsed = dateparser.parse(raw, languages=["fr"])
            if parsed:
                return {
                    "date_str": parsed.strftime("%Y-%m-%d"),
                    "ambigue": False,
                    "question": None,
                    "raw": raw
                }

    # 2. Jour de la semaine seul (lundi, mardi…) => ambigu
    for wd in WEEKDAY_NAMES:
        if _contains_phrase(raw_lower, wd):
            parsed = dateparser.parse(raw, languages=["fr"], settings=DATEPARSER_SETTINGS_WEEKDAY)
            if parsed:
                date_lisible = parsed.strftime("%A %d %B %Y").lower()
                # capitalize first letter
                date_lisible = date_lisible[0].upper() + date_lisible[1:]
                return {
                    "date_str": parsed.strftime("%Y-%m-%d"),
                    "ambigue": True,
                    "question": f"Voulez-vous dire le {date_lisible} ?",
                    "raw": raw
                }

    # 3. Mots-clés ambigus
    for kw in AMBIGUOUS_KEYWORDS:
        if _contains_phrase(raw_lower, kw):
            parsed = dateparser.parse(raw, languages=["fr"], settings=DATEPARSER_SETTINGS_FUTURE)
            if parsed:
                date_lisible = parsed.strftime("%d/%m/%Y")
                return {
                    "date_str": parsed.strftime("%Y-%m-%d"),
                    "ambigue": True,
                    "question": f"Voulez-vous dire le {date_lisible} ?",
                    "raw": raw
                }
            else:
                return {
                    "date_str": None,
                    "ambigue": True,
                    "question": f"La date « {raw} » est ambiguë. Pouvez-vous préciser une date exacte ?",
                    "raw": raw
                }

    # 4. Tentative de parsing direct (date explicite)
    parsed = dateparser.parse(raw, languages=["fr"])
    if parsed:
        return {
            "date_str": parsed.strftime("%Y-%m-%d"),
            "ambigue": False,
            "question": None,
            "raw": raw
        }

    # 5. Échec total
    return {
        "date_str": None,
        "ambigue": True,
        "question": f"Impossible d'interpréter « {raw} ». Entrez une date au format JJ/MM/AAAA.",
        "raw": raw
    }


def analyser_suffisance_des_champs(sujet: str, deadline_raw: str, commentaire: str):
    """
    Vérifie la suffisance minimale des champs sans IA.
    Retourne (ok: bool, message: str or None)
    """
    if not sujet or not sujet.strip():
        return False, "Le sujet est obligatoire."
    return True, None


def generer_question_si_ambiguite(deadline_info: dict):
    """
    À partir du résultat d'interpreter_deadline,
    retourne une question si ambiguïté, sinon None.
    """
    if deadline_info.get("ambigue") and deadline_info.get("question"):
        return deadline_info["question"]
    return None


# ---------------------------------------------------------------------------
# APPEL OPENAI
# ---------------------------------------------------------------------------

def appel_openai(sujet: str, commentaire: str, deadline_raw: str, api_key: str):
    """
    Appelle l'API OpenAI pour analyser la tâche et détecter des ambiguïtés.
    Retourne un dict structuré ou None en cas d'erreur.
    """
    if not OPENAI_AVAILABLE or not api_key:
        return None

    prompt_system = (
        "Tu es un assistant de gestion de tâches professionnelles. "
        "Tu reçois une tâche partielle et tu dois analyser si les informations sont suffisantes. "
        "Réponds UNIQUEMENT en JSON strict, sans texte autour, avec exactement ces clés :\n"
        "{\n"
        '  "sujet_reformule": "...",\n'
        '  "commentaire_reformule": "...",\n'
        '  "deadline_normalisee": "YYYY-MM-DD ou null",\n'
        '  "ambiguite_detectee": true ou false,\n'
        '  "question_unique": "question courte ou null"\n'
        "}\n"
        "Règles :\n"
        "- Ne pose jamais plus d'une question.\n"
        "- Si tout est clair, ambiguite_detectee=false et question_unique=null.\n"
        "- Ne modifie pas les données sans raison.\n"
        "- Réponds en français.\n"
        "- deadline_normalisee doit être au format YYYY-MM-DD ou null si absente ou impossible à déterminer.\n"
        "- Si la deadline est ambiguë, mets null et pose une question."
    )

    prompt_user = (
        f"Sujet : {sujet}\n"
        f"Commentaire : {commentaire or '(vide)'}\n"
        f"Deadline brute : {deadline_raw or '(vide)'}\n"
        f"Date du jour : {date.today().strftime('%Y-%m-%d')}"
    )

    try:
        client = OpenAI(api_key=api_key, timeout=15.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw_content = response.choices[0].message.content.strip()
        # Nettoyage au cas où le modèle ajouterait des blocs markdown
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
            raw_content = raw_content.strip()
        result = json.loads(raw_content)
        return result
    except (APIError, APITimeoutError) as e:
        return {"erreur": f"Erreur API : {e}"}
    except json.JSONDecodeError:
        return {"erreur": "Réponse IA non parseable."}
    except Exception as e:
        return {"erreur": str(e)}


# ---------------------------------------------------------------------------
# EXPORT CSV
# ---------------------------------------------------------------------------

def exporter_csv(tasks, filepath):
    """Exporte la liste des tâches en CSV."""
    headers = ["ID", "Sujet", "Commentaire", "Deadline", "Urgent", "Statut", "Créé le", "Modifié le"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for t in tasks:
            writer.writerow([
                t[0], t[1], t[2], t[3],
                "Oui" if t[4] else "Non",
                t[5], t[6], t[7]
            ])


# ---------------------------------------------------------------------------
# APPLICATION TKINTER
# ---------------------------------------------------------------------------

class ToDoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg="#f5f5f5")

        init_db()

        # État interne
        self.selected_task_id = None
        self.api_key = get_api_key()
        self._pending_deadline_info = None  # résultat interpreter_deadline en attente de confirmation
        self._pending_task_data = None

        self._build_menu()
        self._build_ui()
        self._refresh_table()
        self._update_api_status()

    # -----------------------------------------------------------------------
    # MENU
    # -----------------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        menu_fichier = tk.Menu(menubar, tearoff=0)
        menu_fichier.add_command(label="Exporter en CSV…", command=self._export_csv)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.quit)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)

        menu_config = tk.Menu(menubar, tearoff=0)
        menu_config.add_command(label="Configurer la clé API OpenAI…", command=self._dialog_api_key)
        menu_config.add_command(label="Supprimer la clé API", command=self._delete_api_key)
        menubar.add_cascade(label="Configuration", menu=menu_config)

        self.config(menu=menubar)

    # -----------------------------------------------------------------------
    # INTERFACE PRINCIPALE
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # ---- Barre de statut en bas ----
        self.status_var = tk.StringVar(value="Prêt.")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            anchor="w", bg="#e0e0e0", fg="#333",
            relief="flat", padx=8, pady=3, font=("Helvetica", 11)
        )
        status_bar.pack(side="bottom", fill="x")

        # ---- Indicateur clé API ----
        self.api_label_var = tk.StringVar()
        api_lbl = tk.Label(
            self, textvariable=self.api_label_var,
            anchor="e", bg="#e0e0e0", fg="#555",
            relief="flat", padx=8, pady=3, font=("Helvetica", 10)
        )
        api_lbl.pack(side="bottom", fill="x")

        # ---- Panneau principal (2 colonnes) ----
        main_frame = tk.Frame(self, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Colonne gauche : formulaire + tableau
        left_frame = tk.Frame(main_frame, bg="#f5f5f5")
        left_frame.pack(side="left", fill="both", expand=True)

        # Colonne droite : panneau d'édition
        right_frame = tk.Frame(main_frame, bg="#ebebeb", relief="flat", bd=1, width=340)
        right_frame.pack(side="right", fill="y", padx=(8, 0))
        right_frame.pack_propagate(False)

        self._build_form(left_frame)
        self._build_table(left_frame)
        self._build_edit_panel(right_frame)

    # -----------------------------------------------------------------------
    # FORMULAIRE DE CRÉATION
    # -----------------------------------------------------------------------

    def _build_form(self, parent):
        form = tk.LabelFrame(parent, text="Nouvelle tâche", bg="#f5f5f5",
                              font=("Helvetica", 12, "bold"), padx=8, pady=6)
        form.pack(fill="x", pady=(0, 6))

        # Ligne 1 : Sujet
        row1 = tk.Frame(form, bg="#f5f5f5")
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Sujet *", width=10, anchor="w", bg="#f5f5f5",
                 font=("Helvetica", 11)).pack(side="left")
        self.entry_sujet = tk.Entry(row1, font=("Helvetica", 11))
        self.entry_sujet.pack(side="left", fill="x", expand=True)

        # Ligne 2 : Commentaire
        row2 = tk.Frame(form, bg="#f5f5f5")
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Commentaire", width=10, anchor="w", bg="#f5f5f5",
                 font=("Helvetica", 11)).pack(side="left")
        self.entry_comment = tk.Entry(row2, font=("Helvetica", 11))
        self.entry_comment.pack(side="left", fill="x", expand=True)

        # Ligne 3 : Deadline + Urgent
        row3 = tk.Frame(form, bg="#f5f5f5")
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Deadline", width=10, anchor="w", bg="#f5f5f5",
                 font=("Helvetica", 11)).pack(side="left")
        self.entry_deadline = tk.Entry(row3, width=22, font=("Helvetica", 11))
        self.entry_deadline.pack(side="left", padx=(0, 12))

        self.urgent_var = tk.BooleanVar()
        tk.Checkbutton(row3, text="Urgent", variable=self.urgent_var,
                       bg="#f5f5f5", font=("Helvetica", 11)).pack(side="left", padx=(0, 12))

        self.statut_var = tk.StringVar(value=STATUTS[0])
        tk.Label(row3, text="Statut", bg="#f5f5f5", font=("Helvetica", 11)).pack(side="left")
        statut_combo = ttk.Combobox(row3, textvariable=self.statut_var,
                                    values=STATUTS, state="readonly", width=12,
                                    font=("Helvetica", 11))
        statut_combo.pack(side="left", padx=(4, 0))

        # Zone de clarification (masquée par défaut)
        self.clarif_frame = tk.Frame(form, bg="#fff8e1", relief="flat", bd=1)
        self.clarif_label_var = tk.StringVar()
        self.clarif_label = tk.Label(
            self.clarif_frame, textvariable=self.clarif_label_var,
            bg="#fff8e1", fg="#7a5c00", font=("Helvetica", 11), wraplength=600, anchor="w"
        )
        self.clarif_label.pack(side="left", padx=6, pady=4, fill="x", expand=True)

        self.btn_clarif_oui = tk.Button(
            self.clarif_frame, text="Oui", width=5,
            command=self._clarif_confirm_oui, font=("Helvetica", 11)
        )
        self.btn_clarif_oui.pack(side="left", padx=4, pady=4)

        self.btn_clarif_non = tk.Button(
            self.clarif_frame, text="Non", width=5,
            command=self._clarif_confirm_non, font=("Helvetica", 11)
        )
        self.btn_clarif_non.pack(side="left", padx=4, pady=4)

        # Boutons du formulaire
        row_btn = tk.Frame(form, bg="#f5f5f5")
        row_btn.pack(fill="x", pady=(6, 0))

        tk.Button(row_btn, text="Ajouter", width=10, bg="#4CAF50", fg="white",
                  font=("Helvetica", 11, "bold"),
                  command=self._action_ajouter).pack(side="left", padx=(0, 6))

        tk.Button(row_btn, text="Analyser (IA)", width=12, bg="#2196F3", fg="white",
                  font=("Helvetica", 11),
                  command=self._action_analyser_ia).pack(side="left", padx=(0, 6))

        tk.Button(row_btn, text="Vider", width=8,
                  font=("Helvetica", 11),
                  command=self._vider_formulaire).pack(side="left")

    # -----------------------------------------------------------------------
    # TABLEAU DES TÂCHES
    # -----------------------------------------------------------------------

    def _build_table(self, parent):
        table_frame = tk.Frame(parent, bg="#f5f5f5")
        table_frame.pack(fill="both", expand=True)

        cols = ("Sujet", "Deadline", "Urgent", "Statut", "Modifié le")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        # Configuration colonnes
        self.tree.column("Sujet", width=280, anchor="w")
        self.tree.column("Deadline", width=100, anchor="center")
        self.tree.column("Urgent", width=60, anchor="center")
        self.tree.column("Statut", width=100, anchor="center")
        self.tree.column("Modifié le", width=130, anchor="center")

        for col in cols:
            self.tree.heading(col, text=col, anchor="center")

        # Style zebra light
        self.tree.tag_configure("urgent", foreground="#c62828")
        self.tree.tag_configure("fait", foreground="#9e9e9e")
        self.tree.tag_configure("normal", foreground="#212121")

        # Scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_task_select)

    # -----------------------------------------------------------------------
    # PANNEAU D'ÉDITION (colonne droite)
    # -----------------------------------------------------------------------

    def _build_edit_panel(self, parent):
        tk.Label(parent, text="Détail / Édition", font=("Helvetica", 12, "bold"),
                 bg="#ebebeb").pack(padx=10, pady=(10, 4), anchor="w")

        pad = {"padx": 10, "pady": 3, "anchor": "w"}

        tk.Label(parent, text="Sujet", bg="#ebebeb", font=("Helvetica", 11)).pack(**pad)
        self.edit_sujet = tk.Entry(parent, font=("Helvetica", 11))
        self.edit_sujet.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(parent, text="Commentaire", bg="#ebebeb", font=("Helvetica", 11)).pack(**pad)
        self.edit_comment = tk.Text(parent, height=4, font=("Helvetica", 11), wrap="word")
        self.edit_comment.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(parent, text="Deadline (JJ/MM/AAAA ou texte)", bg="#ebebeb",
                 font=("Helvetica", 11)).pack(**pad)
        self.edit_deadline = tk.Entry(parent, font=("Helvetica", 11))
        self.edit_deadline.pack(fill="x", padx=10, pady=(0, 4))

        self.edit_urgent_var = tk.BooleanVar()
        tk.Checkbutton(parent, text="Urgent", variable=self.edit_urgent_var,
                       bg="#ebebeb", font=("Helvetica", 11)).pack(padx=10, pady=2, anchor="w")

        tk.Label(parent, text="Statut", bg="#ebebeb", font=("Helvetica", 11)).pack(**pad)
        self.edit_statut_var = tk.StringVar(value=STATUTS[0])
        edit_combo = ttk.Combobox(parent, textvariable=self.edit_statut_var,
                                  values=STATUTS, state="readonly", font=("Helvetica", 11))
        edit_combo.pack(fill="x", padx=10, pady=(0, 6))

        # Dates en lecture seule
        self.edit_dates_var = tk.StringVar(value="")
        tk.Label(parent, textvariable=self.edit_dates_var, bg="#ebebeb",
                 fg="#666", font=("Helvetica", 9), wraplength=300).pack(padx=10, anchor="w")

        sep = tk.Frame(parent, height=1, bg="#bbb")
        sep.pack(fill="x", padx=10, pady=8)

        # Zone clarification édition
        self.edit_clarif_frame = tk.Frame(parent, bg="#fff8e1", relief="flat", bd=1)
        self.edit_clarif_label_var = tk.StringVar()
        tk.Label(self.edit_clarif_frame, textvariable=self.edit_clarif_label_var,
                 bg="#fff8e1", fg="#7a5c00", font=("Helvetica", 10),
                 wraplength=280, anchor="w").pack(side="left", padx=6, pady=4, fill="x", expand=True)
        self.btn_edit_clarif_oui = tk.Button(
            self.edit_clarif_frame, text="Oui", width=4,
            command=self._edit_clarif_oui, font=("Helvetica", 10)
        )
        self.btn_edit_clarif_oui.pack(side="left", padx=2, pady=4)
        self.btn_edit_clarif_non = tk.Button(
            self.edit_clarif_frame, text="Non", width=4,
            command=self._edit_clarif_non, font=("Helvetica", 10)
        )
        self.btn_edit_clarif_non.pack(side="left", padx=2, pady=4)

        # Boutons d'action
        btn_frame = tk.Frame(parent, bg="#ebebeb")
        btn_frame.pack(fill="x", padx=10, pady=4)

        tk.Button(btn_frame, text="Enregistrer", bg="#4CAF50", fg="white",
                  font=("Helvetica", 11, "bold"),
                  command=self._action_enregistrer).pack(fill="x", pady=2)

        tk.Button(btn_frame, text="Marquer comme faite", bg="#FF9800", fg="white",
                  font=("Helvetica", 11),
                  command=self._action_marquer_fait).pack(fill="x", pady=2)

        tk.Button(btn_frame, text="Annuler", font=("Helvetica", 11),
                  command=self._action_annuler_edit).pack(fill="x", pady=2)

        tk.Button(btn_frame, text="Supprimer", bg="#f44336", fg="white",
                  font=("Helvetica", 11),
                  command=self._action_supprimer).pack(fill="x", pady=2)

    # -----------------------------------------------------------------------
    # RAFRAÎCHISSEMENT TABLE
    # -----------------------------------------------------------------------

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        tasks = fetch_all_tasks()
        for t in tasks:
            tid, sujet, _, deadline, urgent, statut, _, modifie = t
            tag = "fait" if statut == "Fait" else ("urgent" if urgent else "normal")
            deadline_affiche = deadline if deadline else ""
            urgent_affiche = "⚠️" if urgent else ""
            self.tree.insert("", "end", iid=str(tid),
                             values=(sujet, deadline_affiche, urgent_affiche, statut, modifie),
                             tags=(tag,))

    # -----------------------------------------------------------------------
    # SÉLECTION D'UNE TÂCHE
    # -----------------------------------------------------------------------

    def _on_task_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        task_id = int(sel[0])
        self.selected_task_id = task_id
        self._hide_edit_clarif()

        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return

        _, sujet, commentaire, deadline, urgent, statut, cree_le, modifie_le = row

        self.edit_sujet.delete(0, "end")
        self.edit_sujet.insert(0, sujet or "")

        self.edit_comment.delete("1.0", "end")
        self.edit_comment.insert("1.0", commentaire or "")

        self.edit_deadline.delete(0, "end")
        self.edit_deadline.insert(0, deadline or "")

        self.edit_urgent_var.set(bool(urgent))
        self.edit_statut_var.set(statut or STATUTS[0])

        self.edit_dates_var.set(
            f"Créé le : {cree_le}\nModifié le : {modifie_le}"
        )

    # -----------------------------------------------------------------------
    # ACTIONS FORMULAIRE DE CRÉATION
    # -----------------------------------------------------------------------

    def _action_ajouter(self):
        """Tente d'ajouter une tâche depuis le formulaire de création."""
        sujet = self.entry_sujet.get().strip()
        commentaire = self.entry_comment.get().strip()
        deadline_raw = self.entry_deadline.get().strip()
        urgent = self.urgent_var.get()
        statut = self.statut_var.get()

        # Vérification suffisance
        ok, msg = analyser_suffisance_des_champs(sujet, deadline_raw, commentaire)
        if not ok:
            self._set_status(f"⚠ {msg}")
            messagebox.showwarning("Champ manquant", msg)
            return

        # Interprétation deadline
        deadline_info = interpreter_deadline(deadline_raw)
        question = generer_question_si_ambiguite(deadline_info)

        if question:
            if not deadline_info.get("date_str"):
                self._set_status(question)
                messagebox.showinfo("Date ambiguë", question)
                self.entry_deadline.focus_set()
                return
            # Afficher zone de clarification
            self._pending_deadline_info = deadline_info
            self._pending_task_data = {
                "sujet": sujet, "commentaire": commentaire,
                "deadline_raw": deadline_raw,
                "urgent": urgent, "statut": statut,
                "context": "create"
            }
            self._show_clarif(question)
            self._set_status("Ambiguïté détectée sur la date.")
            return

        # Pas d'ambiguïté : créer directement
        deadline_finale = deadline_info["date_str"]
        insert_task(sujet, commentaire, deadline_finale, urgent, statut)
        self._refresh_table()
        self._vider_formulaire()
        self._set_status("Tâche ajoutée.")

    def _action_analyser_ia(self):
        """Appelle l'API IA pour analyser la saisie et pré-remplir les champs."""
        sujet = self.entry_sujet.get().strip()
        commentaire = self.entry_comment.get().strip()
        deadline_raw = self.entry_deadline.get().strip()

        if not sujet and not commentaire and not deadline_raw:
            self._set_status("Formulaire vide, rien à analyser.")
            return

        if not OPENAI_AVAILABLE:
            self._set_status("Module OpenAI indisponible — mode local uniquement.")
            messagebox.showinfo("OpenAI", "Le module OpenAI n'est pas installé.")
            return

        api_key = get_api_key()
        if not api_key:
            self._set_status("Clé API absente — mode local uniquement.")
            messagebox.showinfo(
                "Clé API",
                "Aucune clé API configurée.\nMenu > Configuration > Configurer la clé API OpenAI…"
            )
            return

        self._set_status("Analyse IA en cours…")
        self.config(cursor="watch")
        self.update()

        def run():
            result = appel_openai(sujet, commentaire, deadline_raw, api_key)
            self.after(0, lambda: self._handle_ia_result(result))

        threading.Thread(target=run, daemon=True).start()

    def _handle_ia_result(self, result):
        self.config(cursor="")
        if result is None:
            self._set_status("Clé API absente ou module OpenAI indisponible.")
            return
        if "erreur" in result:
            self._set_status(f"Erreur IA : {result['erreur']}")
            return

        # Mise à jour des champs si l'IA a reformulé
        sujet_ia = result.get("sujet_reformule", "")
        comment_ia = result.get("commentaire_reformule", "")
        deadline_ia = result.get("deadline_normalisee", "")
        ambiguite = result.get("ambiguite_detectee", False)
        question_ia = result.get("question_unique", None)

        if sujet_ia and sujet_ia != self.entry_sujet.get().strip():
            if messagebox.askyesno("Reformulation IA",
                                   f"L'IA suggère ce sujet :\n« {sujet_ia} »\nAccepter ?"):
                self.entry_sujet.delete(0, "end")
                self.entry_sujet.insert(0, sujet_ia)

        if comment_ia and comment_ia != self.entry_comment.get().strip():
            if messagebox.askyesno("Reformulation IA",
                                   f"L'IA suggère ce commentaire :\n« {comment_ia} »\nAccepter ?"):
                self.entry_comment.delete(0, "end")
                self.entry_comment.insert(0, comment_ia)

        if deadline_ia and deadline_ia != "null":
            self.entry_deadline.delete(0, "end")
            self.entry_deadline.insert(0, deadline_ia)

        if ambiguite and question_ia:
            if deadline_ia and deadline_ia != "null":
                self._set_status(f"IA : {question_ia}")
                # Afficher la question dans la zone de clarification
                self._pending_deadline_info = {
                    "date_str": deadline_ia,
                    "ambigue": True,
                    "question": question_ia,
                    "raw": self.entry_deadline.get()
                }
                self._pending_task_data = {
                    "sujet": self.entry_sujet.get().strip(),
                    "commentaire": self.entry_comment.get().strip(),
                    "deadline_raw": self.entry_deadline.get().strip(),
                    "urgent": self.urgent_var.get(),
                    "statut": self.statut_var.get(),
                    "context": "create"
                }
                self._show_clarif(question_ia)
            else:
                self._set_status(f"IA : {question_ia}")
                messagebox.showinfo("Clarification IA", question_ia)
                self.entry_deadline.focus_set()
        else:
            self._set_status("Analyse IA terminée. Vérifiez les champs.")

    # -----------------------------------------------------------------------
    # ZONE DE CLARIFICATION (formulaire création)
    # -----------------------------------------------------------------------

    def _show_clarif(self, question: str):
        self.clarif_label_var.set(question)
        self.clarif_frame.pack(fill="x", padx=0, pady=(4, 0))

    def _hide_clarif(self):
        self.clarif_frame.pack_forget()
        self._pending_deadline_info = None
        self._pending_task_data = None

    def _clarif_confirm_oui(self):
        """L'utilisateur confirme la date proposée."""
        if self._pending_deadline_info and self._pending_task_data:
            data = self._pending_task_data
            deadline_finale = self._pending_deadline_info.get("date_str")
            if not deadline_finale:
                self._hide_clarif()
                self._set_status("Veuillez saisir une date plus précise.")
                messagebox.showinfo("Date manquante", "Impossible de confirmer sans date explicite.")
                self.entry_deadline.focus_set()
                return
            if data.get("context") == "create":
                insert_task(
                    data["sujet"], data["commentaire"],
                    deadline_finale, data["urgent"], data["statut"]
                )
                self._refresh_table()
                self._vider_formulaire()
                self._set_status("Tâche ajoutée.")
        self._hide_clarif()

    def _clarif_confirm_non(self):
        """L'utilisateur refuse la date proposée : vider le champ deadline."""
        self.entry_deadline.delete(0, "end")
        self.entry_deadline.focus_set()
        self._hide_clarif()
        self._set_status("Veuillez saisir une date plus précise.")

    # -----------------------------------------------------------------------
    # PANNEAU D'ÉDITION — ACTIONS
    # -----------------------------------------------------------------------

    def _action_enregistrer(self):
        if self.selected_task_id is None:
            self._set_status("Aucune tâche sélectionnée.")
            return

        sujet = self.edit_sujet.get().strip()
        commentaire = self.edit_comment.get("1.0", "end").strip()
        deadline_raw = self.edit_deadline.get().strip()
        urgent = self.edit_urgent_var.get()
        statut = self.edit_statut_var.get()

        ok, msg = analyser_suffisance_des_champs(sujet, deadline_raw, commentaire)
        if not ok:
            self._set_status(f"⚠ {msg}")
            messagebox.showwarning("Champ manquant", msg)
            return

        deadline_info = interpreter_deadline(deadline_raw)
        question = generer_question_si_ambiguite(deadline_info)

        if question:
            if not deadline_info.get("date_str"):
                self._set_status(question)
                messagebox.showinfo("Date ambiguë", question)
                self.edit_deadline.focus_set()
                return
            self._pending_deadline_info = deadline_info
            self._pending_task_data = {
                "sujet": sujet, "commentaire": commentaire,
                "urgent": urgent, "statut": statut,
                "context": "edit"
            }
            self._show_edit_clarif(question)
            self._set_status("Ambiguïté détectée sur la date.")
            return

        deadline_finale = deadline_info["date_str"]
        update_task(self.selected_task_id, sujet, commentaire, deadline_finale, urgent, statut)
        self._refresh_table()
        self._set_status("Tâche enregistrée.")

    def _action_marquer_fait(self):
        if self.selected_task_id is None:
            self._set_status("Aucune tâche sélectionnée.")
            return
        mark_done(self.selected_task_id)
        self._refresh_table()
        self.edit_statut_var.set("Fait")
        self._set_status("Tâche marquée comme faite.")

    def _action_annuler_edit(self):
        self._hide_edit_clarif()
        if self.selected_task_id:
            # Recharger depuis la base
            self._reload_edit_from_db(self.selected_task_id)
        self._set_status("Modification annulée.")

    def _reload_edit_from_db(self, task_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return
        _, sujet, commentaire, deadline, urgent, statut, cree_le, modifie_le = row
        self.edit_sujet.delete(0, "end")
        self.edit_sujet.insert(0, sujet or "")
        self.edit_comment.delete("1.0", "end")
        self.edit_comment.insert("1.0", commentaire or "")
        self.edit_deadline.delete(0, "end")
        self.edit_deadline.insert(0, deadline or "")
        self.edit_urgent_var.set(bool(urgent))
        self.edit_statut_var.set(statut or STATUTS[0])

    def _action_supprimer(self):
        if self.selected_task_id is None:
            self._set_status("Aucune tâche sélectionnée.")
            return
        sujet = self.edit_sujet.get().strip() or f"ID {self.selected_task_id}"
        if not messagebox.askyesno("Confirmation",
                                   f"Supprimer la tâche :\n« {sujet} » ?\n\nCette action est irréversible."):
            return
        delete_task(self.selected_task_id)
        self._refresh_table()
        self._clear_edit_panel()
        self.selected_task_id = None
        self._set_status("Tâche supprimée.")

    # -----------------------------------------------------------------------
    # ZONE DE CLARIFICATION (édition)
    # -----------------------------------------------------------------------

    def _show_edit_clarif(self, question: str):
        self.edit_clarif_label_var.set(question)
        self.edit_clarif_frame.pack(fill="x", padx=10, pady=(0, 6))

    def _hide_edit_clarif(self):
        self.edit_clarif_frame.pack_forget()
        self._pending_deadline_info = None
        self._pending_task_data = None

    def _edit_clarif_oui(self):
        if self._pending_deadline_info and self._pending_task_data:
            data = self._pending_task_data
            deadline_finale = self._pending_deadline_info.get("date_str")
            if not deadline_finale:
                self._hide_edit_clarif()
                self._set_status("Veuillez saisir une date plus précise.")
                messagebox.showinfo("Date manquante", "Impossible de confirmer sans date explicite.")
                self.edit_deadline.focus_set()
                return
            update_task(
                self.selected_task_id,
                data["sujet"], data["commentaire"],
                deadline_finale, data["urgent"], data["statut"]
            )
            self.edit_deadline.delete(0, "end")
            self.edit_deadline.insert(0, deadline_finale or "")
            self._refresh_table()
            self._set_status("Tâche enregistrée.")
        self._hide_edit_clarif()

    def _edit_clarif_non(self):
        self.edit_deadline.delete(0, "end")
        self.edit_deadline.focus_set()
        self._hide_edit_clarif()
        self._set_status("Veuillez saisir une date plus précise.")

    # -----------------------------------------------------------------------
    # UTILITAIRES UI
    # -----------------------------------------------------------------------

    def _vider_formulaire(self):
        self.entry_sujet.delete(0, "end")
        self.entry_comment.delete(0, "end")
        self.entry_deadline.delete(0, "end")
        self.urgent_var.set(False)
        self.statut_var.set(STATUTS[0])
        self._hide_clarif()

    def _clear_edit_panel(self):
        self.edit_sujet.delete(0, "end")
        self.edit_comment.delete("1.0", "end")
        self.edit_deadline.delete(0, "end")
        self.edit_urgent_var.set(False)
        self.edit_statut_var.set(STATUTS[0])
        self.edit_dates_var.set("")
        self._hide_edit_clarif()

    def _set_status(self, msg: str):
        self.status_var.set(msg)
        self.update_idletasks()

    def _update_api_status(self):
        if not OPENAI_AVAILABLE:
            self.api_label_var.set("⚠ OpenAI : module indisponible — mode local uniquement")
            return
        key = get_api_key()
        if key:
            self.api_label_var.set("🔑 Clé API OpenAI : configurée")
        else:
            self.api_label_var.set("⚠ Clé API OpenAI : non configurée — mode local uniquement")

    # -----------------------------------------------------------------------
    # DIALOGUE CLÉ API
    # -----------------------------------------------------------------------

    def _dialog_api_key(self):
        dialog = tk.Toplevel(self)
        dialog.title("Configurer la clé API OpenAI")
        dialog.geometry("480x160")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg="#f5f5f5")

        tk.Label(dialog, text="Clé API OpenAI (sk-…) :",
                 bg="#f5f5f5", font=("Helvetica", 11)).pack(padx=16, pady=(14, 4), anchor="w")

        entry = tk.Entry(dialog, show="*", font=("Helvetica", 11), width=48)
        entry.pack(padx=16, fill="x")

        def toggle_show():
            entry.config(show="" if entry.cget("show") == "*" else "*")

        tk.Checkbutton(dialog, text="Afficher la clé", bg="#f5f5f5",
                       font=("Helvetica", 10), command=toggle_show).pack(padx=16, anchor="w")

        def sauver():
            key = entry.get().strip()
            if not key:
                messagebox.showwarning("Clé vide", "Veuillez saisir une clé API.")
                return
            if not key.startswith("sk-"):
                if not messagebox.askyesno("Clé inhabituelle",
                                           "La clé ne commence pas par 'sk-'.\nContinuer quand même ?"):
                    return
            if set_api_key(key):
                self.api_key = key
                self._update_api_status()
                self._set_status("Clé API enregistrée dans le trousseau macOS.")
                dialog.destroy()
            else:
                messagebox.showerror("Erreur", "Impossible d'enregistrer la clé dans keyring.")

        btn_frame = tk.Frame(dialog, bg="#f5f5f5")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Enregistrer", bg="#4CAF50", fg="white",
                  font=("Helvetica", 11), command=sauver).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Annuler", font=("Helvetica", 11),
                  command=dialog.destroy).pack(side="left", padx=6)

    def _delete_api_key(self):
        if not messagebox.askyesno("Supprimer la clé", "Supprimer la clé API du trousseau ?"):
            return
        delete_api_key()
        self.api_key = None
        self._update_api_status()
        self._set_status("Clé API supprimée.")

    # -----------------------------------------------------------------------
    # EXPORT CSV
    # -----------------------------------------------------------------------

    def _export_csv(self):
        tasks = fetch_all_tasks()
        if not tasks:
            messagebox.showinfo("Export CSV", "Aucune tâche à exporter.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="todo_pro_local.csv",
            title="Exporter les tâches"
        )
        if not filepath:
            return
        try:
            exporter_csv(tasks, filepath)
            self._set_status(f"Export CSV : {filepath}")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))


# ---------------------------------------------------------------------------
# POINT D'ENTRÉE
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = ToDoApp()
    app.mainloop()
