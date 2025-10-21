# Specification Document — EpiFlipBoard

## 1. Introduction

### 1.1 Context
The EpiFlipBoard project aims to design a web (and possibly mobile) application for content aggregation (articles, media) inspired by Flipboard, enabling users to "flip through" news based on their interests. This project is carried out with expectations of technical rigor (Docker, CI/CD, documentation, tests, etc.).

### 1.2 Objectives
- Provide a pleasant interface allowing navigation through content (articles/media) from multiple sources.
- Enable the user to personalize their feed according to interests (themes, sources).
- Provide tools for saving (favorites, read-later).
- Integrate search, sorting, and related-content suggestions.
- Deploy a complete infrastructure (backend, frontend, containerization, CI/CD pipeline, documentation, tests).
- Simulate a professional environment (version control, issues, deliverables, demonstration).

### 1.3 Target audience / Personas
- **Curious reader**: wants to stay informed about themes that interest them.
- **Watcher / curator**: wants to select specific sources, save relevant articles.

### 1.4 Benchmark & inspiration
- Flipboard: magazine-style interface, smooth navigation, topic recommendations, feed personalization.
- Other content-aggregation / reading services (Feedly, Inoreader, etc.).

---

## 2. Functional Scope

### 2.1 Main functionalities (MVP)

| Functionality                                      | Description                                                                 | Success criteria                                                                  |
|---------------------------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Home / Personalized feed**                      | Display a feed of articles personalized by selected themes / sources        | The user sees a relevant selection of articles right after landing on the home page |
| **Navigation / "flipping"**                        | Present articles as cards/vignettes, with a "flip" visual effect or smooth scroll | Scrolling/pagination is fluid and the UI is appealing                           |
| **Search / exploration**                           | Allow searching by keywords, topics, or sources                             | Search results are relevant; UI is clear                                         |
| **Filtering / themes / categories**                | Offer filters by theme (e.g., technology, sports, culture) or source        | User can refine or broaden their feed via preferences                             |
| **Favorites / Read-later**                         | Allow marking an article for later reading                                  | The user has accessible list of favorites                                        |
| **Suggestions / similar articles**                 | Show articles related to the one being viewed                               | A simple algorithm (keywords, same theme) offers relevant related content         |
| **User account & personalization (optional/advanced)** | Registration / login / user profile / favorite themes & sources / personal settings | Each user has their own settings and favorites                                 |
| **Media integration (images, videos)**             | Display related images, integrate videos if supported                        | The UI supports media and respects external links                                |
| **Article sharing**                                | Allow sharing an article via link, social, email etc.                        | Standard share functionality (Facebook, Twitter, email)                           |
| **Caching / optimized loading**                    | Load articles progressively, cache data, avoid redundant calls               | Performance acceptable even with large volume of articles                         |
| **Responsive/adaptive design**                      | Interface adapted to different screen sizes                                  | The app works fully on any device                                                |
| **Create & manage personal "journals"**            | Allow user to create journals and add their articles                         | User can create a journal and add articles to it                                 |
| **Technical documentation**                         | Provide full documentation (API, installation, usage)                        | Documentation is clear and accessible                                            |
| **Automated tests**                                 | Coverage of unit & integration tests for critical components                   | Tests pass successfully in CI/CD pipeline                                        |
| **CI/CD pipeline**                                  | Set up continuous integration & deployment pipeline                          | Automated deployment via Docker works                                           |
| **Containerization (Docker)**                        | Containerize components (frontend, backend, database)                         | App deployable via Docker / docker-compose                                      |
| **Feed collection / aggregation**                    | Retrieve articles from external RSS feeds / APIs                             | Aggregation module working, articles updated regularly                          |

### 2.2 Additional functionalities
- Notifications (email, push) for new articles in a theme
- History
- Ranking of articles by popularity / number of favorites
- Import of custom feeds (private RSS, external feeds)
- Article editing / commenting (moderation)
- Internationalization (multilingual) → English / French / Korean

### 2.3 Optional / Future functionalities
These features may be considered for later versions but are **not** detailed in the initial specification:
- Admin panel for managing sources, moderating content and users

---

## 3. Detailed Functional Specifications

### 3.1 Use Cases

