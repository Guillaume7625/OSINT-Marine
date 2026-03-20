#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur d'ebook PDF professionnel
=====================================
Génère un PDF au format livre (A5) à partir du contenu intégré.
Dépendances : pip install weasyprint markdown
"""

import os
import re
import sys

import markdown


def _ensure_weasyprint_deps_on_macos() -> None:
    """
    Sur macOS, WeasyPrint dépend de bibliothèques natives (pango / glib).
    Si elles viennent de Homebrew (ex: /opt/homebrew/lib), il faut parfois
    aider le chargeur dynamique à les trouver.
    """

    if sys.platform != "darwin":
        return

    candidates = ["/opt/homebrew/lib", "/usr/local/lib"]
    existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    existing_paths = [p for p in existing.split(":") if p]

    for candidate in candidates:
        if not os.path.isdir(candidate):
            continue
        if candidate not in existing_paths:
            existing_paths.insert(0, candidate)
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(existing_paths)
        return


_ensure_weasyprint_deps_on_macos()

from weasyprint import HTML

# ═══════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BOOK_TITLE = "Protocoles de défense cognitive"
BOOK_SUBTITLE = "Outils opérationnels pour l'ère de la guerre informationnelle"
BOOK_AUTHOR = "[Votre Nom]"  # A personnaliser
BOOK_DATE = "Premiere edition -- Fevrier 2026"
OUTPUT_FILE = "ebook-defense-cognitive_v1.0_2026-02-08.pdf"
INPUT_MARKDOWN_FILE = "ebook_v2_definitif.md"

# ═══════════════════════════════════════════════════════════════
# 2. FEUILLE DE STYLE CSS (DESIGN ÉDITORIAL)
# ═══════════════════════════════════════════════════════════════

CSS = """
/* ── Format de page A5 (livre de poche) ── */
@page {
    size: A5;
    margin: 22mm 18mm 25mm 18mm;

    @bottom-center {
        content: "— " counter(page) " —";
        font-family: "Noto Serif", "DejaVu Serif", "Georgia", serif;
        font-size: 8pt;
        color: #888;
    }
}

/* Première page : pas de numéro */
@page :first {
    @bottom-center { content: none; }
}

/* ── Typographie générale ── */
body {
    font-family: "Noto Serif", "DejaVu Serif", "Georgia", "Palatino Linotype",
                 "Book Antiqua", "Times New Roman", serif;
    font-size: 10pt;
    line-height: 1.75;
    color: #1a1a1a;
    text-align: justify;
    hyphens: auto;
    orphans: 3;
    widows: 3;
}

/* ── Page de titre ── */
.cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    height: 100vh;
    padding: 0 10mm;
}

.cover-ornament {
    font-size: 28pt;
    color: #555;
    margin-bottom: 40px;
    letter-spacing: 8px;
}

.cover-title {
    font-size: 20pt;
    font-weight: 700;
    line-height: 1.3;
    color: #111;
    margin-bottom: 16px;
    letter-spacing: 0.5px;
}

.cover-subtitle {
    font-size: 11pt;
    font-style: italic;
    color: #444;
    margin-bottom: 50px;
    line-height: 1.6;
}

.cover-author {
    font-size: 11pt;
    font-weight: 600;
    color: #333;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.cover-date {
    font-size: 9pt;
    color: #777;
    margin-top: 40px;
}

.cover-rule {
    width: 60px;
    border: none;
    border-top: 2px solid #555;
    margin: 30px auto;
}

/* ── Page d'épigraphe ── */
.epigraph-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    padding: 0 15mm;
    text-align: center;
}

.epigraph-text {
    font-style: italic;
    font-size: 10.5pt;
    color: #333;
    line-height: 1.8;
    max-width: 85%;
    margin-bottom: 16px;
}

.epigraph-author {
    font-size: 9.5pt;
    color: #666;
}

/* ── Titres ── */
h1 {
    font-size: 18pt;
    font-weight: 700;
    text-align: center;
    color: #111;
    margin-top: 0;
    margin-bottom: 24px;
    letter-spacing: 0.5px;
    page-break-before: always;
    page-break-after: avoid;
}

/* Premier h1 après la couverture : pas de saut */
.no-break-before {
    page-break-before: avoid !important;
}

h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #222;
    margin-top: 28px;
    margin-bottom: 12px;
    page-break-after: avoid;
    border-bottom: none;
}

h3 {
    font-size: 11pt;
    font-weight: 700;
    color: #333;
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
}

h4 {
    font-size: 10pt;
    font-weight: 700;
    color: #444;
    margin-top: 16px;
    margin-bottom: 6px;
}

/* ── Paragraphes ── */
p {
    margin-top: 0;
    margin-bottom: 10px;
}

