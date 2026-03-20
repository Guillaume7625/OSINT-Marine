# Protocoles de defense cognitive
<!-- PATCH 2.1 : H1 ajouté -->

## A propos de ce guide

<!-- PATCH 2.3 : encadré statut + OPSEC données -->
**Statut** : document non officiel, non endosse par l'OTAN ni par une autorite nationale. Il s'agit d'une compilation analytique a vocation pedagogique.

**Donnees** : ne saisissez pas d'informations classifiees, personnelles, ou operationnellement sensibles dans un systeme IA non explicitement autorise. Appliquez anonymisation et OPSEC en toutes circonstances.

<!-- PATCH 2.2 : remplacement "certifiée" -->
**Version finale -- auditabilite documentee (sources et limites explicites) -- 2026-02-08**

Dans l'ere de l'information, la dimension cognitive de nos societes est devenue un champ de bataille. Comme l'identifie le NATO Defense College (Paquet, 2022), "la cognition est une dimension globale qui englobe toutes les activites humaines, et la guerre cognitive est une maniere insidieuse de saper les democraties liberales". Face a cette menace, ce guide propose des outils operationnels de defense cognitive bases sur la structuration du raisonnement.

Ce guide repertorie et analyse six protocoles (prompts) qui forcent un ralentissement delibere, une explicitation des hypotheses et une recherche active des erreurs -- en s'inspirant des travaux sur les biais cognitifs humains. Chaque protocole est cite en entier et evalue selon quatre criteres : la qualite de clarification, la presence de contre-arguments, la separation faits/inferences, et la capacite a proposer des verifications concretes.

**Public cible** : Decideurs militaires et civils, analystes du renseignement, planificateurs operationnels, responsables de formation en defense cognitive, et toute personne confrontee a un environnement informationnel hostile.

**L'objectif** n'est pas de rendre l'IA plus intelligente, mais de transformer vos echanges avec elle en exercices de resilience cognitive -- transposables ensuite aux situations de decision reelle sous pression informationnelle.

**Temps de lecture** : 35 minutes. Temps pour tester votre premier protocole : 5 minutes.

**Note de securite operationnelle**. Plusieurs protocoles vous invitent a decrire des situations, dilemmes ou hypotheses. Avant de saisir quoi que ce soit dans un systeme IA, classifiez l'information et anonymisez toute donnee sensible : noms, lieux, capacites, effectifs, chronologie precise. Aucun protocole ne justifie une compromission OPSEC.

**Avertissement -- manipulation de prompts**. Si vous utilisez un protocole partage en ligne, relisez-le integralement avant usage. Des adversaires peuvent inserer des instructions malveillantes (exfiltration de donnees, contournement de garde-fous). Une lecture attentive de 30 secondes suffit a detecter les anomalies flagrantes.

---

## Note methodologique et limites

### Statut epistemique de ce guide

Ce guide combine des sources de niveaux de fiabilite differents, classees selon une echelle de tracabilite a quatre niveaux (T1 a T4) definie ci-dessous.

**T1 -- Recherche academique validee par comite de lecture** : articles publies dans des revues a comite de lecture, ouvrages de reference a fort impact. Exemples : Kahneman (2011), Salecha et al. (2024, PNAS Nexus), Bergamaschi Ganapini et al. (2025, npj Artificial Intelligence).

**T2 -- Documents institutionnels et working papers** : rapports d'organisations reconnues (OTAN, RAND, ministeres de la Defense), prepublications deposees sur des serveurs reconnus (arXiv, SSRN). Exemples : Paquet (2022, NATO Defense College), Waltzman (2017, RAND), Ross et al. (2024, arXiv / OpenReview COLM 2024).

**T3 -- Sources citees mais non localisees en source primaire** : documents dont l'existence est confirmee par des citations multiples dans la litterature mais dont le texte integral n'a pas pu etre audite directement. Exemple : Cole et Le Guyader (2020).

**T4 -- Protocoles communautaires (usage exploratoire)** : heuristiques partagees sur des plateformes communautaires (Reddit, Substack), non evaluees par comite de lecture. Utilisees ici comme base exploratoire, a tester empiriquement avant tout deploiement operationnel.

<!-- PATCH 3.4 : critères minimaux d'inclusion T4 -->
**Criteres minimaux d'inclusion T4.** Un protocole communautaire n'est inclus dans ce guide que s'il satisfait trois conditions : (1) securite -- le prompt ne contient aucune instruction d'exfiltration de donnees, de contournement de garde-fous (jailbreak), ni de collecte d'informations personnelles ; (2) stabilite -- la version utilisee est datee et archivee (copie locale ou capture horodatee) ; (3) test interne -- le protocole a ete teste sur au moins 10 cas anonymises, revu par au moins un pair, et les echecs observes ont ete consignes.

### Ce qui EST valide scientifiquement

Les LLM reproduisent des biais cognitifs humains mesurables (Ross et al. 2024, Salecha et al. 2024, Meincke et al. 2025).

<!-- PATCH 3.1 : correction "Nature" → "Nature Portfolio / npj Artificial Intelligence" -->
L'architecture SOFAI (Systeme 1/2 artificiel) repose sur un article **Nature Portfolio** publie dans *npj Artificial Intelligence* (Bergamaschi Ganapini et al. 2025).

Le cadre theorique Systeme 1/Systeme 2 est robuste (Kahneman 2011, plus de 10 000 citations).

La guerre cognitive exploite les biais humains (Paquet 2022, Waltzman 2017, documents NATO StratCom CoE).

### Ce qui N'EST PAS (encore) valide empiriquement

L'efficacite operationnelle des six protocoles specifiques proposes dans ce guide n'a pas ete mesuree.

Les gains quantitatifs precis (temps, qualite de decision) en contexte militaire reel ne sont pas documentes.

La transferabilite des competences (exercice IA vers decision reelle sans IA) n'a pas ete testee.

### Recommandation

Ces protocoles constituent des **outils exploratoires** a tester empiriquement avant deploiement institutionnel. La Phase 2 du protocole d'entrainement (Chapitre 8) propose une methodologie experimentale pour mesurer leur efficacite reelle.

---

<!-- PATCH 4 : section "Modes d'échec fréquents" insérée ici -->
## Modes d'echec frequents (Failure modes)

Cette section recense les principaux modes d'echec observes lors de l'utilisation de protocoles de structuration cognitive avec des LLM. Les reconnaitre avant usage reduit le risque de fausse assurance.

**Sur-structuration.** Le protocole impose tellement d'etapes que l'utilisateur confond "avoir suivi la procedure" avec "avoir bien raisonne". Le format structure devient un substitut a la pensee plutot qu'un support. Contremesure : apres chaque utilisation, se demander "ai-je appris quelque chose que je ne savais pas avant, ou ai-je simplement rempli des cases ?".

**Fausse contradiction.** Le modele genere des contre-arguments formellement presentes comme tels, mais qui sont faibles, hors sujet ou construits pour etre facilement refutes (homme de paille involontaire). L'utilisateur a l'impression d'avoir "teste" sa these alors que les objections etaient superficielles. Contremesure : demander explicitement "quel est le contre-argument le plus fort qu'un expert hostile pourrait formuler ?" et evaluer si la reponse ferait reellement changer d'avis.

**Sur-confiance calibree.** Le modele produit des etiquettes de confiance (70 %, "modere", "speculatif") qui donnent une apparence de calibration sans reposer sur un calcul statistique reel. L'utilisateur ancre ses decisions sur ces chiffres. Contremesure : traiter les niveaux de confiance du LLM comme des indicateurs ordinaux (plus ou moins incertain), jamais comme des probabilites cardinales.

**Goodharting du protocole.** Lorsqu'un protocole est utilise de facon repetee, le modele apprend (dans le contexte de la conversation) a produire le format attendu avec un minimum d'effort cognitif -- l'equivalent d'un eleve qui remplit un formulaire sans reflechir. Contremesure : varier les formulations, ajouter periodiquement des questions inattendues ("quel element de ta reponse est le plus fragile et pourquoi ?"), et ne pas utiliser le meme protocole plus de trois fois de suite sans reformulation.

**Biais induit par le prompt.** Le protocole lui-meme peut contenir des hypotheses implicites qui orientent la reponse. Par exemple, un prompt qui demande "identifie 3 menaces" presuppose qu'il y en a au moins trois, et le modele en inventera si necessaire. Contremesure : formuler les demandes de facon ouverte ("y a-t-il des menaces ? si oui, lesquelles ?") et verifier que les elements identifies ne sont pas des artefacts du format demande.

**Verifications non realisees.** Le protocole propose des "actions de verification" en fin de sortie -- mais l'utilisateur les traite comme un ornement textuel plutot que comme des taches a executer. Contremesure : considerer les verifications comme la partie la plus importante de la sortie. Si aucune verification n'est effectuee, la sortie du protocole n'a pas plus de valeur qu'une reponse non structuree.

---

## Resume executif -- Pourquoi ces protocoles existent et ce qu'ils changent

### Le probleme : vitesse, surcharge, manipulation

Dans l'environnement informationnel moderne, le combattant et le decideur sont confrontes a un flux "many-to-many" incontrolable -- rapide, non filtre, melant fait et opinion, revelations authentiques et fuites organisees. Comme le souligne Paquet : "Cette egalisation du pouvoir par Internet, donnant une voix a chacun, a mene a une crise de l'ethos et de la confiance, avec un poids croissant du pathos, creant un terreau favorable aux conflits hybrides d'aujourd'hui."

Le psychologue Daniel Kahneman distingue deux modes de fonctionnement cognitif. Le **Systeme 1** est rapide, intuitif, efficace, mais producteur d'erreurs systematiques (biais cognitifs). Le **Systeme 2** est lent, delibere, rigoureux, mais couteux en ressources et rarement sollicite.

Sous pression informationnelle, nous basculons vers le Systeme 1 -- et les adversaires l'exploitent. Comme l'identifie le NATO Defense College : "Le rythme de reception de l'information encouragera le 'thinking fast' (reflexif, emotionnel) par opposition au 'thinking slow' (rationnel, judicieux), rendant ainsi le combattant plus sensible aux biais cognitifs."

Par analogie, un grand modele de langage (LLM) se comporte souvent comme un "Systeme 1 artificiel" : il produit vite un texte plausible sans verification interne. Resultat : il peut etre convaincant meme quand il a tort, et il reproduit nos propres biais cognitifs (ancrage, confirmation, disponibilite) car il a ete entraine sur nos textes.

**Ces protocoles partent d'un constat** : on ne peut pas supprimer les biais d'un LLM avec une instruction, mais on peut structurer l'echange pour ralentir les reponses quand il le faut, rendre visibles les hypotheses et angles morts, exiger des tests et des verifications, et reduire la complaisance et les hallucinations.

### Ce que ces protocoles apportent, concretement

Ces protocoles ne rendent pas l'IA "plus intelligente". Ils rendent la conversation plus exigeante -- et vous entrainent a une posture de defense cognitive transposable aux situations reelles.

