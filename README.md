# ACLED Backend Developer take-home exercise
API framework for a conflict monitoring platform. Endpoints allow access to statistics at level of country region/state/province. Statstics include region population, number of conflict events, and a conflict risk score at regional level or averaged over the whole country.

Authenticated users may also provide feedback on the regional-level data.

Sourced from ACLED - see [website](https://acleddata.com/conflict-data) for further data.

## Setup Instructions

### Prerequisites
- Python 3.10+ installed
- Git installed

### Installation

1. Clone the repository (alternatively visit [github.com/pj-pyran/acled_backend_developer_exercise](https://github.com/pj-pyran/acled_backend_developer_exercise)):
    ```bash
    git clone https://github.com/pj-pyran/acled_backend_developer_exercise.git
    cd acled_backend_developer_exercise
    ```
2. Create and activate virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ``` 
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Initialise the DB (SQLite) and load sample data:
    ```bash
    python -m app.init_db
    python -m scripts.load_test_data
    ```
    Test data includes the provided `sample_data.csv` and 2 users including one admin user.
5. Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```
6. Access the API:
    * API: http://127.0.0.1:8000
    * OpenAPI interactive docs: http://127.0.0.1:8000/docs. You may test all endpoints here.

## curl samples
1. Register
    ```curl
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email": "user2@test.com", "password": "password123"}'
    ```
2. Login
    ```curl
    curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "user2@test.com", "password": "password123"}'
    ```
3. Get conflict data (paginated)
    ```curl
    curl "http://127.0.0.1:8000/api/v1/conflictdata?offset=0&page_size=20"
    ```
4. Get conflict data by country
    ```curl
    curl "http://127.0.0.1:8000/api/v1/conflictdata/Nigeria"
    ```
5. Get risk score average
    ```curl
    curl "http://127.0.0.1:8000/api/v1/conflictdata/Nigeria/riskscore"
    ```
    If a `202` response is received, wait a few seconds and send the request again for a `200`.

6. Post feedback (authenticated)
    ```curl
    # Login and capture token
    TOKEN=$(curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "user2@test.com", "password": "password123"}' \
    | jq -r '.access_token')

    # Call endpoint
    curl -X POST "http://127.0.0.1:8000/api/v1/conflictdata/Lagos/userfeedback?country=Nigeria" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"feedback_text": "This is my feedback about the region."}'
    ```
7. Delete entry (admin only)
    ```curl
    # Login and capture token
    TOKEN=$(curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "user2@test.com", "password": "password123"}' \
    | jq -r '.access_token')

    # Call endpoint
    curl -X DELETE "http://127.0.0.1:8000/api/v1/conflictdata?admin1=Lagos&country=Nigeria" \
    -H "Authorization: Bearer $TOKEN"
    ```

# Database and query requirements
## Efficient queries (avoid N+1)
Using single queries with `.all()` or `.first()` to fetch data, not looping and making individual queries per row. For example in `POST /feedback` endpoint we query once for matches, not iterating through `admin1`s individually.

## Proper indexing
Implemented a a composite unique index on `(country, admin1)` in the model, covering most common filter patterns. Verified it works with `EXPLAIN QUERY PLAN`.

## Transaction use where appropriate
SQLAlchemy's session handles transactions automatically - `db.commit()` calls ensure atomic writes. The `DELETE /conflictdata` wraps query, delete, and commit in one transaction. For single operations this is sufficient.

## Prevent SQL injection
We use SQLAlchemy ORM throughout, which uses parameterised queries. We don't concatenate user input into raw SQL strings - all filters use `.filter()` with model attributes like `ConflictData.country == country.lower()`, which are safely parameterised by SQLAlchemy


# Stack
## FastAPI
1. Forced schema definitions - better control, fewer bugs
2. Auto-generated API docs using Swagger
3. Plays w

Flask would give quicker/easier start-up due to not needing schema definitions. However a more defined structure will pay off in the longer run and make testing easier

## SQLite
Postgres provides better index usage and query efficiency; SQLite is super fast to start and is sufficient for development, but likely would be preferable to drop in Postgres down the line for index performance.

Checked successful use of composite index via:
```sql
EXPLAIN QUERY PLAN
SELECT country, admin1
FROM conflict_data
ORDER BY country, admin1;
```

## SQLAlchemy
ORM for database interactions.
1. Allows pythonic object-oriented interaction with database objects.
2. Eliminates risk of SQL injection
3. Easier adaptation if we switch databases later (DB-agnostic)

## Pydantic
Packaged with FastAPI - request and response validation

## python-jose
JSON Web Token (JWT) encoding/decoding. Essential for best-practice authentication. PyJWT would also be an option

## passlib[bcrypt]
Password hashing

## Uvicorn
Quick-start ASGI server that runs FastAPI. Handles HTTP requests asynchronously for better concurrency.


# API design
## Versioning
Included `v1` in the request paths of stable release to gracefully accommodate potential future versioning

## HTTP response and error codes
| Endpoint                                             | Code         | Meaning |
|------------------------------------------------------|--------------|---------|
| `GET /conflictdata`                                  | 404          | Passed `offset` value is greater than query row count |
| `GET /conflictdata/{country}`                        | 404          | `country` not found in `conflict_data` table |
| `GET /conflictdata/{country}/riskscore`              | 404          | `country` not found in `conflict_data` table |
| `GET /conflictdata/{country}/riskscore` (cached)     | 200          | Pre-cached value returned |
| `GET /conflictdata/{country}/riskscore` (processing) | 202          | Success, risk score average calculation job initiated. User must call again to get the score average |
| `POST /conflictdata/{admin1}/userfeedback`           | 404          | `(admin1, country)` not found in `conflict_data` table |
| `POST /conflictdata/{admin1}/userfeedback`           | 422          | `(admin1, country)` not found in `conflict_data` table |
| `DELETE /conflictdata`                               | 404          | `(admin1, country)` not found in `conflict_data` table |
| `POST /auth/register`                                | 400          | user already registered for `email` |
| `POST /auth/login`                                   | 401          | invalid credentials (email or password) provided |

These functions are used by endpoints for auth and have HTTP exception logic:
| Function            | Code | Message | Meaning |
|---------------------|------|---------|---------|
|`get_current_user()` | 401  | `missing or invalid authorisation header` | no, or badly formed, header | 
|`get_current_user()` | 401  | `invalid token` | JWT found but invalid |
|`get_current_user()` | 401  | `user not found` | `user_id` not found in `users` table |
|`require_admin()`    | 403  | `admin privileges required` | attempted an admin operation; current user has `is_admin=0` |

Other codes will be passed as-per FastAPI defaults.

## Empty results set
- With some more time/different data structure (use ISO country codes) there could be an implementation of a 'valid country' check to tailor response between an invalid country and one that is valid but not in the dataset
- Further it would be good to treat the scenario where multiple countries' data is requested and some match (rows returned) but some don't (no rows returned). Then the user could be warned of this


## `GET /conflictdata`
### Offset/limit structure
- Fairly simple this way. For a dataset of small size this is fine
- Order by (country, admin1)
- Set a default limit of 20 with max limit of 100 for performance

## `GET /conflictdata/:country`
Given the structure given (`/conflictdata/:country`) it was assumed that country name(s) must be passed as a path parameter. Though typing is possible for path params in FastAPI, it may have been easier to pass the input in the request body. As noted I stuck to what I believe is the structure given by the task.

## `GET /conflictdata/:country/riskscore`
### request and URL structure
As query string parameters have not been specified for any endpoints (but clearly needed in the case of e.g. pagination for `GET /conflictdata`) I have `country` and `admin1` passed as query string params in this endpoint.

### Recalculation
After a data row is deleted, the cached average risk calculation will be invalidated. Once the deletion is committed to db, the average calcualtion job is kicked off for that country.

## `POST /conflictdata/:admin1/userfeedback`
### 422 response (multiple data matches)
I have chosen to throw a `422 Unprocessable content` if the passed `admin1` matches more than one `admin1` in the `conflict_data` table.

The preference could equally to be to force the `country` query string parameter to be passed. That should also be sufficient due to the unique contstraint on the columns. I chose my way so that the client can keep request even more lightweight in most cases, by passing only the `admin1` path parameter.

I then return all matched rows to the client, allowing them to create UI for the user to choose between the matched regions.

## `DELETE /conflictdata`
This could be designed in various ways. I chose to stick to basically the safest basic design, i.e. that which will make it hardest to delete large chunks of data. The endpoint wil only accept a single row deletion at once, and must take both `country` and `admin1` values

# Project structure
## Async job (risk score average calculations)
In a more complex setup with more background jobs needed, these should be separated into a `services` folder for clarity/separation of concerns, with something like Celery for task management. With only 1 async background job, I've just kept it under `/routes/conflict_data.py`. This is suficient for such a simple light workload.

The score is computed asynchronously on first request and cached for subsequent reads. If no cached value exists, the endpoint returns a processing status.

For a light implementation like this the in-memory cache is seen as sufficient. One drawback is that it is lost on app restart. With further dev time a SQL cache table could be implemented as a more robust solution.


# Data
The population estimates in general are definitely very low; query
```sql
SELECT country, sum(population) as popsum
FROM conflict_data
GROUP BY country
ORDER BY popsum DESC
```
yields 126M for China, 62.4M for India, 59.1M for USA and 25.7M for UK. Could be `admin1`s missing from the dataset?

# Known issues
- [ ] Lowercase (case-insensitive) string comparisons currently cause problems with certain non-ASCII characters (tested with `Ö`). Option to either make comparisons case-sensitive or use `.ilike` operator; preference for the latter approach for mos use cases