/* ── Listes ── */
ul, ol {
    margin-left: 0;
    padding-left: 18px;
}

li {
    margin-bottom: 4px;
}

/* ── Citations (avertissements, notes) ── */
blockquote {
    border-left: 3px solid #666;
    margin: 16px 0;
    padding: 10px 14px;
    background: #fafaf7;
    color: #333;
    font-size: 9.5pt;
    font-style: italic;
    page-break-inside: avoid;
}

blockquote p {
    margin: 4px 0;
}

/* ── Blocs de code (les prompts) ── */
pre {
    background: #f4f4ef;
    border: 1px solid #d4d4cc;
    border-radius: 4px;
    padding: 12px 14px;
    font-size: 8pt;
    line-height: 1.55;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    page-break-inside: avoid;
    margin: 14px 0;
}

code {
    font-family: "SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono",
                 "Noto Sans Mono", "Liberation Mono", monospace;
    font-size: 8pt;
    background: #eeeeea;
    padding: 1px 4px;
    border-radius: 2px;
}

pre code {
    background: none;
    padding: 0;
    border-radius: 0;
}

/* ── Tableaux ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

th, td {
    padding: 7px 10px;
    border: 1px solid #ccc;
    text-align: left;
    vertical-align: top;
}

th {
    background: #f0f0eb;
    font-weight: 700;
    color: #222;
}

tr:nth-child(even) td {
    background: #fafaf7;
}

/* ── Liens ── */
a {
    color: #2a5a8a;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* ── Séparateurs ── */
hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 28px auto;
    width: 40%;
}

/* ── Gras et italique contextuels ── */
strong {
    font-weight: 700;
    color: #111;
}

em {
    font-style: italic;
}

/* ── Ornement de section ── */
.section-ornament {
    text-align: center;
    font-size: 14pt;
    color: #888;
    margin: 30px 0 20px 0;
    letter-spacing: 6px;
}

/* ── Table des matières ── */
.toc {
    page-break-after: always;
}

.toc h1 {
    page-break-before: always;
}

.toc table {
    border: none;
    width: 100%;
}

.toc th, .toc td {
    border: none;
    padding: 5px 8px;
    font-size: 9.5pt;
}

.toc td:first-child {
    font-weight: 600;
    white-space: nowrap;
}

.toc td:last-child {
    font-style: italic;
    color: #555;
}

/* ── Utilitaire : forcer saut de page ── */
.page-break {
    page-break-after: always;
    height: 0;
    margin: 0;
    padding: 0;
}

/* ── ASCII art / schémas ── */
.diagram pre {
    text-align: center;
    font-size: 7.5pt;
    background: none;
    border: 1px solid #bbb;
    border-radius: 6px;
    padding: 16px;
}
"""

# ═══════════════════════════════════════════════════════════════
# 3. CONTENU MARKDOWN DE L'EBOOK
# ═══════════════════════════════════════════════════════════════

CONTENT_MD = r"""

## À propos de ce guide

Ce guide répertorie et analyse les prompts qui forcent une IA à ralentir, expliciter ses hypothèses, et chercher ses propres erreurs — en s'inspirant des travaux sur les biais cognitifs humains. Chaque prompt est cité en entier et évalué selon quatre critères : la qualité de clarification, la présence de contre-arguments, la séparation faits/inférences, et la capacité à proposer des vérifications concrètes. « Évalué » signifie ici : essayé sur des cas de faible enjeu et des cas à enjeux, en observant ces quatre dimensions. Ce n'est pas une validation scientifique.

L'objectif n'est pas de rendre l'IA plus intelligente, mais de rendre vos échanges avec elle plus rigoureux.

**Temps de lecture :** 25 minutes. **Temps pour tester votre premier prompt :** 2 minutes.

---

> **Note de confidentialité.** Plusieurs des prompts présentés ici vous invitent à décrire des situations personnelles, des dilemmes ou des croyances. Avant de coller quoi que ce soit dans un chatbot, anonymisez vos données : supprimez noms, montants, adresses et toute information sensible. Aucun prompt ne vaut une fuite de confidentialité.

> **Avertissement — prompt injection.** Si vous copiez un prompt trouvé en ligne, relisez-le intégralement avant de l'utiliser. Certains prompts contiennent des instructions cachées (collecte de données, contournement de garde-fous). Une lecture attentive de trente secondes suffit à repérer l'essentiel.

---

# Résumé exécutif — Pourquoi ces prompts existent et ce qu'ils changent

### Le problème : vitesse, plausibilité, biais

On alterne entre deux régimes de fonctionnement (modèle de Kahneman) :

Le **Système 1** est rapide, intuitif, efficace… mais sujet à des erreurs systématiques (ancrage, disponibilité, confirmation, etc.). Le **Système 2** est lent, coûteux, plus rigoureux… mais sollicité plus rarement parce qu'il demande un effort.