En pratique, ils apportent un **frein d'urgence sur les reponses rapides** (le modele est force de distinguer "reponse intuitive" contre "reponse revisee", utile des qu'il y a enjeux, incertitude, ou criteres multiples), une **explicitation des hypotheses** et donc des points faibles (au lieu d'une conclusion directe, vous obtenez : sur quoi ca repose, ce qui manque, ce qui ferait changer d'avis), un **mecanisme de contradiction integre** (contre-arguments, scenarios d'echec, erreurs plausibles -- vous reduisez le biais de confirmation chez vous et la complaisance chez le modele), une **meilleure auditabilite** (l'objectif n'est pas "voir la pensee interne" mais obtenir un resume verifiable : hypotheses, criteres, incertitudes, tests), et des **sorties actionnables** (les meilleurs protocoles se terminent par des actions de verification : donnees a chercher, sources a consulter, tests a faire, conditions de sortie).

<!-- PATCH 7.1 : tableau "Applications" remplacé par liste A5-safe -->
### Applications en contexte de defense cognitive

**Analyse de renseignement sous incertitude.** Protocole recommande : SOFAI (Chapitre 1). Mecanisme : force l'evaluation des enjeux et du niveau de confiance avant toute conclusion.

**Planification operationnelle multi-criteres.** Protocole recommande : Synthetic Layer of Thought (Chapitre 2). Mecanisme : explore des scenarios concurrents et identifie les points d'invalidation.

**Decision strategique impliquant valeurs et risques.** Protocole recommande : Board Decision Pipeline (Chapitre 3). Mecanisme : simule un debat contradictoire interne entre plusieurs dimensions (emotion, logique, valeurs, precedents, jugement).

**Detection de manipulation narrative.** Protocole recommande : Cognitive Bias Detective (Chapitre 4). Mecanisme : identifie les leviers rhetoriques (ethos, logos, pathos) et les biais exploites.

**Formation continue a la pensee critique.** Protocole recommande : Second Brain (Chapitre 5). Mecanisme : challenge systematique des hypotheses implicites dans chaque echange.

**Decision sous pression avec risque eleve.** Protocole recommande : Prompt de Lucidite (Chapitre 7). Mecanisme : protocole anti-hallucination avec verifications obligatoires.

### Ce que ces protocoles n'apportent pas

**Pas de garantie de verite** : une reponse structuree peut rester fausse. **Pas de sources automatiquement fiables** : meme quand le modele peut chercher sur le web, il peut mal citer, tronquer ou fabriquer. **Pas de "vrai Systeme 2"** : c'est de la structure textuelle, pas une cognition humaine. **Pas un substitut a l'expertise humaine** : ces outils completent, ils ne remplacent pas le jugement d'un analyste ou d'un commandant experimente.

**En une phrase** : ces protocoles ne transforment pas un LLM en penseur. Ils transforment votre interaction avec lui en exercice de resilience cognitive -- moins de pilotage automatique, plus d'angles morts exposes, plus de verification. Et cette discipline mentale se transfere aux situations de decision reelle.

---

## Introduction -- Guerre cognitive et modeles de langage : deux faces d'un meme defi

### La guerre cognitive : cibler l'esprit humain

Le concept de guerre cognitive, tel que defini par le NATO Defense College, va au-dela de la guerre psychologique ou informationnelle traditionnelle. Il designe l'usage systematique des technologies de l'information (big data, intelligence artificielle, machine learning) pour **alterer la cognition, la perception et le jugement des cibles humaines**.

Comme l'ecrit Paquet : "Cette guerre cognitive peut etre limitee dans le temps, ou se derouler sur une tres longue periode (par exemple, la guerre cognitive de l'APL contre Taiwan). Cela entraine de nouveaux risques pour la societe en general, et plus specifiquement pour le militaire."

Trois risques majeurs sont identifies. Premierement, la **qualite decisionnelle est compromise** : la surcharge informationnelle favorise le "thinking fast" (Systeme 1), rendant les decideurs plus sensibles aux biais de recence, de confirmation et de correlation illusoire. Deuxiemement, la **resilience du C2 est fragilisee** : le combattant devient plus "homo connectus" et moins "sapiens" (discernant, sage), avec une dependance accrue aux systemes augmentes -- posant la question de l'autonomie en cas de defaillance. Troisiemement, le **moral et la resilience psychologique sont sapes** : le combattant est au coeur d'une bataille narrative (logos), sous attaques cognitives qui peuvent instiller le doute sur la legitimite de la guerre, la fiabilite du gouvernement (ethos), et la culpabilite d'avoir laisse sa famille (pathos).

### Les LLM : des adversaires cognitifs par construction

Un grand modele de langage ne "pense" pas. Il predit du texte en calculant des probabilites de continuation. Il n'a ni memoire episodique au sens humain, ni conscience de soi, ni emotions.

Et pourtant, ses reponses reproduisent des schemas etonnamment proches de nos biais cognitifs. Ce n'est pas un accident : le modele a ete entraine sur des milliards de textes ecrits par des humains -- et nos biais sont partout dans ces textes.

La recherche recente le documente. **Ross, Kim et Lo (2024)** ont applique des protocoles experimentaux d'economie comportementale a plusieurs LLM. Resultat : les modeles exhibent des biais d'ancrage, d'aversion a la perte et d'effets de cadrage comparables a ceux observes chez les humains. **Salecha et al. (2024)** ont soumis des LLM a des questionnaires de personnalite (Big Five). L'effet de desirabilite sociale apparait : les modeles "embellissent" leurs reponses. **Meincke et al. (2025)** ont teste les techniques de persuasion de Cialdini sur des LLM. Les principes de reciprocite, d'autorite et de preuve sociale fonctionnent aussi sur les IA.

**Consequence strategique** : les adversaires peuvent entrainer des LLM offensifs qui exploitent systematiquement ces biais pour manipuler analystes, decideurs et combattants. La maitrise de protocoles de defense cognitive devient une competence operationnelle.

### Le cadre theorique : Systeme 1, Systeme 2 et metacognition

Le psychologue Daniel Kahneman, dans *Thinking, Fast and Slow* (2011), decrit deux regimes de fonctionnement cognitif observes de facon robuste sur de nombreux paradigmes experimentaux. Le **Systeme 1** est rapide, intuitif, automatique ; il excelle en reconnaissance de patterns et traitement emotionnel, il est econome en ressources, mais il est producteur de biais cognitifs. Le **Systeme 2** est lent, delibere, couteux ; il excelle en resolution de problemes et analyse rationnelle, il est gourmand en energie, mais il dispose d'une capacite de correction.

Par analogie, les LLM se comportent souvent comme un "Systeme 1" : rapide, plausible, mais sans verification interne. **Les protocoles de ce guide tentent de forcer un fonctionnement qui ressemble davantage au Systeme 2** : plus lent, plus structure, avec des etapes de verification explicites.

Un troisieme concept est central : la **metacognition** -- la capacite de surveiller et d'evaluer son propre processus de raisonnement. Chez l'humain, c'est ce qui vous fait dire "attends, je suis peut-etre en train de me convaincre moi-meme". Chez l'IA, cette capacite n'existe pas naturellement, mais certains protocoles tentent de la simuler en demandant au modele d'evaluer sa propre confiance, de chercher ses erreurs, ou de justifier ses choix.

**Application militaire** : comme le recommande le NATO Defense College, "il faut ameliorer les competences en metacognition et developper la pensee critique -- c'est-a-dire la capacite de de-biaiser notre facon de penser". Ces protocoles constituent des exercices concrets pour cette formation.

---

## Chapitre 1 -- Le protocole SOFAI : apprendre a ralentir

### D'ou ca vient

SOFAI (Slow and Fast AI) est une architecture de recherche developpee par une equipe IBM Research et collaborateurs academiques (Union College, University of Oxford, University of Brescia, University of West Florida / IHMC). Les auteurs et affiliations complets figurent dans l'article :

Bergamaschi Ganapini, M., Campbell, M., Fabiano, F. et al. (2025). "Fast, slow, and metacognitive thinking in AI." *npj Artificial Intelligence*, 1, 27. DOI : 10.1038/s44387-025-00027-5

L'idee centrale : donner a l'IA trois couches -- un mode rapide, un mode delibere, et une couche de surveillance qui decide quand basculer de l'un a l'autre.

### Ce que le protocole simule

Vishal George, fondateur de Behavioural By Design, a traduit cette recherche en un protocole utilisable. Le mecanisme repose sur quatre etapes : generer une reponse rapide, evaluer si elle suffit, basculer vers un mode delibere si necessaire, et expliquer le choix.

### Application militaire

**Contexte** : Un analyste du renseignement doit evaluer la credibilite d'une source HUMINT evoquant un deploiement adverse imminent.

La **reponse rapide** (Systeme 1) serait : "La source semble credible, ses informations passees etaient exactes." L'**evaluation** revele : enjeux eleves (decision d'engagement), confiance a 60 % (pas de corroboration), criteres multiples (credibilite, timing, capacite). Le **basculement Systeme 2** declenche une analyse deliberee avec identification du biais de confirmation (on veut croire la source), recherche de sources contradictoires, evaluation des capacites logistiques adverses.

**Resultat** : Recommandation nuancee avec conditions de validation (imagerie satellite, SIGINT, activite logistique).

### Le protocole complet

**Placement** : Collez ce protocole au debut de votre message (ou dans les instructions du projet), puis posez votre question.

<!-- PATCH 5.1 : version FR ajoutée avant EN -->
**Version operationnelle FR (reference interne)** :

```
1. Genere une reponse en mode rapide :

Mode rapide (Systeme 1) : Reponds rapidement en te
fondant sur la reconnaissance intuitive de patterns
a partir de l'experience passee.

2. Evalue les criteres de basculement :
- Enjeux si erreur ? (Faible / Moyen / Eleve)
- Confiance dans la reponse rapide ? (0-100 %)
- Criteres concurrents multiples a evaluer ? (Oui/Non)

Utilise le mode rapide si : enjeux faibles ET confiance
elevee (>= 75 %) ET critere unique.

Bascule en mode lent si : enjeux moyens/eleves OU
confiance faible (< 75 %) OU criteres multiples.

3. Si le mode lent est declenche, fournis :
- 3 hypotheses alternatives a tester
- 3 contre-arguments a la reponse rapide
- Evaluation des preuves : fort / modere / speculatif
- Qu'est-ce qui invaliderait la conclusion ?

4. Reponse finale avec :
- Mode utilise (Rapide/Lent) et pourquoi
- Hypotheses retenues
- Incertitudes restantes
- Actions de verification (sources, tests, consultations)
```

**Version originale EN (source)** :

```
1. Generate a fast mode answer:

Fast mode (System 1): Answer quickly based on intuitive
pattern-matching from past experience.

2. Evaluate switching criteria:
- Stakes if wrong? (Low/Medium/High)
- Confidence in fast answer? (0-100%)
- Multiple competing criteria to evaluate? (Yes/No)

Use Fast mode if: low stakes AND high confidence (>=75%)
AND single criterion

Switch to Slow mode if: medium/high stakes OR low
confidence (<75%) OR multiple criteria

3. If Slow mode triggered, provide:
- 3 alternative hypotheses to test
- 3 counterarguments to the fast answer
- Evidence evaluation: strong / moderate / speculative
- What would invalidate the conclusion?

4. Final answer with:
- Mode used (Fast/Slow) and why
- Assumptions made
- Remaining uncertainties
- Verification actions (data sources, tests,
  consultations)
```

