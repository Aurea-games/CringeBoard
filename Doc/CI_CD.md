# CI/CD GitHub Actions

CringeBoard s’appuie sur une unique pipeline GitHub Actions décrite dans `.github/workflows/ci.yml`. Elle garantit que les deux projets (backend et frontend) restent lintés, formatés et compilables avant intégration.

## Déclencheurs
- `push` sur `main`, `develop`, `feature/**`, `bugfix/**`
- `pull_request` sur n’importe quelle branche

Chaque exécution utilise une stratégie de concurrence (`concurrency`) qui annule la run précédente sur la même ref (`ci-<ref>`), ce qui évite les files d’attente inutiles pendant un rebase ou des pushes successifs.

## Jobs

### `backend` — lint & tests Python
Localisation : `backend/`

1. Checkout du dépôt.
2. Installation de Python 3.12 avec cache pip (dépendances `requirements.txt` et `requirements-dev.txt`).
3. Installation des dépendances runtime, tooling et de `pytest`.
4. Exécution de `ruff check app`.
5. Vérification de formatage avec `black --check app`.
6. Lancement de `pytest`. Si aucun test n’est détecté (`exit code 5`), le job continue et n’échoue pas.

### `frontend` — lint & build Node.js
Localisation : `frontend/`

1. Checkout du dépôt.
2. Installation de Node.js 20 et configuration du cache npm.
3. `npm ci` pour récupérer les dépendances.
4. `npm run lint` pour ESLint.
5. `npm run format:check` pour Prettier.
6. `npm run build` pour valider la compilation Vite/React.

Les deux jobs tournent en parallèle sur `ubuntu-latest`. Aucun secret supplémentaire n’est requis ; `GITHUB_TOKEN` par défaut est suffisant.

## Bonnes pratiques & évolutions
- **Tests backend** : enrichir la suite pytest au fur et à mesure pour obtenir une validation plus complète.
- **Tests frontend** : ajouter des commandes de test (ex. `npm test -- --watch=false`) si une suite Jest/Vitest est disponible.
- **Analyse de sécurité** : intégrer Trivy, Dependabot ou Snyk pour couvrir les vulnérabilités Docker, pip et npm.
- **Déploiement continu** : ajouter un job séparé (avec conditions sur la branche) pour construire et publier les images Docker ou déclencher un déploiement.

Voir également la section “CI/CD” du `README.md` pour un rappel rapide.