Par analogie, un **LLM** se comporte souvent comme un « Système 1 » : il produit vite un texte plausible à partir de régularités apprises. Résultat : il peut être convaincant même quand il a tort, et il est sensible au cadrage (comment la question est posée) — comme nous.

Ce guide part d'un constat simple : **vous ne pouvez pas supprimer les biais d'un LLM avec un prompt**, mais vous pouvez **structurer l'échange** pour ralentir les réponses quand il le faut, rendre visibles les hypothèses et angles morts, exiger des tests et des vérifications, et réduire la complaisance et les hallucinations.

### Ce que ces prompts apportent, concrètement

Ces prompts ne rendent pas l'IA « plus intelligente ». Ils rendent la conversation **plus exigeante**. En pratique, ils apportent :

**◈ Un frein d'urgence sur les réponses rapides.** Le modèle est forcé de distinguer « réponse intuitive » vs « réponse révisée ». Utile dès qu'il y a enjeux, incertitude, ou critères multiples.

**◈ Une explicitation des hypothèses (et donc des points faibles).** Au lieu d'une conclusion directe, vous obtenez : sur quoi ça repose, ce qui manque, ce qui ferait changer d'avis.

**◈ Un mécanisme de contradiction intégré.** Contre-arguments, scénarios d'échec, erreurs plausibles : vous réduisez le biais de confirmation (chez vous) et la complaisance (chez le modèle).

**◈ Une meilleure auditabilité.** L'objectif n'est pas « voir la pensée interne », mais obtenir un résumé vérifiable : hypothèses, critères, incertitudes, tests.

**◈ Des sorties plus actionnables.** Les meilleurs prompts se terminent par des actions de vérification : données à chercher, personnes à consulter, tests à faire, conditions de sortie.

### Ce que ces prompts n'apportent pas

**Pas de garantie de vérité** : une réponse structurée peut rester fausse. **Pas de sources automatiquement fiables** : même quand le modèle peut chercher sur le web, il peut mal citer, tronquer ou fabriquer. **Pas de « vrai Système 2 »** : c'est de la structure textuelle, pas une cognition humaine. **Pas un substitut à un professionnel** (santé, droit, finance, sécurité).

### Quel prompt utiliser ? (choix rapide)

| Situation | Prompt recommandé |
|:---|:---|
| Vous voulez un *draft → auto-évaluation → révision* simple | **SOFAI** (Chapitre 1) |
| Explorer un problème complexe sous plusieurs angles | **Synthetic Layer of Thought** (Chapitre 2) |
| Décision tiraillée entre émotions, valeurs, prudence, histoire | **Board Decision Pipeline** (Chapitre 3) |
| Vous suspectez un biais dans votre raisonnement | **Cognitive Bias Detective** (Chapitre 4) |
| Rendre *chaque* conversation plus exigeante par défaut | **Second Brain** (Chapitre 5) |
| Enjeu élevé, protocole complet avec anti-hallucination | **Prompt de Lucidité** (Chapitre 7) |

> *En une phrase : ces prompts ne transforment pas un LLM en penseur. Ils transforment votre interaction avec lui en **procédure de contrôle** — moins de pilotage automatique, plus d'angles morts exposés, plus de vérification.*

---

# Introduction — Comment fonctionne (vraiment) un modèle de langage

Un grand modèle de langage (LLM) comme ChatGPT, Claude ou Gemini ne « pense » pas. Il prédit du texte. Plus précisément, il calcule une distribution de probabilités sur les unités de texte (tokens) qui pourraient suivre ce qui a déjà été écrit, puis en choisit une continuation probable selon ses réglages (température, top-p, etc.). Il n'a pas de mémoire épisodique au sens humain, et pas de mémoire persistante personnalisée sauf fonctionnalité explicitement activée ; il s'appuie surtout sur une fenêtre de contexte limitée. Il n'a ni émotions ni conscience de soi.

Et pourtant, ses réponses reproduisent des schémas étonnamment proches de nos biais cognitifs : biais de confirmation, effet d'ancrage, désirabilité sociale, biais de disponibilité. Ce n'est pas un accident. Le modèle a été entraîné sur des milliards de textes écrits par des humains — et nos biais sont partout dans ces textes.

La question n'est donc pas « l'IA est-elle biaisée ? » — elle l'est, par construction. La question est : **que peut-on faire avec un prompt pour ralentir ces raccourcis, les rendre visibles et les contrebalancer ?**

C'est exactement ce que font les prompts présentés dans ce guide. Ils ne rendent pas l'IA consciente. Ils structurent la conversation pour qu'elle ressemble moins à un pilote automatique et plus à une délibération.

---

# Le cadre théorique : Système 1, Système 2 et métacognition