#### 3.1.1 Consult the feed of articles
- **Actor**: User (connected or not)
- **Preconditions**: The backend has aggregated articles from sources
- **Scenario**:
  1. The user opens the home page
  2. The application displays article cards (image, title, source, date, excerpt)
  3. The user scrolls the feed to load more articles
  4. When clicking on a card, it flips or opens to show more details and a link to the full article (opens in a new tab)
- **Postconditions**: The user sees a selection of articles and can browse them

#### 3.1.2 Mark an article as favorite
- **Actor**: Authenticated user
- **Preconditions**: The user is logged in and has an accessible favorites area
- **Scenario**:
  1. The user clicks on the "favorite" icon on an article
  2. The system records the article in the user's favorites list
  3. If the user visits the "Favorites" page, they see the article
- **Postconditions**: The article is saved and accessible via the favorites page

#### 3.1.3 Search / filter
- **Actor**: User
- **Scenario**:
  1. The user enters a keyword or selects a theme / source filter
  2. The frontend sends a request (with filters) to the backend
  3. The backend returns a list of matching articles
  4. The frontend displays the results
- **Postconditions**: The user gets a filtered / relevant list of articles

#### 3.1.4 Register on the platform
- **Actor**: Visitor
- **Preconditions**: The visitor doesn't have an account and has a valid email address
- **Scenario**:
  1. The visitor opens the registration page
  2. They fill in the required fields (email, password, optionally first name)
  3. They accept the terms of use and submit the form
  4. The system creates the account
- **Postconditions**: A new active user account is created

#### 3.1.5 Login to the platform
- **Actor**: Registered user
- **Preconditions**: The account is active and user knows login credentials
- **Scenario**:
  1. The user opens the login page
  2. They enter credentials and submit
  3. The system authenticates the user and starts a session (token or cookie)
- **Postconditions**: The user accesses personalized features

#### 3.1.6 Logout from the platform
- **Actor**: Authenticated user
- **Preconditions**: A session is active
- **Scenario**:
  1. The user clicks "Logout"
  2. The system invalidates the session
  3. The user is redirected to a public page
- **Postconditions**: Session ended and user data secured

#### 3.1.7 Reset password
- **Actor**: Registered user
- **Preconditions**: The user forgot the password and email is registered
- **Scenario**:
  1. The user clicks "Forgot password"
  2. They enter their email
  3. System sends a reset link or code
  4. The user enters a new password via secure form
- **Postconditions**: Password updated, user can login again

#### 3.1.8 Update user profile
- **Actor**: Authenticated user
- **Preconditions**: The user is logged in
- **Scenario**:
  1. The user navigates to "Profile/Account" page
  2. They modify personal info (name, avatar) or view data (favorites, history)
  3. They save changes
- **Postconditions**: Profile data updated and reflected in UI

#### 3.1.9 Suggest similar articles
- **Actor**: User
- **Scenario**:
  1. The user views an article
  2. Below/aside, the UI proposes "similar articles"
  3. The user clicks one of the suggested articles
- **Postconditions**: The user accesses additional relevant content

#### 3.1.10 Personalize themes and sources
- **Actor**: Authenticated user
- **Preconditions**: The user has an account and a list of available themes/sources
- **Scenario**:
  1. The user opens "Profile/Preferences"
  2. They select/deselect themes and sources
  3. They submit their preference changes
  4. The system updates preferences and refreshes the user feed
- **Postconditions**: Updated preferences immediately influence the personalized feed

#### 3.1.11 Create a personal journal
- **Actor**: Authenticated user
- **Scenario**:
  1. The user goes to "My Journals" section
  2. They click "New Journal", enter title and optionally description
  3. The system creates the blank journal
- **Postconditions**: A personal journal is available in the user's space

#### 3.1.12 Write a journal article
- **Actor**: Authenticated user
- **Preconditions**: At least one personal journal exists and user has editing rights
- **Scenario**:
  1. Within a journal view, user clicks "New Article"
  2. They enter content (title, text, media, tags) and choose status (draft or published)
  3. They save the article
  4. The system stores it and links to the journal
- **Postconditions**: The article appears in the journal and can be viewed/edited later

#### 3.1.13 Add an article to a journal
- **Actor**: Authenticated user
- **Preconditions**: A personal journal exists
- **Scenario**:
  1. From an article card, user selects "Add to Journal"
  2. They choose a target journal or create a new one on the fly
  3. The system links the article to the journal
