# Cahier des charges — EpiFlipBoard

## 1. Introduction

### 1.1 Contexte

Le projet EpiFlipBoard vise à concevoir une application web (et potentiellement mobile) d'agrégation de contenus (articles, médias) à l'image de Flipboard, permettant aux utilisateurs de « feuilleter » les actualités selon leurs centres d'intérêt.
Ce projet est réalisé avec des attentes en termes de rigueur technique (Docker, CI/CD, documentation, tests, etc.).

### 1.2 Objectifs

- Proposer une interface agréable permettant de naviguer dans des articles / contenus issus de multiples sources.
- Permettre à l'utilisateur de personnaliser son flux selon ses intérêts (thèmes, sources).
- Fournir des outils de sauvegarde (favoris, lecture plus tard).
- Intégrer des fonctionnalités de recherche, tri, suggestions de contenus connexes.
- Mettre en place l'infrastructure complète (backend, frontend, conteneurisation, pipeline CI/CD, documentation, tests).
- Simuler un environnement professionnel (gestion de versions, issues, livrables, démonstration).

### 1.3 Public cible / Personas

- **Lecteur curieux** : souhaite rester informé des thèmes qui l'intéressent.
- **Veilleur / curateur** : souhaite sélectionner des sources spécifiques, conserver des articles pertinents.

### 1.4 Benchmark et inspiration

- Flipboard : interface de type "magazine", navigation fluide, recommandations de sujets, personnalisation du flux.
- Services d'agrégation / lecture de contenus (Feedly, Inoreader, etc.).

---

## 2. Périmètre fonctionnel

### 2.1 Fonctionnalités principales (MVP)

| Fonctionnalité                                                        | Description                                                                                                                    | Critères de réussite                                                                           |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Accueil / Flux personnalisé**                                 | Afficher un flux d'articles personnalisés selon les thèmes / sources sélectionnés                                          | L'utilisateur voit une sélection d'articles pertinents à ses intérêts dès sa page d'accueil |
| **Navigation / "feuilletage"**                                   | Présenter les articles sous forme de cartes / vignettes, avec effet visuel de "flip" ou défilement fluide                    | Le scroll / pagination doit être fluide, l'interface séduisante                                |
| **Recherche / exploration**                                      | Permettre de rechercher des mots-clés, des sujets ou des sources                                                              | Résultats pertinents remontés, interface de recherche claire                                   |
| **Filtrage / thèmes / catégories**                             | Offrir des filtres par thème (ex : technologie, sports, culture) ou par source                                                | L'utilisateur peut restreindre ou étendre son flux selon ses préférences                      |
| **Favoris / Lecture plus tard**                                  | Possibilité de marquer un article pour le relire ultérieurement                                                              | Une liste personnelle de favoris est accessible                                                  |
| **Suggestions / articles similaires**                            | Montrer, à la fin de chaque article affiché, des articles proches ou recommandés                                            | Algorithme simple (mots-clés, même thème) pour proposer du contenu lié                       |
| **Compte utilisateur & personnalisation (optionnel ou avancé)** | Inscription / connexion / gestion du profil utilisateur / choix des thèmes / sources favorites / personnalisation des options | Chaque utilisateur dispose de ses propres réglages et favoris                                   |
| **Intégration de médias (images, vidéos)**                    | Afficher les images associées aux articles, intégrer les vidéos si supporté                                                | L'interface doit pouvoir afficher médias et respecter les liens externes                        |
| **Partage d'articles**                                           | Permettre de partager un article via lien social, email, etc.                                                                  | Fonction share standard (Facebook, Twitter, email)                                               |
| **Cache / chargement optimisé**                                 | Charger les articles progressivement, mettre en cache les données, éviter les appels redondants                              | Performance acceptable même avec un grand nombre d'articles                                     |
| **Responsive / adaptatif**                                       | Interface adaptée aux différentes tailles d'écrans                                                                          | Le site doit être pleinement utilisable quel que soit l'appareil                                |
| **Créer et gérer des "journaux" personnels**                   | Permettre à l'utilisateur de créer des journaux                                                                              | L'utilisateur peut créer un journal et y ajouter ses articles                                   |
| **Documentation technique**                                      | Fournir une documentation complète (API, installation, utilisation)                                                           | Documentation claire et accessible                                                               |
| **Tests automatisés**                                           | Couverture de tests unitaires et d'intégration pour les composants critiques                                                  | Tests passent avec succès dans le pipeline CI/CD                                                |
| **Pipeline CI/CD**                                               | Mise en place d'un pipeline d'intégration et de déploiement continu                                                          | Déploiement automatisé fonctionnel via Docker                                                  |
| **Conteneurisation (Docker)**                                    | Conteneuriser les composants (frontend, backend, base de données)                                                             | Application déployable via Docker / docker-compose                                              |
| **Collecte / agrégation de flux**                               | Récupérer des articles depuis des flux RSS / APIs externes                                                                   | Module de collecte fonctionnel, articles mis à jour régulièrement                             |