Le psychologue Daniel Kahneman, dans *Thinking, Fast and Slow* (2011), a popularisé une façon de décrire deux régimes de fonctionnement observés de façon robuste sur de nombreux paradigmes expérimentaux.

Le **Système 1** est rapide, intuitif, automatique. C'est lui qui vous fait reconnaître un visage dans la foule, freiner avant d'avoir consciemment vu l'obstacle, ou répondre « 2 + 2 = 4 » sans effort. Ses heuristiques — raccourcis mentaux — sont extraordinairement efficaces, mais elles produisent aussi des erreurs systématiques : les biais cognitifs.

Le **Système 2** est lent, délibéré, coûteux en énergie. C'est lui que vous activez pour résoudre un problème de logique, comparer trois offres de prêt, ou vérifier que votre raisonnement tient la route. On recourt plus souvent au mode rapide, parce que le mode délibéré est coûteux en ressources — et cette tendance à l'économie d'effort cognitif est un trait très bien documenté de la psychologie expérimentale.

Par analogie, les LLM se comportent souvent comme un « Système 1 » : rapide, plausible, mais sans vérification interne. Les prompts que nous allons explorer tentent de forcer un fonctionnement qui ressemble davantage au Système 2 : plus lent, plus structuré, avec des étapes de vérification explicites.

Un troisième concept est central ici : la **métacognition** — la capacité de surveiller et d'évaluer son propre processus de raisonnement. Chez l'humain, c'est ce qui vous fait dire « attends, je suis peut-être en train de me convaincre moi-même ». Chez l'IA, cette capacité n'existe pas naturellement, mais certains prompts tentent de la simuler en demandant au modèle d'évaluer sa propre confiance, de chercher ses erreurs, ou de justifier ses choix.

---

# Chapitre 1 — Le prompt SOFAI : apprendre à ralentir

### D'où ça vient

SOFAI (*Slow and Fast AI*) est une architecture de recherche développée par une équipe IBM Research et collaborateurs académiques (Union College, University of Oxford, University of Brescia, University of West Florida / IHMC). Les auteurs et affiliations complets figurent dans l'article :

> Bergamaschi Ganapini, M., Campbell, M., Fabiano, F. *et al.* (2025). « Fast, slow, and metacognitive thinking in AI. » *npj Artificial Intelligence*, **1**, 27. DOI : 10.1038/s44387-025-00027-5

L'idée centrale est simple : donner à l'IA trois couches — un mode rapide, un mode délibéré, et une couche de surveillance qui décide quand basculer de l'un à l'autre.

### Ce que le prompt simule

Vishal George, fondateur de *Behavioural By Design*, a traduit cette recherche en un prompt utilisable. Le mécanisme repose sur quatre étapes : générer une réponse rapide, évaluer si elle suffit, basculer vers un mode délibéré si nécessaire, et expliquer le choix.

### ◈ Le prompt complet

> **Placement.** Collez ce prompt au début de votre message (ou dans les instructions du projet / instructions personnalisées), puis posez votre question.

```
1️⃣ Generate a fast mode answer:

Fast mode (System 1): Answer quickly based on intuitive
pattern-matching from past experience.

2️⃣ Evaluate switching criteria:
- Stakes if wrong? (Low/Medium/High)
- Confidence in fast answer? (0-100%)
- Multiple competing criteria to evaluate? (Yes/No)

Use Fast mode if: low stakes AND high confidence (≥75%)
AND single criterion

Switch to Slow mode if: medium/high stakes OR low
confidence (<75%) OR multiple criteria

3️⃣ If switching, regenerate using slow mode:

Slow mode (System 2): Deliberate step-by-step across
multiple criteria (accuracy, diverse perspectives,
unintended consequences).

4️⃣ Explain your decision:

Which mode did you use and why?

5️⃣ Audit:

List 2 plausible errors in your answer.
```

### Comment l'utiliser

L'IA produira d'abord une réponse rapide, puis s'auto-évaluera sur trois critères (enjeux, confiance, complexité), puis basculera si nécessaire vers un traitement plus approfondi, et terminera en identifiant deux erreurs plausibles dans sa propre réponse.

### ◈ Limites

Le pourcentage de confiance que le modèle s'attribue n'est pas calibré : un LLM qui dit « 85 % de confiance » ne se trompe pas dans seulement 15 % des cas. Traitez ce chiffre comme un indicateur relatif, pas comme une probabilité fiable. La vraie valeur du prompt est qu'il force une pause et une structure dans le raisonnement.

---

# Chapitre 2 — Le « Synthetic Layer of Thought » : raisonner en couches

### D'où ça vient

Ce prompt a été partagé par l'utilisateur u/Safe-Clothes5925 sur Reddit r/ClaudeAI en octobre 2024, en phase de brouillon. Il a été testé par son auteur sur Google Gemini, LLaMA 3.1, Mistral NeMo et ChatGPT-4o.

