# European Soccer Analytics Platform

A comprehensive European Soccer analytics platform that fetches football data, stores it locally in a PostgreSQL database, and presents advanced insights through an interactive Streamlit dashboard.

## 🏆 Features

- **Data Fetching**: Automated data fetching from football-data.org API
- **Local Storage**: PostgreSQL database with well-structured schema
- **Interactive Dashboard**: Multi-page Streamlit application with rich visualizations
- **Advanced Analytics**: Performance metrics, team comparisons, and player statistics
- **Modular Design**: Clean, testable, and maintainable architecture
- **CLI Tools**: Command-line interface for data management and analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13+ (or use Docker)
- Football Data API key from [football-data.org](https://www.football-data.org/client/register)

### Installation

#### Option 1: Automated Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd european-soccer-analytics
   ```

2. **Get your Football Data API key:**
   - Register at [football-data.org](https://www.football-data.org/client/register)
   - Get your free API key

3. **Run the automated setup:**
   ```bash
   ./scripts/setup_and_test.sh
   ```
   
   This script will:
   - Create `.env` file from template
   - Build and start Docker containers
   - Initialize the database
   - Test API connectivity
   - Start the dashboard

4. **Edit your API key:**
   ```bash
   # Edit .env file and replace demo_key with your real API key
   FOOTBALL_DATA_API_KEY=your_actual_api_key_here
   ```

#### Option 2: Manual Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd european-soccer-analytics
   cp .env.example .env
   # Edit .env with your API key
   ```

2. **Using Docker (Recommended):**
   ```bash
   docker-compose up --build
   ```

3. **Or using Poetry/Pip:**
   ```bash
   poetry install && poetry shell
   # Or: pip install -r requirements.txt
   
   # Start database separately
   docker-compose up postgres -d
   
   # Initialize database and run app
   python scripts/run_etl.py --init-db
   streamlit run streamlit_app.py
   ```

## 🐳 Docker Setup

Run the entire application with Docker:

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your API key

# Start all services
docker-compose up -d

# The dashboard will be available at http://localhost:8501
```

## 📊 Usage

### Dashboard Features

- **League Overview**: League tables, team statistics, and performance trends
- **Team Analysis**: Detailed team information, squad lists, and match history
- **Player Search**: Player statistics, performance heatmaps, and comparisons

### CLI Commands

```bash
# Initialize database
poetry run soccer-analytics init-db

# Fetch data for specific competitions
poetry run soccer-analytics fetch-data --competitions PREMIER_LEAGUE BUNDESLIGA

# Generate analytics reports
poetry run soccer-analytics analytics --league "Premier League" --team "Arsenal"

# Start dashboard
poetry run soccer-analytics dashboard
```

### ETL Operations

```bash
# Fetch all data for major competitions
python scripts/run_etl.py

# Fetch data for specific competitions
python scripts/run_etl.py --competitions PREMIER_LEAGUE LA_LIGA

# Skip certain data types
python scripts/run_etl.py --skip-matches --skip-standings
```

## 🏗️ Architecture

```
[Football Data APIs] <--> [Data Fetching Service] <--> [PostgreSQL Database] <--> [Analytics Engine] <--> [Streamlit Dashboard]
```

### Components

- **Data Fetching Service**: Handles API communication with football-data.org
- **PostgreSQL Database**: Local storage with comprehensive schema
- **Analytics Engine**: Data processing and metric calculations
- **Streamlit Dashboard**: Interactive web interface
- **CLI Interface**: Command-line tools for data management

## 📁 Project Structure

```
european-soccer-analytics/
├── src/soccer_analytics/
│   ├── analytics/           # Data processing and metrics
│   ├── cli/                # Command-line interface
│   ├── config/             # Configuration and settings
│   ├── dashboard/          # Streamlit application
│   ├── data_models/        # SQLAlchemy ORM models
│   └── etl/               # Extract, Transform, Load
├── scripts/               # Utility scripts
├── tests/                # Test suite
├── data/                 # Data files
├── logs/                 # Log files
├── docker-compose.yml    # Docker configuration
├── Dockerfile           # Application container
└── streamlit_app.py     # Main application entry point
```

## 🗄️ Database Schema

The platform uses a comprehensive PostgreSQL schema with the following main tables:

- **leagues**: Competition information
- **teams**: Team details and metadata
- **players**: Player information and current team
- **matches**: Match results and details
- **player_stats**: Individual player statistics per match
- **team_stats**: Aggregated team statistics by season

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/soccer_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=soccer_analytics

# API
FOOTBALL_DATA_API_KEY=your_api_key_here

# Application
DEBUG=false
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
```

### Supported Competitions

- Premier League (England)
- La Liga (Spain)
- Bundesliga (Germany)
- Serie A (Italy)
- Ligue 1 (France)
- Eredivisie (Netherlands)
- Primeira Liga (Portugal)
- UEFA Champions League
- UEFA Europa League

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=soccer_analytics

# Run specific test categories
poetry run pytest tests/unit/
poetry run pytest tests/integration/
```

## 📈 Development

### Setting up for Development

1. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run code formatting:
   ```bash
   black src/ tests/
   isort src/ tests/
   ```

4. Run type checking:
   ```bash
   mypy src/
   ```

### Adding New Features

1. Follow the modular architecture
2. Add comprehensive tests
3. Update documentation
4. Ensure code quality with linting tools

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Errors:**
- Run `./scripts/setup_and_test.sh` for automated diagnosis
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs postgres`
- The wait script handles initial database readiness issues

**API Connection Issues:**
- Test API connectivity: `docker-compose exec app python src/soccer_analytics/etl/test_api.py`
- Verify your API key in `.env` file
- Check rate limits (free tier: 10 requests/minute)
- Ensure internet connectivity

**Docker Issues:**
- Clean rebuild: `docker-compose down --volumes && docker-compose up --build`
- Check Docker daemon is running
- Ensure ports 5432 and 8501 are available

**Import Errors:**
- Rebuild containers: `docker-compose up --build`
- Check container logs: `docker-compose logs app`
- Verify all files are copied correctly

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions and support:
- Create an issue on GitHub
- Check the documentation
- Review the project specification

## 🔮 Future Enhancements

- Conversational AI integration
- Real-time match data
- Advanced statistical models
- Mobile-responsive dashboard
- Multi-language support
- Data export capabilities 