- **Postconditions**: The article appears in the chosen journal

#### 3.1.14 Share an article
- **Actor**: User
- **Scenario**:
  1. The user clicks the share button on an article card
  2. The UI shows share options (social networks, email, copy link)
  3. The user selects a channel and confirms
- **Postconditions**: The article link is shared via the selected channel

#### 3.1.15 Manage notifications for new content
- **Actor**: Authenticated user
- **Preconditions**: Notifications feature activated in system
- **Scenario**:
  1. The user accesses their notification preferences
  2. They enable alerts for one or more themes/journals
  3. When a new article matching criteria appears, system sends a notification (web, email)
  4. The user clicks it and is taken to the article or journal
- **Postconditions**: User receives timely relevant content notifications

#### 3.1.16 Manage favorites (view / remove)
- **Actor**: Authenticated user
- **Scenario**:
  1. The user opens the Favorites page
  2. They browse their saved articles (with pagination)
  3. They remove an article from favorites if desired
- **Postconditions**: Favorite list reflects changes

#### 3.1.17 Modify or delete a journal
- **Actor**: Authenticated user
- **Preconditions**: The journal exists and belongs to user
- **Scenario**:
  1. From "My Journals", user selects a journal
  2. They edit title/description/visibility and save or choose to delete the journal
- **Postconditions**: Journal is updated or removed

#### 3.1.18 Make a journal public and share
- **Actor**: Authenticated user
- **Preconditions**: A journal exists
- **Scenario**:
  1. User activates "Make Public" option for journal
  2. System generates/activates shareable public link
- **Postconditions**: Journal is accessible in public read-only mode via URL

#### 3.1.19 Remove an article from a journal
- **Actor**: Authenticated user
- **Preconditions**: The journal exists and contains the article
- **Scenario**:
  1. User opens the journal, locates the article
  2. They choose "Remove from journal"
- **Postconditions**: The article no longer appears in the journal

#### 3.1.20 Manage preferred sources
- **Actor**: Authenticated user
- **Scenario**:
  1. User goes to source preferences section
  2. Adds/removes sources they follow
  3. User feed updates accordingly
- **Postconditions**: Feed is influenced by preferred sources

### 3.2 User Interfaces (wireframes / main screens)
1. **Home / feed page**: grid or card layout of articles, search bar, menu / filters
2. **Article (preview / link)**: image, title, excerpt, w"Read more" link, buttons (favorite, share)
3. **Favorites page**: list or grid of saved articles
4. **Search / results page**: results with applied filters
5. **Profile / Preferences page** (if accounts): choose themes, manage sources
6. **Admin page (back office)**: manage sources, categories, moderation (optional)

### 3.3 API / Backend — endpoints & schema

#### 3.3.1 Possible Endpoints
— **Authentication & Session**
| Endpoint                 | Method | Params / Body                         | Description                                               |
|--------------------------|--------|--------------------------------------|-----------------------------------------------------------|
| `/v1/auth/register`      | POST   | `{ email, password }`                 | Create user account                                       |
| `/v1/auth/login`         | POST   | `{ email, password }`                 | Authenticate user + issue tokens                           |
| `/v1/auth/refresh`       | POST   | `{ refreshToken }`                    | Refresh access token                                       |
| `/v1/auth/logout`        | POST   | —                                    | Invalidate session/token                                   |
| `/v1/auth/forgot-password`| POST  | `{ email }`                            | Request password reset link                                |
| `/v1/auth/reset-password`| POST   | `{ token, newPassword }`              | Reset password                                              |

— **User**
| Endpoint             | Method | Params / Body                      | Description                                             |
|----------------------|--------|-----------------------------------|---------------------------------------------------------|
| `/v1/users/me`       | GET    | —                                  | Get current user's profile                              |
| `/v1/users/me`       | PUT    | `{ displayName, avatarUrl, … }`     | Update profile                                          |
| `/v1/users/me`       | DELETE | —                                  | Delete user account                                     |