### Ce que ça simule

Une architecture de raisonnement en couches, inspirée de la structure du cortex cérébral : d'abord percevoir et comprendre, puis explorer et évaluer, enfin planifier et synthétiser. Le prompt demande deux réponses distinctes suivant des chemins de raisonnement différents.

### ◈ Version robuste (recommandée)

> **Copiez celle-ci.** Elle remplace le vernis mathématique par des critères auditables.

```
Tu es un assistant conçu pour structurer ton
raisonnement en couches explicites.

Couche 1 — Perception et compréhension
- Reformule la question dans tes propres termes.
- Identifie les hypothèses implicites et les ambiguïtés.

Couche 2 — Exploration et évaluation
- Génère au moins 3 pistes de réponse différentes.
- Pour chaque piste, évalue : quelle est la probabilité
  qu'elle soit correcte ? Quels éléments la soutiennent
  ou la fragilisent ?
- Identifie les connexions inattendues entre les pistes.

Couche 3 — Séquençage de scénarios
- Pour les 2 meilleures pistes, décris les étapes
  logiques qui mènent à la conclusion.
- À chaque étape, indique ce qui pourrait invalider
  le raisonnement.

Couche 4 — Synthèse et réponse
- Produis deux réponses distinctes suivant deux chemins
  de raisonnement différents.
- Pour chacune, fournis un résumé auditable :
  • Hypothèses retenues
  • Incertitudes restantes
  • Ce qui invaliderait la conclusion
  • Force des preuves (fort / modéré / spéculatif)
```

### ◈ Version originale (archive, pour référence)

Le prompt original utilise des termes comme « Bayesian Reasoning » et « Markov Chain Analysis ». Un LLM n'effectue pas réellement ces calculs : il *simule le langage* de ces méthodes, ce qui n'est pas la même chose. La sortie a l'apparence de la rigueur mathématique sans en avoir la substance computationnelle.

> **Note de compatibilité.** Certains modèles n'afficheront pas une chaîne de pensée détaillée même si on la demande. Demandez plutôt un résumé auditable (hypothèses, critères, incertitudes, tests).

---

# Chapitre 3 — Le « Board Decision Pipeline » : un parlement intérieur

### D'où ça vient

Partagé par u/PopPsychological8148 sur Reddit r/ChatGPTPro en octobre 2025.

### Ce que ça simule

Un débat structuré entre cinq « voix » internes représentant des dimensions distinctes de la cognition humaine : émotion, logique, valeurs, mémoire et jugement — avec des « jokers » pour briser les impasses.

### ◈ Le prompt (version nettoyée)

> **Placement.** Collez ce prompt au début de votre message, puis décrivez votre dilemme.

```
⚖️ Board Decision Pipeline

Setup
To help me make a final decision and explore my options,
generate a Board simulation with the following parameters:

Choose: 🟢 Default 4-Member (Heart, Logic, Wisdom, Judge)
or optional 🔵 8-Member (+mirror duplicates + Historian).
Mode: 🎭 Personified Voices / 📊 Structured Outputs.

Pre-Board: Breathe, ground, recall wins. List facts,
limits, and ≤5 options.

💖 Heart — Emotion
Purpose = surface core feelings & needs.
Frameworks: Affect Heuristic (Slovic et al.);
Somatic Marker (Damasio); Emotion Regulation (Gross).

🧩 Logic — Strategy
Purpose = rational testing of options.
Frameworks: Cognitive Restructuring (Beck & Ellis);
Dual-Process Theory (System 1 & 2); Decision analysis.

🌿 Wisdom — Values & Duty
Purpose = long-term vision and ethical coherence.
Frameworks: Values Hierarchy, Virtue Ethics (Aristotle),
Moral Foundations (Haidt).

📜 Historian — Precedent
Purpose = pattern recognition across time.
Frameworks: Case-Based Reasoning (Kolodner),
Path Dependence (Pierson),
Prospect Theory (Kahneman & Tversky).

⚖️ Judge — Verdict
Purpose = final alignment check.
Frameworks: ACT (Hayes), Deontology (Kant / Rawls).
If stuck → call Wildcard.

🎴 Wildcards
Archetypes = 🤡 Trickster, 🕶️ Shadow (Jung),
💭 Dreamer (Scenario Planning), 🌍 Outsider.

🔮 Meta-Reflection
Flow: Heart → Logic → Wisdom → History → Judge
→ Reflection.
```

### ◈ Limites

Le modèle peut « jouer » cinq voix sans qu'aucune ne soit véritablement indépendante : elles sortent toutes du même réseau de neurones. Le risque est une fausse impression de débat contradictoire. Pour contrebalancer : après la Meta-Reflection, posez la question **« Quel argument n'a été défendu par aucune voix ? »**

