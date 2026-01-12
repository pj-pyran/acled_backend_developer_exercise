# Backend Developer At-Home Exercise
*72 hours*

Use the details below to guide you in building an API for a conflict monitoring platform. The API must support user authentication, allow you to view information about conflicts in different countries, and allow the user to post feedback.

## Requirements
- [x] **Data:** Use the dataset in the sample_data.csv file. This dataset contains the following variables:
    - **country (string)**: country name
    - **admin1 (string)**: admin1 name
    - **population (numeric)**: population count; null values are blank
    - **events (numeric)**: event count
    - **score (numeric)**: conflict risk score
- [x] **Deployment:** Local or cloud deployment (your preference)
- [x] **Language:** Any mainstream backend language/framework, with preference for Python
- [x] **Authentication:**
    - [x] JWT-based authentication
    - [x] Register and login endpoints
    - [x] Password hash required
- [x] **Endpoints:**
    - [x] **GET** /conflictdata
        - List conflict data for each country with pagination (default to returning 20 countries per page). Note that this will result in multiple entries per country since each country can have multiple admin1 entries.
    - [x] **GET** /conflictdata/:country
        - Based on country name, list country-admin1 details, including the admin1 names, conflict risk scores, and population per admin1. Allow for multiple country names to be accepted.
    - [x] **GET** /conflictdata/:country/riskscore
        - Return the average risk score for the country using a background job to average the risk scores across admin1’s for the country
    - [x] **POST** /conflictdata/:admin1/userfeedback
        - Add user feedback about the admin1 (authentication required)
        - [x] User feedback text must be at least 10 characters but no more than 500 characters
    - [x] **DELETE** /conflictdata
        - [x] Admin only
        - Allow admin user to delete entries from the table based on admin1 and country combination
- [x] **Database and query requirements:**
    - [x] Efficient queries (avoid N+1)
    - [x] Proper indexing
    - [x] Transaction use where appropriate
    - [x] Prevent SQL injection
## Submission materials
<!-- TODO -->
- [ ] Git repo link
- [x] Setup instructions (README file)
- [x] API documentation (OpenAPI or markdown) including:
    - [x] Endpoint descriptions
    - [x] Request and response bodies
    - [x] Auth header (JWT)
    - [x] Error responses (e.g., 400, 401, 404)
- [x] Example curl or Postman request
- [x] Notes explaining decisions and/or tradeoffs