— **Articles & Discovery**
| Endpoint                   | Method | Params / Body                                               | Description                              |
|----------------------------|--------|--------------------------------------------------------------|------------------------------------------|
| `/v1/articles`             | GET    | `page`, `limit`, `sources`, `keywords`, `themes`, `sort`     | Paged list of articles                    |
| `/v1/articles/{id}`        | GET    | —                                                             | Article details                           |
| `/v1/articles/{id}/similar`| GET    | `limit`                                                        | Similar articles to given article         |
| `/v1/articles`             | POST   | `{ title, excerpt, url, imageUrl, publishedAt, themes, sourceId }`| Add article without journal         |
| `/v1/articles/{id}`        | PUT    | `{ title, excerpt, url, imageUrl, publishedAt, themes, sourceId }` | Update article                     |
| `/v1/articles/{id}`        | DELETE | —                                                             | Delete article                          |

— **Favorites**
| Endpoint                   | Method | Params / Body                         | Description                                |
|----------------------------|--------|--------------------------------------|--------------------------------------------|
| `/v1/me/favorites`         | GET    | `page`, `limit`                       | Get user's favorites list                  |
| `/v1/me/favorites`         | POST   | `{ articleId }`                       | Add to favorites                           |
| `/v1/me/favorites/{articleId}` | DELETE | —                                 | Remove favorite                            |

— **Journals (personal collections)**
| Endpoint                                   | Method | Params / Body                                                  | Description                            |
|--------------------------------------------|--------|---------------------------------------------------------------|----------------------------------------|
| `/v1/me/journals`                           | GET    | `page`, `limit`                                                | List user's journals                    |
| `/v1/me/journals`                           | POST   | `{ title, description, visibility? }`                          | Create journal                          |
| `/v1/me/journals/{journalId}`              | GET    | —                                                              | Get details of user's journal           |
| `/v1/me/journals/{journalId}`              | PUT    | `{ title?, description?, visibility? }`                        | Update journal                           |
| `/v1/me/journals/{journalId}`              | DELETE | —                                                              | Delete journal                            |
| `/v1/journals/{journalId}`                  | GET    | `page`, `limit`                                                | View public journal                      |
| `/v1/me/journals/{journalId}/share`         | POST   | `{ public: boolean }`                                          | Enable/disable public link               |
| `/v1/me/journals/{journalId}/articles`      | GET    | `page`, `limit`                                                | List articles in journal                 |
| `/v1/me/journals/{journalId}/articles`      | POST   | `{ articleId OR title, excerpt, url, imageUrl, publishedAt, themes, sourceId }` | Add article to journal     |
| `/v1/me/journals/{journalId}/articles/{articleId}` | DELETE | —                                                             | Remove article from journal           |

— **Themes, Tags & Preferences**
| Endpoint                         | Method | Params / Body               | Description                          |
|----------------------------------|--------|-----------------------------|--------------------------------------|
| `/v1/themes`                      | GET    | —                           | List all available themes             |
| `/v1/me/themes`                   | GET    | —                           | Get user's preferred themes           |
| `/v1/me/themes`                   | PUT    | `{ themes: string[] }`       | Update preferred themes              |
| `/v1/me/themes/blacklist`         | GET    | —                           | Get blacklisted themes                |
| `/v1/me/themes/blacklist`         | PUT    | `{ themes: string[] }`       | Update blacklist                      |

— **Sources**
| Endpoint                               | Method | Params / Body                    | Description                          |
|----------------------------------------|--------|----------------------------------|--------------------------------------|
| `/v1/sources`                           | GET    | `page`, `limit`, `status?`       | List sources                          |
| `/v1/me/sources`                        | GET    | —                                | Get user's preferred sources          |
| `/v1/me/sources`                        | PUT    | `{ sources: string[] }`           | Update preferred sources              |
| `/v1/me/sources/blacklist`              | GET    | —                                | Get blacklisted sources               |
| `/v1/me/sources/blacklist`              | PUT    | `{ sources: string[] }`           | Update blacklist                       |

— **Notifications**
| Endpoint                        | Method | Params / Body                       | Description                               |
|----------------------------------|--------|-------------------------------------|-------------------------------------------|
| `/v1/me/notifications`            | GET    | —                                   | Get notification preferences               |
| `/v1/me/notifications`            | PUT    | `{ channels, topics }`              | Update notification preferences            |

— **Search**
| Endpoint       | Method | Params / Body                              | Description            |
|----------------|--------|---------------------------------------------|--------------------------|
| `/v1/search`   | GET    | `q`, `filters`, `page`, `limit`             | Global search across articles |