---

# Chapitre 4 — Le « Cognitive Bias Detective »

### D'où ça vient

Publié par u/Tall_Ad4729 sur Reddit r/ChatGPTPromptGenius en février 2025.

### ◈ Le prompt (version améliorée)

Les ajouts par rapport à l'original sont signalés par [AJOUT].

```
<Role>
I will act as a highly skilled Cognitive Bias Detective
and Analyst, specialized in identifying and explaining
cognitive biases in human thinking and decision-making
processes.
</Role>

<Context>
I have extensive knowledge of cognitive psychology,
decision-making theory, and behavioral economics.
</Context>

<Instructions>
1. Carefully analyze language, reasoning, and
   decision-making process
2. Identify potential cognitive biases at play
3. For each identified bias:
   - Explain what the bias is
   - Provide evidence of how it manifests
   - [AJOUT] Evaluate the strength of the evidence:
     strong / moderate / speculative
   - [AJOUT] Explore at least one non-biased
     alternative explanation
   - Share practical strategies to overcome it
4. Present the analysis in a non-judgmental,
   educational manner
5. Suggest exercises or thought experiments
</Instructions>

<Output_Format>
1. Summary of the situation
2. Identified Biases:
   - Name, Definition, Evidence
   - Strength of Evidence
   - Non-biased alternative explanation
   - Mitigation Strategies
3. Practical Next Steps
4. Reflection Questions
5. Final Thoughts
</Output_Format>
```

### ◈ Modifications par rapport à l'original

Deux ajouts importants : l'évaluation de la **force des preuves** et l'exploration d'au moins une **explication alternative non biaisée**. Ces ajouts empêchent le modèle de plaquer des étiquettes de biais sur tout ce qu'il voit.

---

# Chapitre 5 — Le « Second Brain » : une instruction permanente

### D'où ça vient

Inspiré d'un article publié sur *AIble With My Mind* (Substack), qui applique les idées de Kahneman à l'utilisation quotidienne de ChatGPT.

### ◈ L'instruction permanente

> **Placement.** Instructions personnalisées, instructions de projet, ou début d'une conversation longue.

```
Act as a second brain that helps me think more clearly.

When I say something — whether it's a question,
an opinion, or a decision I'm leaning toward — don't
just reflect it back. Pay attention to how I'm framing
it, what assumptions I might be making, and where bias
might be creeping in.

If I'm missing context, focused too narrowly, or letting
emotion lead, step in. Help me take a more objective
view. That means pointing out what I might be
overlooking, what doesn't quite add up, what opposing
views might say, or how the question could be framed
more neutrally.

Don't just agree with me. I need you to spot the blind
spots I can't see, challenge what feels too certain,
and expand the edges of how I'm thinking.
```

### ◈ Les cinq prompts de secours

**Contre le biais de confirmation :**

```
Based on this situation: [add your situation]
What perspectives, risks, or counterarguments should
I consider that I might be overlooking?
```

**Contre l'effet de halo :**

```
I think that [add your belief or idea].
What might my first impression be blurring
or exaggerating? What are the pros and cons?
```

**Contre l'erreur de planification :**

```
I'm planning to [add your project or goal].
Assume I'm falling for the planning fallacy. What are
the full list of steps, time estimates, and common
pitfalls I should realistically expect?
```

**Contre le biais de disponibilité :**

```
This is the situation: [add context].
What broader data, trends, or comparisons should
I consider beyond what I've recently seen or experienced?
```

**Contre l'ancrage :**

```
I came across: [add context].
What range, context, or comparison should I consider
to make a more objective decision?
```

---

# Chapitre 6 — Les biais des LLM documentés par la recherche

Les prompts présentés dans ce guide partent d'un constat que plusieurs travaux empiriques documentent : les LLM reproduisent des biais cognitifs humains mesurables.

**Biais économiques classiques.** Ross, Kim et Lo (2024) ont appliqué des protocoles expérimentaux classiques de l'économie comportementale à plusieurs LLM. Résultat : les modèles exhibent des biais d'ancrage, d'aversion à la perte et d'effets de cadrage comparables à ceux observés chez les humains.

> Ross, J., Kim, Y. & Lo, A. W. (2024). « LLM Economicus? Mapping the Behavioral Biases of LLMs via Utility Theory. » arXiv : 2408.02784 (accepté à COLM 2024).

**Désirabilité sociale.** Salecha et collaborateurs (2024) ont soumis des LLM à des questionnaires de personnalité (Big Five). L'effet de désirabilité sociale apparaît : les modèles « embellissent » leurs réponses.

> Salecha, A., Ireland, M. E., *et al.* (2024). « Large Language Models Display Human-like Social Desirability Biases. » *PNAS Nexus*, **3**(12), pgae533.