### 2.2 Fonctionnalités annexes

- Notifications (email, push) sur nouveaux articles dans un thème
- Classement des articles selon popularité / nombre de favorisation
- Importation de flux personnalisés (RSS privés, flux externes)
- Édition / commentaire des articles (modération)
- Internationalisation (multilingue) -> anglais / français / coréen

### 2.3 Fonctionnalités optionnelles / futures

Ces fonctionnalités pourront être envisagées pour des versions ultérieures, mais ne sont pas détaillées dans ce cahier des charges initial.

- Panel d'administration pour gérer les sources, modérer les contenus et utilisateurs

---

## 3. Spécifications fonctionnelles détaillées

### 3.1 Use Cases

#### 3.1.1 Consulter le flux d'articles

- **Acteur** : Utilisateur (connecté ou non)
- **Préconditions** : Le backend a agrégé des articles depuis les sources
- **Scénario** :
  1. L'utilisateur accède à la page d'accueil
  2. L'application affiche les cartes d'articles (image, titre, source, date, extrait)
  3. L'utilisateur fait défiler le flux pour charger d'autres articles
  4. Lorsqu'il clique sur une carte, celle-ci se retourne ou s'ouvre pour afficher plus de détails ainsi que le lien vers l'article complet (ouverture dans un nouvel onglet)
- **Postconditions** : L'utilisateur voit une sélection d'articles, peut naviguer dans le flux

#### 3.1.2 Marquer un article comme favori

- **Acteur** : Utilisateur (connecté)
- **Préconditions** : L'utilisateur est authentifié et dispose d'un espace Favoris personnel
- **Scénario** :
  1. L'utilisateur clique sur l'icône "favori" sur un article
  2. Le système enregistre l'article dans la liste de favoris
  3. Si l'utilisateur consulte sa page "Favoris", il y retrouve l'article
- **Postconditions** : L'article est enregistré, accessible via la page dédiée

#### 3.1.3 Recherche / filtre

- **Acteur** : Utilisateur
- **Scénario** :
  1. L'utilisateur saisit un mot-clé ou sélectionne un thème / source
  2. Le frontend envoie la requête (avec filtres) au backend
  3. Le backend renvoie la liste d'articles correspondants
  4. Le frontend affiche les résultats
- **Postconditions** : L'utilisateur obtient une liste filtrée / pertinente

#### 3.1.4 S'inscrire sur la plateforme

- **Acteur** : Visiteur
- **Préconditions** : Le visiteur ne possède pas encore de compte et dispose d'une adresse email valide
- **Scénario** :
  1. Le visiteur ouvre la page d'inscription
  2. Il renseigne les informations demandées (email, mot de passe, éventuellement prénom)
  3. Il accepte les conditions d'utilisation et valide le formulaire
  4. Le système crée le compte