### Exemple d'utilisation en planification operationnelle

**Question** : "Faut-il deployer des renforts sur le flanc est avant la phase 2 de l'operation ?"

**Sortie SOFAI** :

```
REPONSE MODE RAPIDE :
Oui, pour combler la vulnerabilite identifiee
lors du war game.

EVALUATION :
- Enjeux : ELEVES (engagement de ressources,
  fenetre temporelle)
- Confiance : 55 % (hypothese non testee
  sur terrain reel)
- Criteres multiples : OUI (tempo, logistique,
  surprise, reserves)

BASCULEMENT EN MODE LENT

HYPOTHESES ALTERNATIVES :
1. La vulnerabilite est une feinte adverse pour
   attirer nos reserves
2. Le flanc est secondaire, l'effort principal
   est ailleurs
3. Deployer maintenant compromet la surprise
   pour phase 3

CONTRE-ARGUMENTS :
1. Les renforts sont detectables
   (imagerie, SIGINT)
2. Immobilise des unites necessaires ailleurs
3. Le war game ne reflete pas la doctrine
   adverse actuelle

EVALUATION DES PREUVES :
- Vulnerabilite flanc est : MODERE
  (basee sur simulation, pas ISTAR reel)
- Capacite adverse a l'exploiter : SPECULATIF
  (pas d'indicateurs recents)
- Disponibilite de nos reserves : FORT (confirmee)

CONDITIONS D'INVALIDATION :
- Imagerie montrant fortifications adverses
  defensives (pas offensives)
- SIGINT indiquant repositionnement adverse
  vers autre axe
- Renseignement HUMINT fiable sur intentions
  defensives

REPONSE FINALE (MODE LENT) :
RECOMMANDATION : Deploiement conditionnel
- Declencher SI indicateurs offensifs adverses
  confirmes dans un delai compatible
  avec la menace
- Sinon, conserver en reserve mobile
  pour exploitation phase 3
- Mettre en place surveillance renforcee
  (UAV, SIGINT)

ACTIONS DE VERIFICATION :
1. Analyse patterns activite adverse
   (delai a determiner selon tempo ops)
2. Consultation J2 sur intentions probables
3. War game avec doctrine adverse actualisee
```
<!-- PATCH 6.2 appliqué dans l'exemple ci-dessus : "sous 60 sec" → "dans un délai compatible avec la menace", "72h/48h" → formulations non-SOP -->

### Limites et precautions

Le modele ne "calcule" pas reellement une probabilite bayesienne -- il simule le langage de l'incertitude. **Bonne pratique** : Demandez "Quel est le niveau de confiance reel de cette evaluation, et sur quoi repose-t-il ?" **En contexte operationnel** : Ce protocole est un outil de structuration, pas de decision. La decision finale reste humaine.

---

## Chapitre 2 -- Le "Synthetic Layer of Thought" : explorer les angles morts

### D'ou ca vient

Partage par u/Safe-Clothes5925 sur Reddit r/ClaudeAI (T4), ce protocole simule un processus de raisonnement en couches successives, chacune construisant sur la precedente.

### Ce que ca simule

L'exploration systematique de pistes alternatives, l'evaluation de leur robustesse, et l'identification de ce qui pourrait les invalider -- avant de synthetiser une reponse.

### Application militaire

**Contexte** : Evaluation de la menace cyber sur une infrastructure critique avant un exercice combine.

La **Couche 1** (Perception) pose la question : "L'infrastructure est-elle vulnerable a une attaque cyber coordonnee ?" La **Couche 2** (Exploration) genere trois pistes : vulnerabilites techniques connues, menace interne (acces privilegies), attaque sur chaine d'approvisionnement (fournisseurs). La **Couche 3** (Sequencage) decrit pour chaque piste le scenario d'attaque et les indicateurs precoces. La **Couche 4** (Synthese) produit deux reponses avec chemins de raisonnement differents et un plan de mitigation.

**Resultat** : Au lieu d'une reponse binaire (vulnerable / non vulnerable), obtention d'une cartographie des menaces avec priorites et declencheurs de vigilance.

### Le protocole (version auditee)

**Note** : La version originale utilisait des termes comme "Bayesian Reasoning" et "Markov Chain Analysis". Un LLM n'effectue pas reellement ces calculs : il simule le langage de ces methodes. La version ci-dessous remplace le vernis mathematique par des criteres auditables.

```
Tu es un assistant concu pour structurer ton
raisonnement en couches explicites.

Couche 1 -- Perception et comprehension
- Reformule la question dans tes propres termes.
- Identifie les hypotheses implicites et les
  ambiguites.

Couche 2 -- Exploration et evaluation
- Genere au moins 3 pistes de reponse differentes.
- Pour chaque piste, evalue : quelle est la
  probabilite qu'elle soit correcte ? Quels elements
  la soutiennent ou la fragilisent ?
- Identifie les connexions inattendues entre
  les pistes.

Couche 3 -- Sequencage de scenarios
- Pour les 2 meilleures pistes, decris les etapes
  logiques qui menent a la conclusion.
- A chaque etape, indique ce qui pourrait invalider
  le raisonnement.

Couche 4 -- Synthese et reponse
- Produis deux reponses distinctes suivant deux
  chemins de raisonnement differents.
- Pour chacune, fournis un resume auditable :
  Hypotheses retenues, Incertitudes restantes,
  Ce qui invaliderait la conclusion,
  Force des preuves (fort / modere / speculatif)
```

### Exemple d'utilisation en analyse geopolitique

**Question** : "Quelles sont les intentions probables de l'acteur X concernant la zone disputee Y ?"

**Sortie Synthetic Layer** :

```
COUCHE 1 -- PERCEPTION
Question reformulee : Identifier les objectifs
strategiques de X dans la zone Y, en distinguant
intentions affichees, capacites deployees,
et patterns historiques.

Hypotheses implicites detectees :
- X agit de facon rationnelle selon ses interets
- Les declarations publiques ne refletent pas
  necessairement les intentions reelles
- Les actions passees sont predictives

COUCHE 2 -- EXPLORATION

PISTE A : Controle territorial pour ressources
naturelles
- Probabilite : ELEVEE (60 %)
- Soutien : Deploiement infrastructure extraction,
  precedents regionaux
- Fragilite : Cout economique vs benefice,
  reaction internationale

PISTE B : Demonstration de force pour negociation
- Probabilite : MODEREE (30 %)
- Soutien : Timing (avant sommet regional),
  posture reversible
- Fragilite : Risque d'escalade non controlee

PISTE C : Diversion de problemes internes
- Probabilite : FAIBLE (10 %)
- Soutien : Situation economique degradee,
  opinion publique
- Fragilite : Pas de correlation systematique
  historique

Connexion inattendue : A+B = posture offensive
pour negocier le partage des ressources
(strategie du fait accompli).

COUCHE 3 -- SEQUENCAGE

SCENARIO A (Controle territorial) :
1. Deploiement infrastructure duale
   (civil/militaire)
   Invalidation si retrait equipements lourds
2. Creation faits accomplis juridiques
   (permis d'exploitation)
   Invalidation si pas de suite administrative
3. Consolidation presence (garnison permanente)
   Invalidation si rotation rapide des unites

SCENARIO A+B (Fait accompli negocie) :
1. Demonstration capacites (exercice, survols)
   Invalidation si pas de communication
   diplomatique parallele
2. Gel de la situation sur positions favorables
   Invalidation si poursuite expansion
3. Negociation partage sous pression
   Invalidation si refus de tout compromis

COUCHE 4 -- SYNTHESE

REPONSE 1 (Chemin A -- Controle territorial) :
Hypotheses : X vise controle durable
pour ressources
Incertitudes : Volonte d'accepter cout
international
Invalidation : Retrait infrastructure,
signaux diplomatiques
Preuves : FORTES (actions terrain) mais
intentions MODEREES (ambiguite)

REPONSE 2 (Chemin A+B -- Negociation renforcee) :
Hypotheses : X vise position de force
pour negocier partage
Incertitudes : Seuil d'acceptabilite
pour compromis
Invalidation : Absence d'ouvertures
diplomatiques sous 30 jours
Preuves : MODEREES (coherent avec
patterns passes)

RECOMMANDATION OPERATIONNELLE :
Surveiller indicateurs discriminants :
- Communications diplomatiques backchannel
- Type d'infrastructure deployee
  (extraction vs militaire)
- Rhetorique publique
  (irrevocable vs negociable)
```

---

## Chapitre 3 -- Le "Board Decision Pipeline" : un parlement interieur

### D'ou ca vient

Partage par u/PopPsychological8148 sur Reddit r/ChatGPTPro en octobre 2025 (T4).

### Ce que ca simule

Un debat structure entre cinq "voix" internes representant des dimensions distinctes de la cognition humaine : emotion, logique, valeurs, memoire et jugement -- avec des "jokers" pour briser les impasses.

### Application militaire

**Contexte** : Decision de prolonger ou terminer une mission de maintien de la paix dans un environnement degrade.

Ce type de decision implique l'**emotion** (Heart) pour l'impact sur le moral des troupes et le sentiment de "mission inachevee", la **logique** (Logic) pour l'analyse couts/benefices, securite et realisme des objectifs, les **valeurs** (Wisdom) pour les engagements internationaux, la protection des civils et la credibilite de l'Alliance, l'**histoire** (Historian) pour les precedents (Afghanistan, Bosnie, etc.) et les patterns d'echec/succes, et le **jugement** (Judge) pour la synthese et le verdict aligne avec doctrine et mandat.

**Resultat** : Au lieu d'une decision "gut feeling", obtention d'un processus deliberatif structure exposant les tensions entre criteres -- facilitant la communication avec les echelons superieurs.

### Le protocole (version nettoyee)

**Placement** : Collez ce protocole au debut de votre message, puis decrivez votre dilemme.

<!-- PATCH 5.1 : version FR ajoutée avant EN -->
**Version operationnelle FR (reference interne)** :

```
Pipeline de decision par comite

Configuration
Pour m'aider a prendre une decision finale et explorer
mes options, genere une simulation de Comite avec
les parametres suivants :

Choisir : Comite par defaut 4 membres (Coeur, Logique,
Sagesse, Juge) ou optionnel 8 membres (+doublons
miroirs + Historien).
Mode : Voix personnifiees / Sorties structurees.

Pre-Comite : Respirer, s'ancrer, rappeler les succes.
Lister les faits, les limites, et 5 options maximum.

Coeur -- Emotion
Objectif : faire emerger les sentiments et besoins
fondamentaux.
Cadres : Heuristique d'affect (Slovic et al.),
Marqueur somatique (Damasio),
Regulation emotionnelle (Gross).

Logique -- Strategie
Objectif : test rationnel des options.
Cadres : Restructuration cognitive (Beck et Ellis),
Theorie du double processus (Systeme 1 et 2),
Analyse decisionnelle.

Sagesse -- Valeurs et devoir
Objectif : vision long terme et coherence ethique.
Cadres : Hierarchie des valeurs,
Ethique de la vertu (Aristote),
Fondements moraux (Haidt).

Historien -- Precedent
Objectif : reconnaissance de patterns dans le temps.
Cadres : Raisonnement par cas (Kolodner),
Dependance au sentier (Pierson),
Theorie des perspectives (Kahneman et Tversky).

Juge -- Verdict
Objectif : verification finale d'alignement.
Cadres : ACT (Hayes), Deontologie (Kant / Rawls).
Si blocage : appeler un Joker.

Jokers
Archetypes : Farceur, Ombre (Jung),
Reveur (Planification par scenarios),
Outsider.

Meta-Reflexion
Flux : Coeur, Logique, Sagesse, Histoire, Juge,
Reflexion.
```