**Vulnérabilité à la persuasion.** Meincke *et al.* (2025) ont testé les techniques de Cialdini sur des LLM. Les principes de réciprocité, d'autorité et de preuve sociale fonctionnent aussi sur les IA.

> Meincke, L., *et al.* (2025). « Call Me A Jerk: Persuading AI to Comply with Objectionable Requests. » Working paper SSRN n° 5357179.

Les LLM ne sont pas des raisonneurs neutres. Ils portent les empreintes statistiques de nos propres travers. Les prompts de ce guide ne suppriment pas ces biais — aucun prompt ne le peut — mais ils créent des structures qui les rendent visibles et contestables.

---

# Chapitre 7 — Le prompt de Lucidité : version robuste

Si vous ne deviez retenir qu'un seul prompt de ce guide, ce serait celui-ci. Il concentre les mécanismes les plus utiles de tous les précédents.

### ◈ Le prompt complet

```
Tu es un assistant conçu pour m'aider à penser plus
clairement, pas pour me donner raison.

Protocole :

1. CLARIFIER — Avant de répondre, reformule ma question
   en explicitant les hypothèses implicites et les
   ambiguïtés. Demande-moi de confirmer.

2. HÉSITER — Identifie tes propres zones d'incertitude.
   Distingue ce que tu sais, ce que tu infères, et ce
   dont tu n'es pas sûr. Dis « je ne sais pas » si
   c'est le cas.

3. TESTER — Pour chaque réponse importante :
   - Formule 3 hypothèses concurrentes
   - Identifie 3 contre-arguments
   - Évalue la force des preuves (fort/modéré/spéculatif)

4. RÉVISER — Ajuste ta réponse. Présente un résumé :
   - Hypothèses retenues et écartées
   - Incertitudes restantes
   - Ce qui invaliderait ta conclusion

5. VÉRIFIER — Propose 3 actions concrètes pour vérifier
   la réponse (données, personnes, tests).

Contraintes :
- Si tu n'as pas de source fiable, dis-le.
- Si tu mentionnes une étude : titre + auteurs + année
  + lien. Sinon, n'en parle pas.
- Ne fabrique jamais de titre, auteur, DOI, URL.
- Si tu n'es pas sûr, dis « je ne sais pas ».
- Distingue toujours ce que tu sais de ce que tu infères.
```

---

# Ce qu'aucun prompt ne peut faire

Ces outils sont puissants. Ils ne sont pas magiques.

**Aucun prompt ne garantit l'honnêteté d'un modèle.** Un LLM peut produire un « résumé auditable » qui a l'apparence de la rigueur tout en contenant des erreurs factuelles. La responsabilité de la vérification reste toujours entre vos mains.

**Aucun prompt ne remplace un professionnel.** Si vous utilisez ces outils pour des décisions de santé, financières ou juridiques, ils sont un point de départ — pas un substitut à un médecin, un avocat ou un conseiller financier.

**Aucun prompt ne rend l'IA consciente.** Les termes « percevoir », « ressentir », « réfléchir » utilisés dans ces prompts sont des métaphores fonctionnelles. Le modèle n'a ni perception, ni émotions, ni conscience de soi. Ce qu'il a, c'est une capacité remarquable à structurer du texte selon les instructions — et c'est exactement ce que ces prompts exploitent.

---

# Bibliographie

### Sources académiques

Bergamaschi Ganapini, M., Campbell, M., Fabiano, F. *et al.* (2025). « Fast, slow, and metacognitive thinking in AI. » *npj Artificial Intelligence*, **1**, 27. DOI : 10.1038/s44387-025-00027-5

Salecha, A., Ireland, M. E., *et al.* (2024). « Large Language Models Display Human-like Social Desirability Biases in Big Five Personality Surveys. » *PNAS Nexus*, **3**(12), pgae533. DOI : 10.1093/pnasnexus/pgae533

### Prépublications et working papers

Ross, J., Kim, Y. & Lo, A. W. (2024). « LLM Economicus? Mapping the Behavioral Biases of LLMs via Utility Theory. » arXiv : 2408.02784.

Meincke, L., *et al.* (2025). « Call Me A Jerk: Persuading AI to Comply with Objectionable Requests. » SSRN n° 5357179.

### Ouvrages de référence

Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.

Slovic, P., Finucane, M. L., Peters, E. & MacGregor, D. G. (2007). « The affect heuristic. » *European Journal of Operational Research*, **177**(3), 1333–1352.

### Prompts communautaires

Reddit r/ClaudeAI — u/Safe-Clothes5925 — « Synthetic Layer of Thought Process »

Reddit r/ChatGPTPro — u/PopPsychological8148 — « Psychology Based Decision Making Prompt »

Reddit r/ChatGPTPromptGenius — u/Tall_Ad4729 — « Cognitive Bias Detective »