- **Postconditions** : Un compte utilisateur actif est enregistré

#### 3.1.5 Se connecter à son espace

- **Acteur** : Utilisateur inscrit
- **Préconditions** : Le compte est actif et l'utilisateur connaît ses identifiants
- **Scénario** :
  1. L'utilisateur ouvre la page de connexion
  2. Il saisit ses identifiants et valide
  3. Le système authentifie l'utilisateur et initialise une session (token, cookie)
- **Postconditions** : L'utilisateur accède à ses fonctionnalités personnalisées

#### 3.1.6 Se déconnecter de la plateforme

- **Acteur** : Utilisateur connecté
- **Préconditions** : Une session est active
- **Scénario** :
  1. L'utilisateur clique sur l'action « Se déconnecter »
  2. Le système invalide la session en cours
  3. L'utilisateur est redirigé vers une page publique
- **Postconditions** : La session est fermée et les données utilisateur sont protégées

#### 3.1.7 Réinitialiser son mot de passe

- **Acteur** : Utilisateur inscrit
- **Préconditions** : L'utilisateur a oublié son mot de passe et son email est enregistré
- **Scénario** :
  1. L'utilisateur clique sur « Mot de passe oublié »
  2. Il renseigne son adresse email
  3. Le système envoie un lien ou un code de réinitialisation
  4. L'utilisateur choisit un nouveau mot de passe via le formulaire sécurisé
- **Postconditions** : Le mot de passe est mis à jour, l'utilisateur peut se reconnecter

#### 3.1.8 Mettre à jour son profil utilisateur

- **Acteur** : Utilisateur connecté
- **Préconditions** : L'utilisateur est authentifié
- **Scénario** :
  1. L'utilisateur accède à la page Profil / Compte
  2. Il modifie ses informations personnelles (nom, avatar) ou consulte ses données (favoris, historique)
  3. Il sauvegarde les modifications
- **Postconditions** : Les informations de profil sont mises à jour côté backend et reflétées dans l'interface

#### 3.1.9 Suggestion d'articles similaires

- **Acteur** : Utilisateur
- **Scénario** :
  1. L'utilisateur consulte un article
  2. En dessous / à côté, l'interface propose des articles "similaires"
  3. L'utilisateur peut cliquer sur ces propositions
- **Postconditions** : L'utilisateur accède à du contenu potentiellement pertinent

#### 3.1.10 Personnaliser ses thèmes et sources

- **Acteur** : Utilisateur connecté
- **Préconditions** : L'utilisateur dispose d'un compte et d'une liste de thèmes / sources disponibles
- **Scénario** :
  1. L'utilisateur ouvre la page Profil / Préférences
  2. Il sélectionne ou désélectionne des thèmes et sources recommandés
  3. Il valide ses nouveaux choix
  4. Le système met à jour les préférences et recharge le flux utilisateur
- **Postconditions** : Les préférences mises à jour influencent immédiatement le flux personnalisé

#### 3.1.11 Créer un journal personnel

- **Acteur** : Utilisateur connecté
- **Scénario** :
  1. L'utilisateur accède à la section "Mes journaux"
  2. Il clique sur "Nouveau journal" et saisit un titre et, si souhaité, une description
  3. Le système crée le journal vide
- **Postconditions** : Un journal personnel est disponible dans l'espace de l'utilisateur

#### 3.1.12 Rédiger un article dans son journal

- **Acteur** : Utilisateur connecté
- **Préconditions** : Au moins un journal personnel existe et l'utilisateur dispose des droits d'édition
- **Scénario** :
  1. Depuis la vue d'un journal, l'utilisateur sélectionne l'action « Nouvel article »
  2. Il saisit le contenu (titre, texte, médias, tags) et choisit le statut (brouillon ou publié)
  3. Il enregistre l'article en respectant le statut choisi
  4. Le système stocke l'article et l'associe au journal
