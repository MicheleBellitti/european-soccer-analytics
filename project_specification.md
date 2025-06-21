## European Soccer Analytics Platform: A Simplified, Modular Design

This document outlines a streamlined and highly modular design for a European Soccer analytics platform. The focus is on creating a robust, testable, and maintainable system that fetches football data, stores it locally in a PostgreSQL database, and presents advanced insights through an interactive Streamlit dashboard. This design intentionally defers the conversational AI component to a later stage, ensuring the foundational data platform is solid and well-engineered first.

### 1\. Project Vision & Goals

The project's vision is to create a powerful yet easy-to-use tool for exploring European soccer data. It will empower users to discover trends, analyze performance, and compare entities (players, teams) across various dimensions.

**Core Goals:**

  * **Modularity:** Every component of the system will be designed as a distinct, interchangeable module, facilitating independent development, testing, and updates.
  * **Data Integrity:** Ensure reliable data fetching and storage in a well-structured local PostgreSQL database.
  * **Advanced Interactive Analytics:** The Streamlit dashboard will be the centerpiece, offering rich, interactive visualizations and data filtering capabilities.
  * **Testability:** Emphasize a test-driven development approach with comprehensive unit and integration tests.
  * **Future-Proofing:** The data schema and architecture will be designed with the future integration of a conversational AI in mind.

### 2\. System Architecture

The simplified architecture is composed of four primary, loosely coupled components: a Data Fetching Service, a local PostgreSQL Database for storage, a Data Processing and Analytics Engine, and a Streamlit-based Presentation Layer.

**Architectural Diagram:**

```
[Football Data APIs] <--> [Data Fetching Service] <--> [PostgreSQL Database (Local)] <--> [Analytics Engine] <--> [Streamlit Dashboard]
```

**2.1. Data Fetching Service:**

This service is responsible for all external API communications. Its sole purpose is to retrieve data and pass it on for storage.

  * **Data Sources:**
      * **Primary (Free):** `football-data.org` will be the initial target for its comprehensive free tier covering major European leagues.
      * **Contingency (Low-Cost):** The system will be designed with an abstraction layer to easily integrate other APIs like **Sportmonks** or **TheOddsAPI** if more detailed data is required in the future.
  * **Implementation:** A set of Python scripts, organized by data entity (e.g., `leagues_fetcher.py`, `teams_fetcher.py`, `players_fetcher.py`), will handle the API requests. These scripts will be designed to be run on a schedule (e.g., using a simple cron job or a lightweight scheduler library).

**2.2. Storage Layer: Local PostgreSQL Database**

A local PostgreSQL database will serve as the single source of truth for all structured data. This simplifies setup and reduces costs while providing a powerful and reliable storage solution.

  * **Database Schema:** A well-defined relational schema is crucial for data integrity and efficient querying. The initial schema will include tables such as:
      * `Leagues`: Stores information about each competition (e.g., name, country).
      * `Teams`: Contains details for each club, with a foreign key to `Leagues`.
      * `Players`: Holds player information, including nationality, position, and a foreign key to their current `Teams`.
      * `Matches`: Records match details, including home and away teams, scores, and date.
      * `PlayerStats`: A table to store individual player statistics for each match, with foreign keys to `Players` and `Matches`. This design will facilitate future RAG by keeping player performance data structured and easily retrievable.
  * **Database Interaction:** **SQLAlchemy** will be used as the Object-Relational Mapper (ORM). This provides a Python-centric way to interact with the database, abstracting away raw SQL queries and making the code more readable and maintainable.

**2.3. Data Processing & Analytics Engine:**

This component is responsible for transforming the raw data from the database into meaningful insights and preparing it for visualization.

  * **Implementation:** A collection of Python functions within a dedicated `analytics` module. These functions will take dataframes (queried from the database via SQLAlchemy) as input and perform calculations for:
      * **Advanced Metrics:** Calculation of metrics like points per game, goal difference, player goal contributions (goals + assists), etc. More advanced metrics like xG (Expected Goals) can be added later by integrating open-source models.
      * **Data Aggregation:** Functions to group data by team, nationality, or position to power the dashboard filters.
      * **Visualization Data Preparation:** Functions that prepare data specifically for chart and heatmap generation (e.g., creating pivot tables for heatmaps).