— **System**
| Endpoint       | Method | Params / Body | Description                        |
|----------------|--------|--------------|------------------------------------|
| `/v1/health`   | GET    | —            | Service health check               |
| `/v1/version`  | GET    | —            | API version                        |

#### 3.3.2 Simplified Data Model
- **User**
  - Primary key: `id`
  - Foreign keys: `default_theme_pref_id` → `UserThemePreference.id`, `default_source_pref_id` → `UserSourcePreference.id`
  - Main fields: `email` (unique), `password_hash`, `created_at`, `updated_at`
- **Article**
  - Primary key: `id`
  - Foreign key: `source_id` → `Source.id`
  - Main fields: `title`, `excerpt`, `url`, `image_url`, `published_at`, `themes`, `external_id` (unique per source)
- **Source**
  - Primary key: `id`
  - Main fields: `name`, `feed_url` / `api_url`, `logo`, `categories`, `status`
- **Journal**
  - Primary key: `id`
  - Foreign key: `owner_id` → `User.id`
  - Main fields: `title`, `description`, `created_at`, `updated_at`, `visibility` (private / public)
- **JournalArticle** (n-n relation between `Journal` and `Article`)
  - Primary key: `id`
  - Foreign keys: `journal_id` → `Journal.id`, `article_id` → `Article.id` (nullable if no article), `author_id` → `User.id`
  - Main fields: `media`, `status` (draft / published), `created_at`, `updated_at`
- **Favorite**
  - Primary key: `id`
  - Foreign keys: `user_id` → `User.id`, `article_id` → `Article.id`
  - Constraint: unique pair (`user_id`, `article_id`)
- **UserThemePreference**
  - Primary key: `id`
  - Foreign keys: `user_id` → `User.id`, `theme_id` → `Theme.id`
  - Constraint: unique pair (`user_id`, `theme_id`)
- **UserSourcePreference**
  - Primary key: `id`
  - Foreign keys: `user_id` → `User.id`, `source_id` → `Source.id`
  - Constraint: unique pair (`user_id`, `source_id`)
- **Theme**
  - Primary key: `id`
  - Main fields: `name` (unique), `slug`, `description`
- **NotificationPreference**
  - Primary key: `id`
  - Foreign key: `user_id` → `User.id`
  - Main fields: `channels` (email, in-app), `frequency` (real-time, digest), `created_at`, `updated_at`
- **NotificationPreferenceTheme**
  - Primary key: `id`
  - Foreign keys: `notification_pref_id` → `NotificationPreference.id`, `theme_id` → `Theme.id`
  - Constraint: unique pair (`notification_pref_id`, `theme_id`)
- **NotificationPreferenceSource**
  - Primary key: `id`
  - Foreign keys: `notification_pref_id` → `NotificationPreference.id`, `source_id` → `Source.id`
  - Constraint: unique pair (`notification_pref_id`, `source_id`)
- Fields that accept a finite set of values (statuses, visibility, channels) will be implemented using enumerations (ENUMs).

#### 3.3.3 Feed Collection / Aggregation
- A module for **polling / scheduling** (e.g., cron job or periodic task)
- For each defined source, query its RSS feed or API, parse returned items, check if they are new (by external ID or URL), store new articles in the database
- Handle errors (inaccessible feed, timeout) and log failures

---

## 4. Non-Functional Constraints

### 4.1 Performance & scalability
- Pagination / lazy loading to avoid loading all articles at once
- Caching (in memory or persistent) to avoid frequent external calls
- Optimize frontend: code minification, bundling, asynchronous loading
- Compress images / media where possible
- Limit unnecessary external API calls

### 4.2 Security
- Input validation / sanitization
- Protection from SQL / NoSQL injection
- Secure password hashing (bcrypt, argon2)
- Use JWT tokens or secure sessions
- Access control for sensitive API endpoints
- Proper CORS setup between frontend and backend
- Secure handling of API keys / secrets (not exposed to client)

### 4.3 Reliability / robustness
- Error handling for timeouts, invalid feeds, API unavailability; include fallback/retry
- Logs of key events (errors, requests, failures)
- Automated tests (unit, integration, API)
- Monitoring / health checks: logs, alerts, service health endpoints

### 4.4 Portability / deployment
- Containerization: each component (frontend, backend, database) runs in Docker
- Local orchestration via `docker-compose`
- CI/CD pipeline for builds, tests, deployment
- Deployment to server or cloud environment
- Installation / configuration documentation