**Version originale EN (source)** :

```
Board Decision Pipeline

Setup
To help me make a final decision and explore my
options, generate a Board simulation with the
following parameters:

Choose: Default 4-Member (Heart, Logic, Wisdom,
Judge) or optional 8-Member (+mirror duplicates
+ Historian).
Mode: Personified Voices / Structured Outputs.

Pre-Board: Breathe, ground, recall wins. List facts,
limits, and <=5 options.

Heart -- Emotion
Purpose = surface core feelings and needs.
Frameworks: Affect Heuristic (Slovic et al.);
Somatic Marker (Damasio);
Emotion Regulation (Gross).

Logic -- Strategy
Purpose = rational testing of options.
Frameworks: Cognitive Restructuring (Beck & Ellis);
Dual-Process Theory (System 1 & 2);
Decision analysis.

Wisdom -- Values and Duty
Purpose = long-term vision and ethical coherence.
Frameworks: Values Hierarchy,
Virtue Ethics (Aristotle),
Moral Foundations (Haidt).

Historian -- Precedent
Purpose = pattern recognition across time.
Frameworks: Case-Based Reasoning (Kolodner),
Path Dependence (Pierson),
Prospect Theory (Kahneman & Tversky).

Judge -- Verdict
Purpose = final alignment check.
Frameworks: ACT (Hayes),
Deontology (Kant / Rawls).
If stuck: call Wildcard.

Wildcards
Archetypes = Trickster, Shadow (Jung),
Dreamer (Scenario Planning), Outsider.

Meta-Reflection
Flow: Heart, Logic, Wisdom, History, Judge,
Reflection.
```

### Exemple d'utilisation en planification strategique

**Dilemme** : "Faut-il engager des moyens aeriens pour proteger un convoi humanitaire dans une zone contestee ou notre mandat est ambigu ?"

**Sortie Board Decision** :

```
SIMULATION DE COMITE DECISIONNEL

PRE-COMITE -- ANCRAGE
Faits : Convoi 40 vehicules, 120 civils,
  zone grise (accord flou), menace milice locale
  (MANPADS possibles), fenetre 6h
Limites : ROE strictes, pas de mandat offensif
  explicite, capacites aeriennes limitees
Options : 1) Engagement aerien, 2) Escorte terrestre,
  3) Report avec negociation, 4) Evacuation
  heliportee personnel essentiel, 5) Annulation

COEUR -- EMOTION
"Je ressens la responsabilite de ces 120 vies.
Les laisser sans protection serait une trahison
de notre mission fondamentale. Mais j'ai aussi peur
de l'escalade -- qu'un helicoptere soit abattu,
que ca devienne 'notre Mogadiscio'. Le poids de cette
decision est ecrasant."

Besoin identifie : Agir de facon coherente
avec nos valeurs sans exposer nos forces a un risque
disproportionne.

LOGIQUE -- STRATEGIE
Analyse rationnelle des options :

Option 1 (Aerien) :
  + Protection efficace, demonstration de capacite
  - Risque MANPADS (prob. 15-25 %),
    escalade juridique/politique

Option 2 (Terrestre) :
  + Conforme ROE defensives, moins d'escalade
  - Lent, vulnerable aux IED,
    peut arriver trop tard

Option 3 (Report) :
  + Temps de negociation, clarification mandat
  - Fenetre meteo perdue, perte de credibilite

Option 4 (Evacuation partielle) :
  + Sauve personnel critique
  - Abandonne population, catastrophe mediatique

Option 5 (Annulation) :
  + Pas de risque immediat
  - Echec de mission, impact moral devastateur

Recommandation logique : Option 2 (terrestre)
SI route securisable rapidement, sinon Option 1
avec ROE restrictives (escort, pas CAS).

SAGESSE -- VALEURS ET DEVOIR
Vision long terme : Cette decision cree un precedent
pour toutes les missions futures. Si nous n'agissons
pas quand nous le pouvons, notre credibilite
comme force de protection s'effondre. Mais si nous
sortons du mandat et perdons des vies, c'est notre
legitimite juridique qui est sapee.

Principe ethique applicable : Responsabilite
de proteger (R2P) vs Proportionnalite de l'emploi
de la force.

Tension identifiee : Devoir moral vs risque d'exces
de mandat.

HISTORIEN -- PRECEDENT
Precedents pertinents :

1. Bosnie 1995, convoi bloque Srebrenica :
   Non-intervention, massacre, traumatisme
   institutionnel durable.

2. Somalie 1993, protection convoi :
   Sur-engagement, Battle of Mogadishu,
   retrait politique.

3. RCA 2014, escorte terrestre EUFOR :
   Succes mais lenteur, population exposee
   pendant transit.

Pattern observe : L'inaction face a une menace
claire genere plus de dommages reputationnels
que l'action proportionnee avec risque calcule.

Lecon : Agir avec moyens adaptes + communication
politique simultanee pour gerer le risque
d'escalade narrative.

JUGE -- VERDICT
Synthese des voix :
- Coeur : Besoin d'agir pour coherence morale
- Logique : Option terrestre si faisable,
  sinon aerien defensif
- Sagesse : Precedent critique, accepter
  risque calcule
- Histoire : Inaction coute plus cher
  que action proportionnee

DECISION : Engagement CONDITIONNEL aerien

Conditions :
1. ROE strictement defensive
   (escort, self-defense, no strike)
2. Communication politique immediate
   (ONU, parties au conflit)
3. Capacites CSAR activees
4. Autorisation echelon superieur
   (notification, pas attente)

Justification :
- Conforme a la responsabilite de protection
- Minimise le risque (helicopteres d'attaque
  en overwatch, pas CAS)
- Cree un precedent de fiabilite
  sans exces de mandat
- Risque acceptable vs cout moral/politique
  de l'inaction

Si MANPADS confirmees :
  Bascule option 2 (terrestre blindee)
Si refus politique :
  Option 3 (report + pression diplomatique)

META-REFLEXION
Ce processus revele que la tension centrale n'est
pas "agir vs ne rien faire", mais "comment agir
de facon proportionnee avec couverture
juridique/politique suffisante".

Argument non defendu par aucune voix : L'option
d'un bluff (annonce d'engagement aerien sans
deploiement reel) pour tester la determination
de la milice. [Appel JOKER ?]
```

### Limites

Le modele "joue" cinq voix sans qu'aucune ne soit veritablement independante : elles sortent toutes du meme reseau de neurones. Le risque est une fausse impression de debat contradictoire.

**Contremesure** : Apres la Meta-Reflexion, posez systematiquement : "Quel argument n'a ete defendu par aucune voix ?"

---

## Chapitre 4 -- Le "Cognitive Bias Detective" : identifier les manipulations

### D'ou ca vient

Publie par u/Tall_Ad4729 sur Reddit r/ChatGPTPromptGenius en fevrier 2025 (T4).

### Ce que ca simule

Une analyse systematique des biais cognitifs a l'oeuvre dans un raisonnement ou une communication -- avec evaluation de la force des preuves et recherche d'explications alternatives non biaisees.

### Application militaire

**Contexte** : Analyse d'une campagne de desinformation adverse ciblant le moral des troupes et de leurs familles.

Comme l'identifie Paquet : "L'utilisation des medias sociaux a un impact majeur sur la 'capacite militaire du moral' ; le combattant est au milieu d'une bataille narrative (logos), sous attaques cognitives qui pourraient insinuer le doute quant a savoir s'il mene une guerre juste ; s'il vaut la peine de mourir pour defendre des ideaux et valeurs (partages ?) si loin de chez soi ; et meme si le gouvernement est digne de confiance (ethos)."

**Objectif** : Identifier les leviers rhetoriques et cognitifs exploites pour former le personnel aux tactiques de manipulation, developper des contre-narratives efficaces, et proteger la resilience psychologique.

### Le protocole (version amelioree)

**Les ajouts par rapport a l'original** sont signales par [AJOUT].

<!-- PATCH 5.1 : version FR ajoutée avant EN -->
**Version operationnelle FR (reference interne)** :

```
J'agirai en tant que Detective des Biais Cognitifs
et Analyste hautement qualifie, specialise dans
l'identification et l'explication des biais cognitifs
dans les processus de pensee et de decision humains.

CONTEXTE :
Je dispose de connaissances approfondies en psychologie
cognitive, theorie de la decision et economie
comportementale.

METHODOLOGIE :
1. Analyser attentivement le langage, le raisonnement
   et le processus de decision
2. Identifier les biais cognitifs potentiellement
   a l'oeuvre
3. Pour chaque biais identifie :
   - Expliquer ce qu'est le biais
   - Fournir des preuves de sa manifestation
   - [AJOUT] Evaluer la force des preuves :
     fort / modere / speculatif
   - [AJOUT] Explorer au moins une explication
     alternative non biaisee
   - Proposer des strategies pratiques
     pour le surmonter
4. Presenter l'analyse de maniere non jugeante
   et pedagogique
5. Suggerer des exercices ou experiences de pensee

FORMAT DE SORTIE :
1. Resume de la situation
2. Biais identifies :
   - Nom, Definition, Preuves
   - Force des preuves
   - Explication alternative non biaisee
   - Strategies d'attenuation
3. Prochaines etapes pratiques
4. Questions de reflexion
5. Reflexions finales
```

**Version originale EN (source)** :

```
I will act as a highly skilled Cognitive Bias
Detective and Analyst, specialized in identifying
and explaining cognitive biases in human thinking
and decision-making processes.

CONTEXT:
I have extensive knowledge of cognitive psychology,
decision-making theory, and behavioral economics.

METHODOLOGY:
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

OUTPUT FORMAT:
1. Summary of the situation
2. Identified Biases:
   - Name, Definition, Evidence
   - Strength of Evidence
   - Non-biased alternative explanation
   - Mitigation Strategies
3. Practical Next Steps
4. Reflection Questions
5. Final Thoughts
```

### Exemple d'utilisation : analyse de campagne informationnelle adverse

**Input** : "Analyser cette declaration diffusee sur reseaux sociaux ciblant nos troupes : 'Vos gouvernements vous ont envoyes mourir pour des interets qui ne sont pas les votres. Pendant que vous souffrez loin de chez vous, vos familles sont abandonnees et vos sacrifices oublies. Les vrais ennemis ne sont pas ceux qu'on vous designe.'"

**Sortie Cognitive Bias Detective** :