- **Postconditions** : L'article apparaît dans le journal, prêt à être consulté ou édité ultérieurement

#### 3.1.13 Ajouter un article à un journal

- **Acteur** : Utilisateur connecté
- **Préconditions** : Au moins un journal personnel existe
- **Scénario** :
  1. Depuis une carte d'article, l'utilisateur sélectionne l'option "Ajouter au journal"
  2. Il choisit le journal cible ou en crée un nouveau à la volée
  3. Le système associe l'article au journal
- **Postconditions** : L'article apparaît dans le journal choisi

#### 3.1.14 Partager un article

- **Acteur** : Utilisateur
- **Scénario** :
  1. L'utilisateur clique sur le bouton de partage d'une carte d'article
  2. L'application ouvre les options de partage (réseaux sociaux, email, copie de lien)
  3. L'utilisateur sélectionne un canal et confirme
- **Postconditions** : Le lien de l'article est transmis via le canal choisi

#### 3.1.15 Gérer les notifications de nouveaux contenus

- **Acteur** : Utilisateur connecté
- **Préconditions** : Les notifications sont activées côté système
- **Scénario** :
  1. L'utilisateur accède à ses préférences de notification
  2. Il active les alertes pour un ou plusieurs thèmes / journaux
  3. Lorsqu'un nouvel article correspondant est disponible, le système envoie une notification sur l'interface web ou par email
  4. L'utilisateur ouvre la notification et accède directement à l'article ou au journal concerné
- **Postconditions** : L'utilisateur est tenu informé des nouveaux contenus pertinents

#### 3.1.16 Gérer ses favoris (voir / retirer)

- Acteur : Utilisateur connecté
- Scénario :
  1. L'utilisateur ouvre la page Favoris
  2. Il parcourt ses favoris, éventuellement avec pagination
  3. Il peut retirer un article des favoris
- Postconditions : La liste de favoris reflète les changements

#### 3.1.17 Modifier ou supprimer un journal

- Acteur : Utilisateur connecté
- Préconditions : Le journal existe et appartient à l'utilisateur
- Scénario :
  1. Depuis « Mes journaux », l'utilisateur choisit un journal
  2. Il modifie le titre/description/visibilité puis enregistre, ou supprime le journal
- Postconditions : Le journal est mis à jour ou supprimé

#### 3.1.18 Rendre un journal public et partager

- Acteur : Utilisateur connecté
- Préconditions : Un journal existe
- Scénario :
  1. L'utilisateur active l'option « Rendre public » pour un journal
  2. Le système génère/active un lien public partageable
- Postconditions : Le journal est accessible en lecture via une URL publique

#### 3.1.19 Retirer un article d'un journal

- Acteur : Utilisateur connecté
- Préconditions : Le journal existe et contient l'article
- Scénario :
  1. L'utilisateur ouvre le journal et localise l'article
  2. Il choisit « Retirer du journal »
- Postconditions : L'article n'apparaît plus dans le journal

#### 3.1.20 Gérer ses sources préférées

- Acteur : Utilisateur connecté
- Scénario :
  1. L'utilisateur ouvre ses préférences de sources
  2. Il ajoute/retire des sources suivies
  3. Le flux personnalisé s'actualise en conséquence
- Postconditions : Les sources favorites influencent le flux

### 3.2 Interfaces utilisateur (wireframes / écrans principaux)

1. **Page d'accueil / flux** : grille ou carte d'articles, barre de recherche, menu / filtres
2. **Article (aperçu / lien)** : image, titre, extrait, lien "Lire la suite", boutons (favori, partager)
3. **Page Favoris** : liste ou grille d'articles marqués
4. **Page Recherche / résultats** : résultats avec filtres appliqués
5. **Page Profil / Préférences** (si comptes) : choix de thèmes, gestion des sources
6. **Page Administration (back-office)** : gestion des sources, catégories, modération (optionnelle)

### 3.3 API / backend — endpoints & schéma

