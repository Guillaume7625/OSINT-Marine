# Cycle Outlook

Application locale de tri Outlook 2016 (COM/MAPI) avec règles locales prioritaires, option GENIAL configurable et résumé quotidien.

## Prérequis
- Windows
- Outlook 2016 desktop installé et configuré
- Python 3.10+
- Accès COM via `pywin32`

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Installation automatique (PowerShell)
```powershell
.\install.ps1
```
Optionnel pour lancer les tests:
```powershell
.\install.ps1 -RunTests
```

## Lancer l'UI
```bash
python -m app.webapp
```
Ouvrir `http://127.0.0.1:5000`.

## Lancer un job batch
```bash
python -m app.run_job --limit 50 --days 7 --dry-run true
```
Passer `--dry-run false` pour déplacer réellement les emails.

## Planification (Task Scheduler)
Créer une tâche Windows qui exécute :
```
C:\path\to\python.exe -m app.run_job --limit 50 --days 7 --dry-run false
```

## Sécurité UI
Dans `config.yaml` (copier `config.yaml.example`):
```
ui:
  require_token: true
  token: "local-dev-token"
```
Le token est attendu via `?token=...` ou l'entête `X-Auth-Token` pour `/logs`, `/genial`, et `/trier` si `dry_run=false`.

## GENIAL
Configurer via `/genial`. La configuration est stockée en SQLite. L'accès réseau est bloqué hors allowlist host:port.
Les redirections HTTP sont refusées et `requests` ignore les variables d'environnement proxy.

## Règles préchargées
Un exemple de règles est fourni dans `rules_seed.json` et est inséré automatiquement si la base est vide.
Vous pouvez modifier ce fichier avant le premier lancement.

## Dossiers Outlook
Les emails sont déplacés dans :
- `Inbox\Crises`
- `Inbox\Décisions`
- `Inbox\À lire`
Les dossiers sont créés s'ils n'existent pas.

## Résumé quotidien
`/resume` génère un Markdown, sauvegardé localement dans `data/YYYY-MM-DD.md`.
Option : ajouter `?draft=1` pour créer un brouillon Outlook “Résumé Cycle” (ou `?draft=1&folder=Résumé` pour déposer dans `Inbox\Résumé`).

## Logs & audit
Logs JSON append-only dans `data/logs/audit.jsonl` + table SQLite.
Chaque run a un `run_id` corrélé aux messages.

## Limites
- Pas de tests Outlook (COM) en CI.
- Dépend de la configuration locale d'Outlook.

## Dépannage COM
- Redémarrer Outlook.
- Vérifier que le profil par défaut est valide.
- Lancer l'app depuis une session utilisateur interactive.

## Guide d'extension
Voir `EXTENSION_GUIDE.md` pour la structure, les points d'extension et les conventions.