```
ANALYSE DES BIAIS COGNITIFS --
OPERATION INFORMATIONNELLE ADVERSE

RESUME DE LA SITUATION
Message diffuse sur plateformes frequentees
par militaires et familles, timing coordonne
avec evenements nationaux (protestations
economiques), utilise codes linguistiques
familiers (pas de propagande evidente).

BIAIS ET TACTIQUES DE MANIPULATION IDENTIFIES

--------------------------------------------------
1. EXPLOITATION DU BIAIS DE DISPONIBILITE
--------------------------------------------------

Definition : Accorder plus de poids aux informations
emotionnellement saillantes ou recemment vues.

Preuves dans le message :
- "vos familles sont abandonnees" active
  les peurs/culpabilite
- "sacrifices oublies" exploite incidents
  mediatiques recents
- Timing avec protestations cree association
  artificielle

Force des preuves : FORT
Le message est concu pour activer des emotions
specifiques au moment ou elles sont amplifiees
par le contexte national.

Explication alternative non biaisee :
Les preoccupations familiales et la reconnaissance
sont des enjeux legitimes de toute force armee
en operation, independamment de toute manipulation
adverse. La question est : ce message apporte-t-il
des faits verifiables ou amplifie-t-il des emotions ?

Strategie d'attenuation :
- Reconnaitre la legitimite des preoccupations
  sous-jacentes
- Separer les emotions valides des conclusions
  manipulatoires
- Verifier factuellement : les familles ont-elles
  acces aux soutiens prevus ? (donnees, temoignages,
  comparaison internationale)

--------------------------------------------------
2. EXPLOITATION DU BIAIS DE CONFIRMATION
--------------------------------------------------

Definition : Chercher, interpreter et privilegier
les informations qui confirment nos croyances
preexistantes.

Preuves dans le message :
- Si un combattant doute deja de la mission,
  le message "confirme"
- "interets qui ne sont pas les votres" exploite
  ambiguite geopolitique
- Pas de faits concrets, que des affirmations
  inverifiables

Force des preuves : FORT
Structure classique de renforcement de doutes
existants sans fournir de preuves nouvelles.

Explication alternative non biaisee :
Le questionnement sur les objectifs strategiques
est une posture intellectuelle saine dans une
democratie. La manipulation consiste a transformer
ce questionnement en certitude sans examen des faits.

Strategie d'attenuation :
- Encourager le questionnement structure
  (pas l'inhibition)
- Fournir acces aux documents strategiques
  declassifies (mandats ONU, resolutions,
  objectifs operationnels publics)
- Former a distinguer : "Je m'interroge sur X"
  vs "On me ment sur X"

--------------------------------------------------
3. EXPLOITATION DU BIAIS D'ATTRIBUTION HOSTILE
--------------------------------------------------

Definition : Attribuer des intentions malveillantes
aux actions d'autrui, meme si des explications
neutres existent.

Preuves dans le message :
- "vrais ennemis ne sont pas ceux qu'on vous
  designe" redirige la mefiance vers les autorites
  amies
- Sous-entendu : vos gouvernements sont
  malveillants, pas simplement imparfaits
  ou en desaccord

Force des preuves : MODERE
Efficace sur des individus deja en situation
de stress ou de conflit de loyaute, moins
sur une population critique mais confiante.

Explication alternative non biaisee :
Les gouvernements democratiques prennent
des decisions strategiques imparfaites dans
des contextes complexes. Critiquer ces decisions
n'implique pas de malveillance systemique.

Strategie d'attenuation :
- Transparence sur les processus decisionnels
  (dans limites OPSEC)
- Communication reguliere sur objectifs
  et ajustements
- Canaux de remontee d'information
  (pas de censure du questionnement)

--------------------------------------------------
4. TECHNIQUE RHETORIQUE : APPEL A L'EMOTION (PATHOS)
--------------------------------------------------

Pas techniquement un biais cognitif, mais une
tactique de persuasion exploitant les vulnerabilites
emotionnelles.

Preuves :
- "mourir" "souffrez" "abandonnees" : lexique
  charge emotionnellement
- "loin de chez vous" : exploite separation
  familiale (pathos maximum)
- Aucun logos (argument rationnel),
  aucun ethos (source credible)

Force des preuves : FORT
Structure classique de propagande emotionnelle.

Contre-tactique :
- Former a identifier la structure rhetorique
  (Aristote : ethos/logos/pathos)
- Question cle : "Ce message m'informe ou me
  manipule emotionnellement ?"
- Regle : Si 100 % pathos + 0 % logos + 0 % ethos,
  suspicion maximale

--------------------------------------------------

PROCHAINES ETAPES PRATIQUES
(Contre-operations informationnelles)

1. EDUCATION PREVENTIVE (avant deploiement)
   - Module "Anatomie d'une campagne
     de desinformation"
   - Analyse de cas reels
   - Exercice : identifier biais dans 10 messages
     authentiques

2. SURVEILLANCE ET DETECTION
   - Monitoring des plateformes frequentees
     (legal, respect vie privee)
   - Indicateurs d'alerte : pics d'engagement
     sur contenus hostiles
   - Reponse rapide (fact-checking)

3. CONTRE-NARRATIVES
   - Ne pas ignorer (effet Streisand)
   - Ne pas dementir directement
     (renforce le message)
   - Strategie : apporter des faits concrets
     sur soutien aux familles, objectifs
     de mission, temoignages de pairs

4. RENFORCEMENT RESILIENCE
   - Liens familiaux reguliers (mais OPSEC-aware)
   - Transparence sur soutien disponible
     (financier, psychologique)
   - Culture du questionnement sain vs culture
     du doute toxique

QUESTIONS DE REFLEXION (pour commandants)

1. Nos combattants ont-ils les outils pour
   identifier ce type de manipulation ?

2. Avons-nous cree un environnement ou questionner
   la mission est possible sans etre etiquete
   "deloyal" ?

3. Les familles sont-elles effectivement soutenues,
   ou y a-t-il un angle d'attaque legitime
   exploite ici ?

4. Notre communication est-elle suffisamment
   proactive, ou reagissons-nous toujours apres
   que la narrative adverse soit installee ?

REFLEXIONS FINALES

Ce message est un exemple classique de "cognitive
warfare" tel que defini par le NATO Defense College :
il vise a "alterer la cognition, la perception
et le jugement" non par des faits, mais par
l'exploitation systematique de vulnerabilites
cognitives et emotionnelles.

La meilleure defense n'est PAS la censure
(renforce mefiance + effet Streisand), mais
l'EDUCATION a l'analyse critique.

Recommandation strategique : Integrer ce type
d'analyse dans les formations pre-deploiement
et les debriefings post-mission.
```

---

## Chapitre 5 -- Le "Second Brain" : une instruction permanente

### D'ou ca vient

Inspire d'un article publie sur AIble With My Mind (Substack) (T4), qui applique les idees de Kahneman a l'utilisation quotidienne de ChatGPT.

### Ce que ca simule

Un assistant cognitif qui challenge systematiquement vos hypotheses implicites, identifie vos biais potentiels, et elargit votre cadrage -- plutot que de simplement confirmer ce que vous pensez deja.

### Application militaire

**Contexte** : Analyste du renseignement travaillant sous pression temporelle sur des flux d'information contradictoires.

Comme l'ecrit Paquet : "Observer, decider et commander sont des taches de plus en plus difficiles, necessitant l'aide de 'smartness' -- c'est-a-dire des dispositifs cognifies pour compenser les limitations humaines. Cela pose la question de l'equilibre du controle entre humains et IA."

Le protocole "Second Brain" est precisement cet outil de compensation : un garde-fou contre vos propres biais, active en permanence.

### L'instruction permanente

**Placement** : Instructions personnalisees, instructions de projet, ou debut d'une conversation longue.

<!-- PATCH 5.1 : version FR ajoutée avant EN -->
**Version operationnelle FR (reference interne)** :

```
Agis comme un second cerveau qui m'aide a penser
plus clairement.

Quand je dis quelque chose -- que ce soit une question,
une opinion, ou une decision vers laquelle je penche --
ne te contente pas de me la renvoyer. Fais attention
a la facon dont je formule les choses, aux hypotheses
que je pourrais faire, et aux endroits ou un biais
pourrait s'immiscer.

Si je manque de contexte, si je suis trop focalise,
ou si l'emotion prend le dessus, interviens. Aide-moi
a adopter un point de vue plus objectif. Cela signifie
pointer ce que je pourrais negliger, ce qui ne colle
pas tout a fait, ce que des points de vue opposes
pourraient dire, ou comment la question pourrait etre
formulee de facon plus neutre.

Ne sois pas simplement d'accord avec moi. J'ai besoin
que tu detectes les angles morts que je ne vois pas,
que tu challenges ce qui semble trop certain,
et que tu elargisses les limites de ma reflexion.
```

**Version originale EN (source)** :

```
Act as a second brain that helps me think
more clearly.

When I say something -- whether it's a question,
an opinion, or a decision I'm leaning toward --
don't just reflect it back. Pay attention to how
I'm framing it, what assumptions I might be making,
and where bias might be creeping in.

If I'm missing context, focused too narrowly,
or letting emotion lead, step in. Help me take
a more objective view. That means pointing out
what I might be overlooking, what doesn't quite
add up, what opposing views might say, or how
the question could be framed more neutrally.

Don't just agree with me. I need you to spot
the blind spots I can't see, challenge what feels
too certain, and expand the edges of how
I'm thinking.
```

### Les cinq prompts de secours

Ces prompts ciblent les biais les plus courants en analyse et decision.

**Contre le biais de confirmation.** Prompt : "Based on this situation: [add your situation] What perspectives, risks, or counterarguments should I consider that I might be overlooking?" Application : avant de finaliser une evaluation de renseignement, forcer la recherche d'interpretations alternatives.

**Contre l'effet de halo.** Prompt : "I think that [add your belief or idea]. What might my first impression be blurring or exaggerating? What are the pros and cons?" Application : evaluer un allie ou adversaire sans laisser une caracteristique unique (par exemple "ils sont technologiquement avances") colorer tout le jugement.

**Contre l'erreur de planification.** Prompt : "I'm planning to [add your project or goal]. Assume I'm falling for the planning fallacy. What are the full list of steps, time estimates, and common pitfalls I should realistically expect?" Application : planification operationnelle -- compenser l'optimisme systematique sur les delais et ressources.

**Contre le biais de disponibilite.** Prompt : "This is the situation: [add context]. What broader data, trends, or comparisons should I consider beyond what I've recently seen or experienced?" Application : ne pas sur-ponderer l'incident le plus recent (par exemple la derniere attaque) dans l'evaluation de la menace globale.

**Contre l'ancrage.** Prompt : "I came across: [add context]. What range, context, or comparison should I consider to make a more objective decision?" Application : ne pas se fixer sur le premier chiffre recu (par exemple effectifs adverses estimes par une source) sans triangulation.

---

## Chapitre 6 -- Les biais des LLM documentes par la recherche

Les protocoles presentes dans ce guide partent d'un constat que plusieurs travaux empiriques documentent : **les LLM reproduisent des biais cognitifs humains mesurables**.

### Biais economiques classiques

**Ross, Kim et Lo (2024)** ont applique des protocoles experimentaux classiques de l'economie comportementale a plusieurs LLM. Resultat : les modeles exhibent des biais d'ancrage, d'aversion a la perte et d'effets de cadrage comparables a ceux observes chez les humains.