#### 3.3.1 Endpoints possibles

— Authentification et session

| Endpoint                     | Méthode | Paramètres / Body         | Description                             |
| ---------------------------- | -------- | -------------------------- | --------------------------------------- |
| `/v1/auth/register`        | POST     | `{ email, password }`    | Création de compte                     |
| `/v1/auth/login`           | POST     | `{ email, password }`    | Authentification et émission de tokens |
| `/v1/auth/refresh`         | POST     | `{ refreshToken }`       | Rafraîchit le token d'accès           |
| `/v1/auth/logout`          | POST     | -                          | Invalide la session/token               |
| `/v1/auth/forgot-password` | POST     | `{ email }`              | Demande de réinitialisation            |
| `/v1/auth/reset-password`  | POST     | `{ token, newPassword }` | Réinitialise le mot de passe           |

— Utilisateur

| Endpoint         | Méthode | Paramètres / Body                 | Description                           |
| ---------------- | -------- | ---------------------------------- | ------------------------------------- |
| `/v1/users/me` | GET      | -                                  | Récupère le profil de l'utilisateur |
| `/v1/users/me` | PUT      | `{ displayName, avatarUrl, … }` | Met à jour le profil                 |
| `/v1/users/me` | DELETE   | -                                  | Supprime le compte                    |

— Articles et découverte

| Endpoint                      | Méthode | Paramètres / Body                                                   | Description                    |
| ----------------------------- | -------- | -------------------------------------------------------------------- | ------------------------------ |
| `/v1/articles`              | GET      | `page`, `limit`, `sources`, `keywords`, `themes`, `sort` | Liste paginée d'articles      |
| `/v1/articles/{id}`         | GET      | -                                                                    | Détail d'un article           |
| `/v1/articles/{id}/similar` | GET      | `limit`                                                            | Articles similaires            |
| `/v1/articles`              | POST     | `{ title, excerpt, url, imageUrl, publishedAt, themes, sourceId }` | Ajoute un article sans journal |
| `/v1/articles/{id}`         | PUT      | `{ title, excerpt, url, imageUrl, publishedAt, themes, sourceId }` | Met à jour un article         |
| `/v1/articles/{id}`         | DELETE   | -                                                                    | Supprime un article            |

— Favoris

| Endpoint                         | Méthode | Paramètres / Body  | Description                        |
| -------------------------------- | -------- | ------------------- | ---------------------------------- |
| `/v1/me/favorites`             | GET      | `page`, `limit` | Liste des favoris de l'utilisateur |
| `/v1/me/favorites`             | POST     | `{ articleId }`   | Ajoute un favori                   |
| `/v1/me/favorites/{articleId}` | DELETE   | -                   | Retire un favori                   |

— Journaux (collections personnelles)

| Endpoint                                             | Méthode | Paramètres / Body                        | Description                                                     |
| ---------------------------------------------------- | -------- | ----------------------------------------- | --------------------------------------------------------------- |
| `/v1/me/journals`                                  | GET      | `page`, `limit`                       | Liste des journaux                                              |
| `/v1/me/journals`                                  | POST     | `{ title, description, visibility? }`   | Crée un journal                                                |
| `/v1/me/journals/{journalId}`                      | GET      | -                                         | Détail d'un journal (propriétaire)                            |
| `/v1/me/journals/{journalId}`                      | PUT      | `{ title?, description?, visibility? }` | Met à jour un journal                                          |
| `/v1/me/journals/{journalId}`                      | DELETE   | -                                         | Supprime un journal                                             |
| `/v1/journals/{journalId}`                         | GET      | `page`, `limit`                       | Consulte un journal public                                      |
| `/v1/me/journals/{journalId}/share`                | POST     | `{ public: boolean }`                   | Active/désactive le partage public                             |
| `/v1/me/journals/{journalId}/articles`             | GET      | `page`, `limit`                       | Liste les articles du journal                                   |
| `/v1/me/journals/{journalId}/articles`             | POST     | `{ articleId                              | title, excerpt, url, imageUrl, publishedAt, themes, sourceId }` |
| `/v1/me/journals/{journalId}/articles/{articleId}` | DELETE   | -                                         | Retire un article du journal                                    |