### 4.5 User Experience / UI / Accessibility
- Responsive, smooth interface
- Progressive loading + light animations
- Good readability: fonts, contrast
- Basic accessibility: dark theme option, language selection
- Intuitive navigation: menus, filters, search

### 4.6 Compatibility & browser support
- Support for modern browsers: Chrome, Firefox, Edge, Safari
- Support for mobile via browser: iOS, Android
- Compatibility testing across different screen sizes

---

## 5. Recommended Technologies

### 5.1 Frontend
- **React + TypeScript**: Mature ecosystem, reusable components, well-suited for SPA projects.

### 5.2 Backend
- **FastAPI (Python)**: High performance, validation via Pydantic, automatically generated API docs (OpenAPI/Swagger).

### 5.3 Infrastructure / DevOps
- **Docker + docker-compose**: Containerization of all services.
- **GitHub Actions**: CI/CD pipeline for tests, builds, deployment.
- **Swagger-UI / Redoc**: Interactive API documentation.

### 5.4 Tests & Quality
- **pytest** (Python): Unit and integration tests.
- **HTTPX**: API testing.
- **Cypress**: End-to-end (E2E) testing.
- **ESLint + Prettier**: Linting and formatting for code quality.

---

## 6. Architecture & Urbanization

### 6.1 High-level architecture diagram
> Frontend (client application)
> ↕ HTTP/HTTPS
> Backend (API)
> ↕ Database + Cache
> ↕ Feed collection / aggregation module (cron / scheduler)
> ↕ External sources (RSS feeds / APIs)

### 6.2 Simplified data flow
1. The polling / scheduler module periodically queries external feeds (RSS/APIs) for each source.
2. It parses the results, removes duplicates, and stores new articles in the database (PostgreSQL).
3. The FastAPI backend exposes REST endpoints for:
   - retrieving articles (filters, pagination)
   - managing favorites
   - managing users / preferences
4. The React frontend consumes the API, displays articles, offers filters, handles UI.
5. When a user marks an article as favorite, the frontend issues a POST to the API, which stores the relation in the database.

---

## 7. Schedule & Proposed Milestones

| Phase                         | Start         | Estimated Duration | Objectives / Deliverables                                     |
|------------------------------|---------------|--------------------|----------------------------------------------------------------|
| Scoping & design             | Day 0         | 1-2 weeks          | Specification document validated, wireframes, tech choices     |
| Initialization / infrastructure | +1-2 weeks    | 1 week             | Project scaffolding, Docker, Git repository, basic CI setup    |
| Basic backend                | +3 weeks      | 2-3 weeks          | Aggregation module, articles API / base endpoints              |
| Frontend feed                | +3 weeks      | 2-3 weeks          | Home UI, article listing, UI components                        |
| Search / filters / suggestions| +5-6 weeks    | 1-2 weeks          | Basic search engine, filters, recommendation logic              |
| Favorites / personalization  | +7-8 weeks    | 1-2 weeks          | Favorites module, user preferences, optional user management   |
| Testing / optimization       | +9-10 weeks   | 1 week             | Test coverage, bug fixes, performance tuning                   |
| Documentation / benchmark / report | +10-11 weeks | 2 weeks        | Writing documentation, benchmark vs Flipboard / competitors    |
| Buffer / extra features      | after         | remaining time     | Additional features, improved UX/UI, extended test coverage     |

Extra time may be used for adding additional features, enhancing UX/UI, or expanding test coverage.

---

## 8. Validation / Acceptance Criteria
- All MVP functionalities (feed, filters, favorites, search) work correctly.
- User interface is responsive, smooth, without major bugs.
- Backend is stable; APIs respond correctly; feed collection module operates in production.
- Automated tests pass without errors.
- The project can be deployed and run via `docker-compose`.
- Documentation (installation guide, API docs, user manual) is clear and complete.
- Security requirements are met (e.g., passwords hashed, tokens secure, no sensitive data exposed).

---

## 9. Appendices & References
- List of potential sources (public RSS feeds / APIs)
- Glossary of terms (feed, API, pagination, etc.)
- Technical benchmark (tools, libraries used)
- Database schema (ERD)
- Detailed architecture diagrams
- API endpoint documentation (OpenAPI/Swagger)