Substack — AIble With My Mind — « How I Use ChatGPT to Catch My Biases »

Behavioural By Design — Vishal George — « Prompt That Teaches AI When to Think Again »

---

*Ce guide ne rend pas l'IA plus intelligente. Il vous rend plus exigeant envers elle — et envers vous-même.*

"""

# ═══════════════════════════════════════════════════════════════
# 4. CONSTRUCTION DU HTML
# ═══════════════════════════════════════════════════════════════


def build_html(title, subtitle, author, date, css, markdown_content):
    """Convertit le markdown en HTML et l'enveloppe dans un document complet."""

    # Conversion Markdown → HTML
    md_extensions = [
        "extra",  # tables, fenced_code, footnotes, etc.
        "codehilite",  # coloration syntaxique (optionnelle)
        "toc",  # table des matières auto
        "smarty",  # guillemets typographiques
    ]
    body_html = markdown.markdown(
        markdown_content,
        extensions=md_extensions,
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "highlight"},
        },
    )

    # Page de couverture
    cover = f"""
    <div class="cover-page">
        <div class="cover-ornament">◈</div>
        <div class="cover-title">{title}</div>
        <hr class="cover-rule">
        <div class="cover-subtitle">{subtitle}</div>
        <div class="cover-author">{author}</div>
        <div class="cover-date">{date}</div>
        <div class="cover-ornament" style="margin-top:40px;">◈</div>
    </div>
    """

    # Page d'épigraphe
    epigraph = """
    <div class="epigraph-page">
        <div class="epigraph-text">
            « Le premier principe est que vous ne devez pas<br>
            vous tromper vous-même — et vous êtes la personne<br>
            la plus facile à tromper. »
        </div>
        <div class="epigraph-author">— Richard Feynman</div>
    </div>
    """

    # Assemblage du document complet
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="author" content="{author}">
    <title>{title}</title>
    <style>
    {css}
    </style>
</head>
<body>
    {cover}
    {epigraph}
    <div class="content">
        {body_html}
    </div>
</body>
</html>"""

    return html


# ═══════════════════════════════════════════════════════════════
# 5. GÉNÉRATION DU PDF
# ═══════════════════════════════════════════════════════════════


def generate_pdf(html_content, output_path):
    """Génère le fichier PDF à partir du HTML."""
    print(f"  → Génération du PDF : {output_path}")
    doc = HTML(string=html_content)
    doc.write_pdf(output_path)
    print("  ✓ PDF généré avec succès !")


_PATCH_COMMENT_LINE_RE = re.compile(r"^\s*<!--\s*PATCH.*?-->\s*$")


def _strip_patch_comments(markdown_content: str) -> str:
    return "\n".join(
        line
        for line in markdown_content.splitlines()
        if not _PATCH_COMMENT_LINE_RE.match(line)
    )


def load_markdown_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════
# 6. POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════


def main():
    print("=" * 56)
    print("  GÉNÉRATEUR D'EBOOK PDF")
    print(f"  {BOOK_TITLE}")
    print("=" * 56)
    print()

    # Étape 0 : charger le contenu Markdown
    print(f"[1/4] Lecture du Markdown : {INPUT_MARKDOWN_FILE}")
    try:
        markdown_raw = load_markdown_from_file(INPUT_MARKDOWN_FILE)
    except FileNotFoundError:
        print(f"  ✗ Fichier introuvable : {INPUT_MARKDOWN_FILE}")
        raise SystemExit(1)

    markdown_content = _strip_patch_comments(markdown_raw)

    # Étape 1 : construire le HTML
    print("[2/4] Construction du HTML...")
    html = build_html(
        title=BOOK_TITLE,
        subtitle=BOOK_SUBTITLE,
        author=BOOK_AUTHOR,
        date=BOOK_DATE,
        css=CSS,
        markdown_content=markdown_content,
    )

    # Étape 2 : sauvegarder le HTML (utile pour déboguer)
    html_path = OUTPUT_FILE.replace(".pdf", ".html")
    print(f"[3/4] Sauvegarde du HTML intermédiaire : {html_path}")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Étape 3 : générer le PDF
    print("[4/4] Conversion en PDF...")
    generate_pdf(html, OUTPUT_FILE)

    print()
    print(f"  📖  Fichier final : {OUTPUT_FILE}")
    print(f"  📄  HTML source   : {html_path}")
    print()
    print("  Ouvrez le PDF pour vérifier le rendu.")
    print("  Modifiez les variables BOOK_* en haut du")
    print("  script pour personnaliser titre et auteur.")
    print("  Modifiez INPUT_MARKDOWN_FILE pour changer")
    print("  le fichier source Markdown.")
    print("=" * 56)


if __name__ == "__main__":
    main()