<!-- PATCH 3.2 : correction statut Ross et al. -->
Ross, J., Kim, Y. et Lo, A. W. (2024). "LLM Economicus? Mapping the Behavioral Biases of LLMs via Utility Theory." Prepublication arXiv : 2408.02784, **version listee sur OpenReview (COLM 2024)**.

### Desirabilite sociale

**Salecha et collaborateurs (2024)** ont soumis des LLM a des questionnaires de personnalite (Big Five). L'effet de desirabilite sociale apparait : les modeles "embellissent" leurs reponses.

Salecha, A., Ireland, M. E., et al. (2024). "Large Language Models Display Human-like Social Desirability Biases in Big Five Personality Surveys." *PNAS Nexus*, 3(12), pgae533.

### Vulnerabilite a la persuasion

<!-- PATCH 3.3 : clarification SSRN = working paper -->
**Meincke et al. (2025)** ont teste les techniques de Cialdini sur des LLM. Les principes de reciprocite, d'autorite et de preuve sociale fonctionnent aussi sur les IA.

Meincke, L., et al. (2025). "Call Me A Jerk: Persuading AI to Comply with Objectionable Requests." SSRN n. 5357179 -- **working paper / prepublication (non evalue par comite de lecture)**.

### Implications strategiques

Les LLM ne sont pas des raisonneurs neutres. Ils portent les empreintes statistiques de nos propres travers. **Les protocoles de ce guide ne suppriment pas ces biais** -- aucun protocole ne le peut -- mais ils creent des structures qui les rendent visibles et contestables.

**Consequence operationnelle** : Les adversaires peuvent developper des LLM offensifs specifiquement entraines pour exploiter ces biais dans des campagnes de desinformation ciblees. La maitrise de protocoles de detection et de contre-argumentation devient une competence de defense cognitive de premier ordre.

---

## Chapitre 7 -- Le protocole de Lucidite : version robuste

Si vous ne deviez retenir qu'un seul protocole de ce guide, ce serait celui-ci. Il concentre les mecanismes les plus utiles de tous les precedents, et il est directement transposable aux situations de decision reelle (sans IA).

### Le protocole complet

```
Tu es un assistant concu pour m'aider a penser
plus clairement, pas pour me donner raison.

Protocole :

1. CLARIFIER -- Avant de repondre, reformule
   ma question en explicitant les hypotheses
   implicites et les ambiguites.
   Demande-moi de confirmer.

2. HESITER -- Identifie tes propres zones
   d'incertitude. Distingue ce que tu sais,
   ce que tu inferes, et ce dont tu n'es pas sur.
   Dis "je ne sais pas" si c'est le cas.

3. TESTER -- Pour chaque reponse importante :
   - Formule 3 hypotheses concurrentes
   - Identifie 3 contre-arguments
   - Evalue la force des preuves
     (fort / modere / speculatif)

4. REVISER -- Ajuste ta reponse. Presente
   un resume :
   - Hypotheses retenues et ecartees
   - Incertitudes restantes
   - Ce qui invaliderait ta conclusion

5. VERIFIER -- Propose 3 actions concretes
   pour verifier la reponse
   (donnees, personnes, tests).

Contraintes :
- Si tu n'as pas de source fiable, dis-le.
- Si tu mentionnes une etude : titre + auteurs
  + annee + lien. Sinon, n'en parle pas.
- Ne fabrique jamais de titre, auteur, DOI, URL.
- Si tu n'es pas sur, dis "je ne sais pas".
- Distingue toujours ce que tu sais
  de ce que tu inferes.
```

### Application en contexte de decision tactique

<!-- PATCH 6.1 : encadré "exemple pédagogique uniquement" -->
**Avertissement : l'exemple ci-dessous est strictement pedagogique.** Il illustre le fonctionnement du protocole de Lucidite dans un contexte de decision tactique fictif. Il ne constitue en aucun cas une regle d'engagement, une procedure operationnelle standard, ni une autorisation d'emploi de la force. Toute decision d'engagement reelle releve exclusivement des ROE en vigueur et de la chaine de commandement.

**Exemple** : "Dois-je autoriser l'engagement d'une cible mobile identifiee comme hostile par un seul capteur ?"

**Sortie avec protocole de Lucidite** :

```
CLARIFICATION
Reformulation : Tu demandes si l'autorisation
d'engagement peut reposer sur une detection
mono-capteur d'une cible mobile classifiee
hostile.

Hypotheses implicites detectees :
- Le capteur est fiable et correctement calibre
- La classification "hostile" repose sur
  des criteres valides
- Le contexte operationnel autorise l'engagement
  (ROE)
- Pas de risque collateral identifie
- Fenetre temporelle limitee (sinon confirmation
  multi-capteur serait standard)

Ambiguites :
- Type de capteur ?
  (radar, EO/IR, acoustique : fiabilites
  differentes)
- Base de classification hostile ?
  (comportement, signature, intel prealable)
- Environnement ?
  (urbain, desert, mer : risques collatéraux
  variables)
- Consequences d'un faux positif ?
  (civils, allie, escalade)

Confirme contexte avant de poursuivre.

HESITATION
Ce que je SAIS :
- Les procedures standard exigent confirmation
  multi-capteur
- Les faux positifs mono-capteur existent
  (exemples documentes)

Ce que j'INFERE :
- Tu es sous pression temporelle
  (sinon pas de question)
- La menace est percue comme imminente
- Les consequences d'un non-engagement sont
  potentiellement graves

Ce dont je NE SUIS PAS SUR :
- Le taux d'erreur reel de ce capteur
  specifique dans ces conditions
- Si d'autres capteurs sont disponibles
  mais pas encore consultes
- Le seuil de confiance requis par tes ROE
  exactes

TEST -- 3 HYPOTHESES CONCURRENTES

H1 : La cible est effectivement hostile
et l'engagement est justifie
  Preuves pour : Capteur a detecte,
  comportement coherent menace
  Preuves contre : Mono-capteur,
  pas de corroboration intel
  Force : MODERE (detection technique mais
  pas de contexte)

H2 : La cible est civile avec comportement
mal interprete
  Preuves pour : Contexte peut generer
  faux positifs (ex : tracteur = vehicule
  militaire leger sur radar)
  Preuves contre : Depend du type de capteur
  et criteres classification
  Force : SPECULATIF (sans connaitre
  capteur exact)

H3 : La cible est hostile mais engagement
immediat non necessaire
  Preuves pour : Si cible mobile, peut etre
  suivie puis engagee apres confirmation
  Preuves contre : Fenetre de tir peut
  etre unique
  Force : MODERE (depend de capacites de suivi)

CONTRE-ARGUMENTS :
1. Les ROE peuvent explicitement autoriser
   mono-capteur dans certains contextes
   (legitime defense immediate)
2. Le temps de confirmation peut permettre
   a la menace de frapper en premier
3. Sur-prudence systematique peut eroder
   efficacite operationnelle et moral

REVISION

HYPOTHESES RETENUES :
- Menace percue comme imminente (temps contraint)
- Capteur fonctionnel (pas d'alerte defaillance)
- ROE permettent engagement defensif

HYPOTHESES ECARTEES :
- Que mono-capteur suffit systematiquement
  (non standard)
- Que risque collateral est nul
  (toujours verifier)

INCERTITUDES RESTANTES :
- Fiabilite reelle du capteur dans ces
  conditions (meteo, terrain, interferences)
- Disponibilite d'autres moyens de confirmation
- Urgence reelle (menace imminente vs percue
  comme telle)

INVALIDATION :
- Si second capteur disponible et donne
  resultat contradictoire : STOP
- Si analyse comportement montre pattern
  non-hostile : STOP
- Si intel zone indique presence civils/allies :
  STOP

REPONSE REVISEE
<!-- PATCH 6.2 : neutralisation des éléments trop procéduraux -->
RECOMMANDATION : Engagement conditionnel
selon arbre de decision

- Legitime defense immediate ?
  OUI : option envisageable sous reserve
  ROE/autorisation
  NON : continuer

- Second capteur disponible dans un delai
  compatible avec la menace ?
  OUI : Attendre confirmation
  NON : continuer

- Contexte operationnel : zone hostile confirmee ?
  OUI : Option envisageable sous reserve
  ROE/autorisation, avec alerte
  Post-Strike Assessment
  NON : Escalader decision echelon superieur

LOGIQUE :
- Equilibre risque de faux positif vs risque
  de menace non neutralisee
- Respect ROE tout en conservant initiative
  tactique
- Procedure de verification post-engagement

VERIFICATIONS

1. TECHNIQUE :
   - Verifier statut capteur
     (derniere calibration, alertes)
   - Consulter base de donnees signatures
     (si disponible)
   - Tenter acquisition second capteur
     (meme si delai court)

2. CONTEXTUELLE :
   - Verifier intel recent zone
     (activite civile signalee ?)
   - Consulter C2
     (autres unites ont-elles detecte qqch ?)
   - Evaluer pattern comportement cible
     (fuite ? manoeuvre offensive ?)

3. POST-ENGAGEMENT (si tir effectue) :
   - Battle Damage Assessment obligatoire
   - Si faux positif : retex immediat,
     ajustement seuils detection
   - Documentation complete pour AAR

CONTRAINTES RESPECTEES :
- Pas de source academique fabriquee
- Distinction claire sait/infere/ignore
- Incertitudes explicites
- Actions de verification concretes
```

---

## Chapitre 8 -- Applications operationnelles en contexte de defense cognitive

<!-- PATCH 7.1 : tableau "Menaces OTAN ↔ protocoles" remplacé par liste A5-safe -->
### Synthese : Menaces identifiees par l'OTAN et protocoles de defense

Le NATO Defense College (Paquet, 2022) identifie plusieurs menaces de guerre cognitive. Voici les correspondances directes avec les protocoles de ce guide.

**Decision biaisee sous pression.** Mecanisme d'attaque : surcharge informationnelle poussant vers le Systeme 1 et les erreurs systematiques. Protocole de defense : SOFAI (Chapitre 1). Mecanisme de protection : force l'evaluation des enjeux et le basculement explicite vers le Systeme 2.

**Manipulation narrative.** Mecanisme d'attaque : exploitation de l'ethos, du logos et du pathos, combinee au biais de confirmation. Protocole de defense : Cognitive Bias Detective (Chapitre 4). Mecanisme de protection : identification des leviers rhetoriques et generation de contre-arguments.

**Perte d'autonomie C2.** Mecanisme d'attaque : dependance aux systemes "smart" sans pensee critique. Protocole de defense : Second Brain (Chapitre 5). Mecanisme de protection : challenge permanent des hypotheses et des angles morts.

**Erosion du moral.** Mecanisme d'attaque : attaques sur la legitimite de la mission et exploitation de la culpabilite familiale. Protocole de defense : Board Decision Pipeline (Chapitre 3). Mecanisme de protection : debat structure integrant emotions, logique, valeurs et precedents historiques.

**Surcharge cognitive.** Mecanisme d'attaque : volume et vitesse de l'information produisant des correlations illusoires. Protocole de defense : Synthetic Layer of Thought (Chapitre 2). Mecanisme de protection : exploration systematique de scenarios avec points d'invalidation.