— Thèmes, tags et préférences

| Endpoint                    | Méthode | Paramètres / Body       | Description                         |
| --------------------------- | -------- | ------------------------ | ----------------------------------- |
| `/v1/themes`              | GET      | -                        | Liste des thèmes                   |
| `/v1/me/themes`           | GET      | -                        | Récupère les thèmes préférés  |
| `/v1/me/themes`           | PUT      | `{ themes: string[] }` | Met à jour les thèmes préférés |
| `/v1/me/themes/blacklist` | GET      | -                        | Récupère les thèmes blacklistés |
| `/v1/me/themes/blacklist` | PUT      | `{ themes: string[] }` | Met à jour la blacklist            |

— Sources

| Endpoint                     | Méthode | Paramètres / Body               | Description                          |
| ---------------------------- | -------- | -------------------------------- | ------------------------------------ |
| `/v1/sources`              | GET      | `page`, `limit`, `status?` | Liste des sources                    |
| `/v1/me/sources`           | GET      | -                                | Préférences de sources             |
| `/v1/me/sources`           | PUT      | `{ sources: string[] }`        | Met à jour les sources préférées |
| `/v1/me/sources/blacklist` | GET      | -                                | Récupère les sources blacklistées |
| `/v1/me/sources/blacklist` | PUT      | `{ sources: string[] }`        | Met à jour la blacklist             |

— Notifications

| Endpoint                 | Méthode | Paramètres / Body       | Description                   |
| ------------------------ | -------- | ------------------------ | ----------------------------- |
| `/v1/me/notifications` | GET      | -                        | Récupère les préférences  |
| `/v1/me/notifications` | PUT      | `{ channels, topics }` | Met à jour les préférences |

— Recherche

| Endpoint       | Méthode | Paramètres / Body                      | Description       |
| -------------- | -------- | --------------------------------------- | ----------------- |
| `/v1/search` | GET      | `q`, `filters`, `page`, `limit` | Recherche globale |

— Système

| Endpoint        | Méthode | Paramètres / Body | Description       |
| --------------- | -------- | ------------------ | ----------------- |
| `/v1/health`  | GET      | -                  | Santé du service |
| `/v1/version` | GET      | -                  | Version de l'API  |

#### 3.3.2 Modèle de données simplifié

- **User**

  - **Clé primaire** : `id`
  - **Clé étrangère** : `default_theme_pref_id` → `UserThemePreference.id`, `default_source_pref_id` → `UserSourcePreference.id`
  - **Champs principaux** : `email` (unique), `password_hash`, `created_at`, `updated_at`
- **Article**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `source_id` → `Source.id`
  - **Champs principaux** : `title`, `excerpt`, `url`, `image_url`, `published_at`, `themes`, `external_id` (unique par source)
- **Source**

  - **Clé primaire** : `id`
  - **Champs principaux** : `name`, `feed_url` / `api_url`, `logo`, `categories`, `status`
- **Journal**

  - **Clé primaire** : `id`
  - **Clé étrangère** : `owner_id` → `User.id`
  - **Champs principaux** : `title`, `description`, `created_at`, `updated_at`, `visibility` (privé / public)