**2.4. Presentation Layer: Interactive Streamlit Dashboard**

The user interface will be a multi-page Streamlit application, providing an intuitive way to explore the data.

  * **Key Features:**
      * **Interactive Filters:** Users will be able to filter the entire dashboard view by League, Nationality, Team, Player, and Position using widgets like `st.selectbox` and `st.multiselect`.
      * **Data Views:**
          * **League Overview:** Display league tables and aggregated team statistics.
          * **Team Analysis:** Show team-specific information, squad lists, and performance charts.
          * **Player Search & Comparison:** A dedicated page to search for players and view their detailed statistics, including performance heatmaps.
      * **Visualizations:**
          * **Charts:** Interactive bar charts, line charts, and scatter plots using **Plotly Express** for a rich user experience.
          * **Heatmaps:** To visualize player performance across different metrics.
          * **Tables:** Interactive and sortable tables using `st.dataframe`.
  * **Performance:** Streamlit's caching (`st.cache_data` and `st.cache_resource`) will be used extensively to prevent re-running expensive database queries and computations, ensuring a smooth and responsive dashboard.

### 3\. Project Structure

A modular, testable, and scalable project structure is paramount.

```
european-soccer-analytics/
├── .github/
│   └── workflows/
│       └── testing.yml
├── .env.example
├── config/
│   └── db_config.py
├── data_models/
│   ├── __init__.py
│   └── models.py
├── etl/
│   ├── __init__.py
│   ├── fetch.py
│   └── load.py
├── analytics/
│   ├── __init__.py
│   └── metrics.py
├── dashboard/
│   ├── __init__.py
│   ├── pages/
│   │   ├── 01_League_Overview.py
│   │   ├── 02_Team_Analysis.py
│   │   └── 03_Player_Search.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_etl.py
│   ├── test_analytics.py
│   └── test_dashboard.py
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── streamlit_app.py
```

**Directory Breakdown:**

  * **`.github/workflows/`**: For setting up CI/pipelines to run tests automatically.
  * **`config/`**: Contains database connection settings.
  * **`data_models/`**: Defines the SQLAlchemy ORM models that map to the PostgreSQL database tables.
  * **`etl/`**: Holds the Extract, Transform, Load logic. `fetch.py` gets data from the API, and `load.py` uses the SQLAlchemy models to save it to the database.
  * **`analytics/`**: Contains all functions for data processing and calculation of advanced metrics.
  * **`dashboard/`**: The main Streamlit application.
      * **`pages/`**: Each file represents a separate page in the multi-page Streamlit app.
      * **`utils.py`**: Utility functions for the dashboard, such as data querying functions that use caching.
  * **`tests/`**: A critical directory containing unit and integration tests for each module using the **pytest** framework.
  * **`docker-compose.yml` & `Dockerfile`**: For containerizing the application and the PostgreSQL database, ensuring a consistent development and deployment environment.
  * **`streamlit_app.py`**: The main entry point for the Streamlit application.

### 4\. Implementation Plan

1.  **Environment Setup:** Initialize the project structure, Git repository, and set up Docker for the PostgreSQL instance.
2.  **Database Modeling:** Define the database schema in `data_models/models.py` using SQLAlchemy.
3.  **ETL Pipeline:** Implement the data fetching and loading scripts in the `etl/` directory. Write tests to verify data integrity.
4.  **Analytics Core:** Develop the core analytical functions in the `analytics/` module. These should be pure functions that are easy to test.
5.  **Dashboard Development:** Build the Streamlit dashboard, starting with the filtering logic and then creating each page one by one.
6.  **Testing:** Continuously write and run tests for all components to ensure reliability.
7.  **Containerization:** Finalize the Docker setup for easy deployment.

This simplified, modular design provides a clear and robust foundation for the European Soccer Analytics Platform, ensuring that the initial goals are met while paving the way for future enhancements like the conversational AI.