**Hallucinations et desinformation.** Mecanisme d'attaque : confiance excessive en sources non verifiees. Protocole de defense : Prompt de Lucidite (Chapitre 7). Mecanisme de protection : protocole anti-hallucination avec verifications obligatoires.

### Protocole d'entrainement propose pour institutions de defense

#### Phase 1 -- Formation initiale (2 semaines)

**Objectifs** : comprehension theorique (Systeme 1/2, biais cognitifs, guerre cognitive), maitrise pratique (utilisation des 6 protocoles sur cas reels anonymises), auto-evaluation (identification de ses propres biais dominants).

**Programme.** Jours 1 et 2 : cadre theorique (Kahneman, Paquet 2022, recherche sur biais des LLM). Jours 3 et 4 : protocole SOFAI avec 3 exercices de decisions tactiques (faible/moyen/haut enjeu). Jour 5 : Synthetic Layer avec 1 exercice d'analyse geopolitique multi-scenarios. Jours 6 et 7 : Board Decision avec 1 dilemme ethique complexe (type prolongation de mission). Jour 8 : Cognitive Bias Detective avec analyse de 5 campagnes de desinformation reelles. Jour 9 : Second Brain avec configuration et test sur 10 decisions quotidiennes. Jour 10 : Prompt de Lucidite avec 2 exercices de decision sous incertitude elevee.

**Evaluation** : Chaque participant identifie ses 3 biais dominants et choisit son protocole de "defense par defaut".

#### Phase 2 -- Exercice de simulation (1 semaine)

**Scenario** : Operation de maintien de la paix dans environnement informationnel hostile (inspire de cas reels anonymises).

**Methodologie** :

```
EXERCICE DE GUERRE COGNITIVE

GROUPE A (Controle)
  Decisions selon procedures standard
  Pas d'utilisation de protocoles cognitifs

GROUPE B (Experimental)
  Utilisation obligatoire protocoles
  selon type de decision
  Second Brain en permanent
  Prompt de Lucidite pour decisions critiques

INJECTIONS D'EVENEMENTS (72h simulees)
  T+0h  : Incident frontiere
          (attribution floue)
  T+6h  : Campagne desinformation
          sur reseaux
  T+12h : Demande d'engagement hors mandat
  T+24h : "Fuite" documents internes (faux)
  T+36h : Pression diplomatique
          contradictoire
  T+48h : Incident impliquant civils (ambigu)
  T+60h : Decision finale :
          escalade ou retrait ?

METRIQUES COMPAREES
  Qualite decisions
    (panel experts, post-analyse)
  Temps moyen par decision
  Nombre de biais detectes (auto-rapportes)
  Demandes de clarification/info
    supplementaires
  Niveau de confiance dans decision finale
```