- **JournalArticle** (relation n-n logique entre `Journal` et `Article`)

  - **Clé primaire** : `id`
  - **Clés étrangères** : `journal_id` → `Journal.id`, `article_id` → `Article.id` (nullable pas d'article), `author_id` → `User.id`
  - **Champs principaux** : `media`, `status` (brouillon / publié), `created_at`, `updated_at`
- **Favori**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `user_id` → `User.id`, `article_id` → `Article.id`
  - **Contraintes** : paire (`user_id`, `article_id`) unique
- **UserThemePreference**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `user_id` → `User.id`, `theme_id` → `Theme.id`
  - **Contraintes** : paire (`user_id`, `theme_id`) unique
- **UserSourcePreference**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `user_id` → `User.id`, `source_id` → `Source.id`
  - **Contraintes** : paire (`user_id`, `source_id`) unique
- **Theme**

  - **Clé primaire** : `id`
  - **Champs principaux** : `name` (unique), `slug`, `description`
- **NotificationPreference**

  - **Clé primaire** : `id`
  - **Clé étrangère** : `user_id` → `User.id`
  - **Champs principaux** : `channels` (email, in-app), `frequency` (temps réel, digest), `created_at`, `updated_at`
- **NotificationPreferenceTheme**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `notification_pref_id` → `NotificationPreference.id`, `theme_id` → `Theme.id`
  - **Contraintes** : paire (`notification_pref_id`, `theme_id`) unique
- **NotificationPreferenceSource**

  - **Clé primaire** : `id`
  - **Clés étrangères** : `notification_pref_id` → `NotificationPreference.id`, `source_id` → `Source.id`
  - **Contraintes** : paire (`notification_pref_id`, `source_id`) unique
- Les champs à valeurs finies (statuts, visibilité, canaux) vont être implémentés via des énumérations.

#### 3.3.3 Collecte / agrégation des flux

- Module de **polling / scheduler** (ex : cron ou tâche périodique)
- Pour chaque source définie, interroger le flux RSS / API, parser les articles, vérifier s'ils sont nouveaux (comparaison sur identifiant ou URL), enregistrer les nouveaux.
- Traitement des erreurs (flux inaccessibles, timeouts) et log des échecs

---

## 4. Contraintes non-fonctionnelles

### 4.1 Performance & scalabilité

- Pagination / lazy loading pour éviter de charger tous les articles d'un coup
- Cache (en mémoire ou persistant) pour éviter des appels externes fréquents
- Optimisation au niveau frontend (minification, bundling, chargement asynchrone)
- Compression des images / médias si possible
- Limiter les appels API externes inutilement fréquents

### 4.2 Sécurité

- Validation / sanitation des entrées utilisateur
- Protection contre injections SQL / NoSQL
- Hashage sécurisé des mots de passe (bcrypt, argon2)
- Utilisation de tokens JWT ou sessions sécurisées
- Contrôle d'accès pour les endpoints sensibles
- CORS configuré correctement entre front / backend
- Gestion sécurisée des clés API / secrets (ne pas les exposer dans le client)

### 4.3 Fiabilité / robustesse

- Gestion des erreurs (timeouts, flux morts, API indisponible) avec fallback / retry
- Logs des événements importants (erreurs, requêtes, échecs)
- Tests automatisés (unitaires, intégration, API)
- Surveillance / monitoring léger (logs, alertes basiques, santé des services)

### 4.4 Portabilité / déploiement

- Conteneurisation : Docker pour chaque composant (frontend, backend, base)
- Orchestration locale avec `docker-compose`
- Pipeline CI/CD pour les builds, tests, déploiement
- Possibilité de déployer sur un serveur
- Documentation d'installation / configuration

### 4.5 Expérience utilisateur / UI / accessibilité

- Interface responsive et fluide
- Chargement progressif et animations
- Bonne lisibilité (polices, contrastes)
- Accessibilité basique (thème sombre, langue)
- Navigation intuitive (menus, filtres, recherche)

### 4.6 Compatibilité & support navigateur

- Support des navigateurs modernes (Chrome, Firefox, Edge, Safari)
- Support mobile (iOS, Android via navigateur)
- Tests de compatibilité sur différentes tailles d'écran

---

## 5. Technologies recommandées

### 5.1 Frontend

- **React + TypeScript** : écosystème mature, composants réutilisables, bonne intégration pour projets SPA.

### 5.2 Backend

- **FastAPI (Python)** : performant, validation via Pydantic, documentation automatique (OpenAPI/Swagger).

### 5.3 Infrastructure / DevOps

- **Docker + docker-compose** : conteneurisation des services.
- **GitHub Actions** : pipeline CI/CD (tests, build, déploiement).
- **Swagger-UI / Redoc** : documentation interactive de l'API.

### 5.4 Tests & qualité

- **pytest** (Python): tests unitaires / intégration.
- **HTTPX** : tests d'API.
- **Cypress** : tests end-to-end (E2E).
- **ESLint + Prettier** : linting/formatage.

---

## 6. Architecture & urbanisation

### 6.1 Diagramme d'architecture (haut niveau)

> Frontend (application cliente)
> ↕ HTTP/HTTPS
> Backend (API)
> ↕ Base de données + cache
> ↕ Module de collecte / agrégation (cron / scheduler)
> ↕ Sources externes (flux RSS / APIs)

### 6.2 Flux de données simplifié

1. Le module de polling / scheduler interroge périodiquement les flux externes (RSS / API) pour chaque source.
2. Il parse les résultats, filtre les doublons, et stocke les nouveaux articles dans la base de données (PostgreSQL).
3. Le backend FastAPI expose des endpoints REST pour :
   • récupérer les articles (avec filtres, pagination)
   • gérer les favoris
   • gérer les utilisateurs / préférences
4. Le frontend React interroge l'API, affiche les articles, propose les filtres, gère l'interface utilisateur.
5. Lorsqu'un utilisateur marque un favori, le frontend envoie la requête POST à l'API, qui stocke la relation dans la base.

---

## 7. Planning & jalons proposés

| Phase                               | Début     | Durée estimée | Objectifs / livrables                                |
| ----------------------------------- | ---------- | --------------- | ---------------------------------------------------- |
| Cadrage & conception                | Jour 0     | 1 semaine      | Cahier des charges validé, wireframes, choix tech   |
| Initialisation / infrastructure     | +1 sem    | 1-2 semaines    | Structure du projet, Docker, dépôt Git, CI de base |
| Backend de base                     | +3 sem     | 2-3 semaines    | Module agrégation, API articles / endpoints de base |
| Frontend du flux                    | +3 sem     | 2-3 semaines    | Interface d'accueil, affichage des articles          |
| Recherche / filtres / suggestions   | +5-6 sem   | 1-2 semaines    | Moteur de recherche simple, filtres, recommandations |
| Favoris / personnalisation          | +7-8 sem   | 1-2 semaines    | Module de favoris, gestion utilisateur               |
| Tests / optimisation                | +9-10 sem  | 1 semaine       | Tests, corrections, optimisation performances        |
| Documentation / benchmark / rapport | +10-11 sem | 2 semaine       | Rédaction, comparaison avec Flipboard / concurrents |

Le temps supplémentaire disponible peut être utilisé pour ajouter des fonctionnalités annexes, améliorer l'UX/UI, ou approfondir les tests.

---

## 8. Critères de validation / recette

- Toutes les fonctionnalités du MVP fonctionnent correctement (flux, filtres, favoris, recherche).
- L'interface est responsive, fluide, sans bugs majeurs.
- Le backend est stable, les API répondent correctement, la collecte des flux marche en production.
- Les tests automatisés passent sans erreur.
- Le projet peut être monté et exécuté via docker-compose.
- La documentation (installation, API, manuel utilisateur) est claire et complète.
- Respect des contraintes de sécurité (ex : les données sensibles sont protégées).

---

## 9. Annexes & références

- Liste des sources potentielles (RSS / APIs publiques)
- Glossaire des termes (flux, API, pagination, etc.)
- Benchmark technique (outils, librairies utilisées)
- Schéma de la base de données (ERD)
- Diagrammes d'architecture détaillés
- Documentation des endpoints API (OpenAPI/Swagger)

---