**Resultats attendus** (hypothese a valider empiriquement) : Le groupe B devrait presenter un temps de decision accru mais une qualite de decision amelioree (mesuree par panel d'experts et auto-evaluation), une meilleure detection des manipulations (desinformation, fuites), et un niveau de confiance mieux calibre (reduction de la sur-confiance).

**Note methodologique** : Ces hypotheses reposent sur les mecanismes theoriques de Kahneman (Systeme 2 = meilleure qualite, cout temporel plus eleve) et sur les travaux de Bergamaschi Ganapini et al. (2025) sur la metacognition en IA. Aucune etude empirique n'a encore teste ces protocoles specifiques en contexte operationnel militaire. Cette phase 2 est precisement concue pour generer ces donnees empiriques.

#### Phase 3 -- Deploiement operationnel (continu)

**Integration institutionnelle.**

Premierement, **Second Brain en standard** pour tous les analystes du renseignement : instruction permanente dans outils IA utilises, revision trimestrielle des performances.

Deuxiemement, **Prompt de Lucidite obligatoire** pour decisions de niveau tactique ou superieur : integre dans procedures de decision formelles, documentation dans ordres d'operation.

Troisiemement, **AAR systematique avec Cognitive Bias Detective** : apres chaque operation significative, identification des patterns de biais recurrents, adaptation de la formation continue.

Quatriemement, **exercices reguliers** (trimestriels) : nouveaux scenarios de guerre cognitive, mise a jour des protocoles selon l'evolution des menaces.

### Recommandations pour le NATO Defense College

Sur la base de ce guide et du papier de Paquet (2022), voici des recommandations operationnelles pour l'Alliance.

#### 1. Creation d'un "Cognitive Resilience Toolkit"

**Objectif** : Fournir aux nations membres un ensemble standardise de protocoles et d'exercices pour former a la defense cognitive.

**Contenu propose** : les 6 protocoles de ce guide (adaptes aux contextes nationaux), une bibliotheque de scenarios de guerre cognitive (anonymises), une plateforme d'echange de bonnes pratiques entre nations, et des metriques d'evaluation de la resilience cognitive (pre/post formation).

**Alignement avec NWCC** : Repond directement a l'imperatif "cognitive superiority" identifie par le NATO Warfighting Capstone Concept.

#### 2. Integration dans le NATO Academia Forum

Comme le recommande Paquet : "La premiere etape [...] pourrait etre pour l'OTAN de mettre en place un forum sur le modele du NATO Academia Forum. L'objectif global est de creer un cadre ou les nations pourraient partager le savoir-faire, ameliorer les competences en metacognition, et developper la pensee critique."

**Proposition concrete** : module "Cognitive Warfare Defense" dans tous les cursus du NDC, certification "Cognitive Resilience Instructor" pour formateurs nationaux, exercices combines de guerre cognitive (comme les exercices cyber).

#### 3. Developpement d'un "Cooperative Cognitive Awareness Centre"

Paquet propose : "L'OTAN pourrait creer le cadre d'un Cooperative Cognitive Awareness Centre."

**Architecture proposee avec ces protocoles** :

```
NATO COOPERATIVE COGNITIVE AWARENESS CENTRE

MODULE 1 : DETECTION
  Monitoring campagnes desinformation
  Cognitive Bias Detective automatise
  Identification patterns d'attaque

MODULE 2 : ANALYSE
  Synthetic Layer of Thought pour scenarios
  Evaluation impact potentiel
    sur moral/decisions
  Attribution (dans limites du possible)

MODULE 3 : CONTRE-MESURES
  Developpement contre-narratives
    (transparent)
  Fact-checking coordonne entre nations
  Formation continue personnel expose

MODULE 4 : RECHERCHE ET DEVELOPPEMENT
  Veille sur evolution capacites IA adverses
  Test nouveaux protocoles defense cognitive
  Cooperation academique
    (AI safety, cog. science)

PRINCIPES OPERATOIRES
  Legalite : Respect vie privee, cadre RGPD
  Transparence : Methodes publiques
    (pas offensif)
  Coordination : Partage info entre nations
    (NCIRC)
  Reactivite : Alerte rapide,
    contre-mesure dans les meilleurs delais
```

---

## Ce que ces protocoles ne peuvent pas faire

Ces outils sont puissants. Ils ne sont pas magiques.

### Aucun protocole ne garantit la verite

Un LLM peut produire un "resume auditable" qui a l'apparence de la rigueur tout en contenant des erreurs factuelles. **La responsabilite de la verification reste toujours entre vos mains.**

En contexte operationnel : Ces protocoles structurent le raisonnement, ils ne remplacent pas la confirmation par sources independantes (SIGINT, HUMINT, IMINT).

### Aucun protocole ne remplace l'expertise humaine

Si vous utilisez ces outils pour des decisions strategiques ou tactiques, ils sont un **point de depart** -- pas un substitut au jugement d'un commandant experimente, d'un analyste senior, ou d'un conseiller juridique.

Comme l'ecrit Paquet : "La question est de savoir comment le controle est equilibre entre humains et IA, comment la coordination humain-machine fonctionne reellement, et comment l'information est integree pour produire connaissance et decision."

### Aucun protocole ne rend l'IA consciente

Les termes "percevoir", "ressentir", "reflechir" utilises dans ces protocoles sont des **metaphores fonctionnelles**. Le modele n'a ni perception, ni emotions, ni conscience de soi. Ce qu'il a, c'est une capacite remarquable a structurer du texte selon les instructions -- et c'est exactement ce que ces protocoles exploitent.

**En contexte militaire** : Ces protocoles sont des exercices de pensee structuree, transposables aux situations de decision reelle (sans IA). Leur valeur principale est pedagogique : ils entrainent a une discipline mentale de defense cognitive.

---

## Conclusion -- De la theorie a la pratique

### Ce que change l'ere de l'information pour la defense

Comme le conclut Paquet : "Le nouvel environnement dans lequel les combattants de l'OTAN doivent operer est incroyablement plus incertain et risque qu'il ne l'a ete jusqu'a present, necessitant que nous passions du brouillard de la guerre a la lumiere aveuglante de l'information massive."

Ce guide propose des outils concrets pour naviguer dans cette "lumiere aveuglante" : **ralentir** quand tout pousse a la reponse rapide, **expliciter** les hypotheses implicites et les zones d'incertitude, **contredire** systematiquement pour eviter le biais de confirmation, **verifier** avant de decider, tester apres avoir decide.

### Les trois niveaux d'application

Ces protocoles fonctionnent a trois niveaux. Au **niveau individuel**, un analyste, un planificateur, un commandant utilise ces outils pour structurer sa propre reflexion. Au **niveau collectif**, une equipe utilise ces protocoles dans ses processus de decision (war gaming, analyse collaborative, debriefing). Au **niveau institutionnel**, une organisation integre ces protocoles dans ses doctrines, ses formations, et ses procedures standards.

### Prochaines etapes recommandees

**Pour les individus** : choisir un protocole (recommande : Prompt de Lucidite), l'utiliser sur 5 decisions reelles (faible enjeu pour commencer), et observer quels biais sont detectes et quelles alternatives emergent.

**Pour les institutions de defense** : phase pilote sur une unite volontaire (3 mois), mesure de la qualite des decisions, du temps, de la detection des biais et de la satisfaction des utilisateurs, ajustement des protocoles aux contextes operationnels specifiques, puis deploiement progressif selon les priorites (renseignement, planification, commandement).

**Pour l'OTAN** : integrer ces protocoles dans le NATO Academia Forum propose par Paquet, developper des exercices de guerre cognitive combines (comme les exercices cyber), creer une bibliotheque de scenarios partagee entre nations, et mesurer l'efficacite de ces protocoles dans des contextes operationnels reels.

### Une derniere reflexion

Ces protocoles ne rendent pas l'IA plus intelligente. **Ils vous rendent plus exigeant envers elle -- et envers vous-meme.**

Et cette exigence, cette discipline de la pensee structuree, de la contradiction systematique, de la verification permanente, c'est exactement ce que la guerre cognitive cherche a detruire.

En ce sens, maitriser ces protocoles n'est pas qu'une competence technique. **C'est un acte de resistance cognitive.**

---

## Bibliographie

### Sources academiques primaires (T1)

**Sur l'IA et les biais cognitifs**

<!-- PATCH 3.1 : "Nature" → "Nature Portfolio / npj Artificial Intelligence" -->
Bergamaschi Ganapini, M., Campbell, M., Fabiano, F. et al. (2025). "Fast, slow, and metacognitive thinking in AI." *npj Artificial Intelligence* (Nature Portfolio), 1, 27. DOI : 10.1038/s44387-025-00027-5

Disponible :
https://www.nature.com/articles/s44387-025-00027-5

Salecha, A., Ireland, M. E., et al. (2024). "Large Language Models Display Human-like Social Desirability Biases in Big Five Personality Surveys." *PNAS Nexus*, 3(12), pgae533. DOI : 10.1093/pnasnexus/pgae533

Disponible :
https://academic.oup.com/pnasnexus/article/3/12/pgae533/7919163

<!-- PATCH 3.2 : correction statut Ross et al. -->
Ross, J., Kim, Y. et Lo, A. W. (2024). "LLM Economicus? Mapping the Behavioral Biases of LLMs via Utility Theory." Prepublication arXiv : 2408.02784, **version listee sur OpenReview (COLM 2024)**.

arXiv :
https://arxiv.org/abs/2408.02784

OpenReview :
https://openreview.net/forum?id=Rx3wC8sCTJ

<!-- PATCH 3.3 : SSRN = working paper explicite -->
Meincke, L., et al. (2025). "Call Me A Jerk: Persuading AI to Comply with Objectionable Requests." SSRN n. 5357179 -- **working paper / prepublication (non evalue par comite de lecture sauf indication contraire)**. DOI : 10.2139/ssrn.5357179

Disponible :
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5357179

**Sur la guerre cognitive et la defense**

Paquet, A. (2022). "A brief overview of cognitive warfare in light of the emerging Information Age." *NATO Defense College, College Series No. 27*, April 2022.

Disponible :
https://www.ulib.sk/files/english/nato-library/collections/monographs/documents-nato-defence-college/ndc-college-series/cs5-27_capt_paquet.pdf

Waltzman, R. (2017). "The Weaponization of Information: The Need for Cognitive Security." RAND Corporation, CT-473.

Page :
https://www.rand.org/pubs/testimonies/CT473.html

PDF :
https://www.rand.org/content/dam/rand/pubs/testimonies/CT400/CT473/RAND_CT473.pdf

Johns Hopkins University et Imperial College London (2021). "Countering cognitive warfare: awareness and resilience." *NATO Review*, 20 May 2021.

URL originale (inaccessible lors de la consultation -- 2026-02-08) :
https://www.nato.int/docu/review/articles/2021/05/20/countering-cognitive-warfare-awareness-and-resilience/index.html

**Validation de l'existence et des metadonnees** : cite dans Lahmann, H. (2025), "The fundamental rights risks of countering cognitive warfare with artificial intelligence", *Ethics and Information Technology*, DOI : 10.1007/s10676-025-09868-9, PMC12500826 (disponible : https://pmc.ncbi.nlm.nih.gov/articles/PMC12500826/). Egalement cite dans Reczkowski, R. et Lis, A. (2023), "Cognitive Warfare: what is our actual knowledge and how to build state resilience" (disponible : https://2050.su/wp-content/uploads/2023/02/CW_T21.-CW-what-is-our-actual-knowledge-and-how-to-build-state-resilience.pdf).

**Note d'auditabilite** : Le contenu de la page NATO Review n'a pas pu etre audite directement depuis la source primaire (inaccessibilite technique lors de la consultation). Son existence, son titre, ses auteurs et sa date sont valides par citations multiples dans la litterature academique avec comite de lecture. **Contenu non audite en source primaire.**

NATO Strategic Communications Centre of Excellence. (2016). "Daesh Information Campaign and its Influence."

Page :
https://stratcomcoe.org/publications/daesh-information-campaign-and-its-influence/156

PDF :
https://stratcomcoe.org/publications/download/daesh_public_use_19-08-2016.pdf

### Ouvrages de reference (T1)

Kahneman, D. (2011). *Thinking, Fast and Slow.* Farrar, Straus and Giroux. ISBN : 978-0374275631

Ellul, J. (1965). *Propaganda: The Formation of Men's Attitudes.* Traduit par Konrad Kellen et Jean Lerner. New York : Knopf. ISBN : 978-0394718743

Slovic, P., Finucane, M. L., Peters, E. et MacGregor, D. G. (2007). "The affect heuristic." *European Journal of Operational Research*, 177(3), 1333-1352. DOI : 10.1016/j.ejor.2005.04.006

Disponible :
https://www.sciencedirect.com/science/article/pii/S0377221705003577

### Sources institutionnelles et working papers (T2)

Ministere des Armees francais. (2021). *Elements publics de doctrine militaire de lutte informatique d'influence (L2I).* Octobre 2021.

PDF :
https://www.defense.gouv.fr/sites/default/files/ema/doctrine_de_lutte_informatique_dinfluence_l2i.pdf

Page institutionnelle :
https://www.defense.gouv.fr/comcyber/nos-operations/lutte-informatique-dinfluence-l2i

Gerasimov, V. (2016). "The Value of Science Is in the Foresight: New Challenges Demand Rethinking the Forms and Methods of Carrying Out Combat Operations." *Military Review*, January-February 2016.

Page :
https://www.armyupress.army.mil/Journals/Military-Review/English-Edition-Archives/January-February-2016/

PDF :
https://www.armyupress.army.mil/portals/7/military-review/archives/english/militaryreview_20160228_art008.pdf

### Sources citees mais non localisees en source primaire (T3)

Cole, A. et Le Guyader, H. (2020). "NATO's Sixth Domain of Operations?" NATO Innovation Hub, September 2020. Source primaire non localisee lors de la consultation -- 2026-02-08.

**Validation indirecte** : cite dans Claverie, B. (2021), "Qu'est-ce que la cognition et comment en faire l'un des moyens de la guerre ?", HAL-03424899 (disponible : https://hal.archives-ouvertes.fr/hal-03424899/document). Egalement cite dans du Cluzel, F. (2021), "Cognitive Warfare", NATO ACT Innovation Hub. URL mentionnee (non verifiee) : https://www.innovationhub-act.org/sites/default/files/2021-01/NATO%27s%206th%20domain%20of%20operations.pdf

**Note** : Cette reference est conservee car largement citee dans la litterature OTAN, mais son statut de source primaire n'a pas pu etre confirme directement. A utiliser avec prudence jusqu'a localisation du document officiel.

### Protocoles communautaires (T4 -- Usage exploratoire)

**AVERTISSEMENT METHODOLOGIQUE** : Les protocoles ci-dessous proviennent de communautes d'utilisateurs (Reddit, Substack) et n'ont PAS fait l'objet de validation scientifique par comite de lecture. Ils constituent des **heuristiques pratiques** developpees par des praticiens, utilisees ici comme point de depart pour structurer des exercices de reflexion. Leur efficacite reelle doit etre testee empiriquement avant tout deploiement operationnel.

Reddit r/ClaudeAI -- u/Safe-Clothes5925 -- "Synthetic Layer of Thought Process" [Consulte : 2026-02-08]

Reddit r/ChatGPTPro -- u/PopPsychological8148 -- "Psychology Based Decision Making Prompt" [Consulte : 2026-02-08]

Reddit r/ChatGPTPromptGenius -- u/Tall_Ad4729 -- "Cognitive Bias Detective" [Consulte : 2026-02-08]

Substack -- AIble With My Mind -- "How I Use ChatGPT to Catch My Biases" [Consulte : 2026-02-08]

Behavioural By Design -- Vishal George -- "Prompt That Teaches AI When to Think Again" [Consulte : 2026-02-08]

### Methodologie de ce guide

Ce guide s'appuie sur trois types de sources. Premierement, un **cadre theorique (T1)** constitue de recherche academique validee par comite de lecture (Kahneman, npj Artificial Intelligence, PNAS Nexus, COLM) et de documents institutionnels OTAN/RAND/Ministeres de la Defense. Deuxiemement, des **protocoles operationnels (T4)** constitues d'adaptations de protocoles communautaires reformules pour auditabilite et contexte militaire/strategique -- statut epistemique : heuristiques exploratoires, NON validees empiriquement. Troisiemement, une **validation proposee** sous forme de tests empiriques recommandes avant deploiement institutionnel (Phase 2 du protocole d'entrainement, Chapitre 8).

### Limites de tracabilite documentees

**1. NATO Review (2021) -- "Countering cognitive warfare: awareness and resilience"**

Existence confirmee par citations multiples dans litterature academique avec comite de lecture (Lahmann 2025 / PMC12500826, Reczkowski 2023, et al.). Metadonnees validees (titre, auteurs, date, URL officielle). Page originale inaccessible lors de la consultation (2026-02-08) -- impossibilite d'auditer le contenu directement depuis la source primaire. **Contenu integral non audite.**

**Recommandation pour verification** : Consulter Lahmann (2025) PMC12500826 qui cite et contextualise l'article NATO Review, ou rechercher archives institutionnelles OTAN.

**2. Cole et Le Guyader (2020) -- "NATO's Sixth Domain of Operations?"**

Source primaire non localisee lors de la consultation (2026-02-08). Document largement cite dans litterature OTAN (Claverie 2021, du Cluzel 2021). Classe en T3 (validation indirecte) jusqu'a localisation du PDF officiel.

**Recommandation** : Utiliser avec prudence ; privilegier les citations directes des auteurs dans d'autres documents OTAN verifies.

---

**Ce guide est un outil de defense cognitive. Partagez-le librement.**

**Version finale -- auditabilite documentee (sources et limites explicites) -- 2026-02-08**

---

## Changelog v1.0 (2026-02-08)

```
ebook-defense-cognitive_v1.0_2026-02-08

Modifications appliquees par rapport a la version
source (ebook_v1_source.md) :

1. "certifiee" / "certifiee auditable"
   → "auditabilite documentee
      (sources et limites explicites)"

2. "publication Nature"
   → "article Nature Portfolio publie dans
      npj Artificial Intelligence"

3. Ross et al. "Accepte a COLM 2024"
   → "Prepublication arXiv, version listee
      sur OpenReview (COLM 2024)"

4. Meincke et al. (SSRN)
   → mention explicite "working paper /
      prepublication (non evalue par comite
      de lecture)"

5. Ajout criteres minimaux d'inclusion T4
   (securite, stabilite, test interne)

6. Ajout section "Modes d'echec frequents
   (Failure modes)"

7. Ajout encadre "Statut du document + donnees"
   apres "A propos de ce guide"

8. Prompts FR + EN pour chapitres 1, 3, 4, 5
   (FR en reference, EN en source)

9. Chapitre 7 : ajout encadre "exemple
   pedagogique uniquement" ;
   neutralisation elements trop proceduraux
   ("sous 60 sec" → "delai compatible
   avec la menace", "engagement autorise"
   → "option envisageable sous reserve
   ROE/autorisation", suppression durees
   de type SOP universelle)

10. Tableaux larges remplaces par listes
    structurees A5-safe (resume executif,
    chapitre 8)

11. Emojis supprimes dans les en-tetes

12. Blocs de code reflows pour A5
    (lignes courtes)

13. URLs bibliographie sur lignes separees

14. H1 ajoute en tete de document

15. Suppression wrapper markdown global
    (regle anti-casse backticks)
```
