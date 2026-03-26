🏠 Airbnb Market Expert
I built this to help Airbnb hosts move away from "gut feeling" pricing and start using actual market data. It’s a full-stack pipeline that handles everything from raw web scraping to deploying a live ML model.

🎯 Key Features
Custom Scraper: Uses Playwright to bypass basic bot detection and pull real-time listing data.

Structured Storage: All raw data is cleaned and piped into a MySQL database for persistence.

Price Intelligence: An XGBoost model trained on local market features (room type, location, amenities) to predict the "sweet spot" price.

Interactive UI: A Streamlit dashboard so users can visualize trends without looking at a terminal.

Production-Ready API: A FastAPI backend that serves model predictions via REST endpoints.

🏗️ How it works
The data flows from the web into a dashboard through these stages:

Scraping: Playwright mimics a browser to grab listings.

Storage: Python scripts handle the SQL insertions.

Training: I use Pandas for feature engineering and XGBoost for the regression task.

Serving: FastAPI loads the saved .json model and serves predictions at /predict.

📁 Repository Map
Plaintext
airbnb-market-expert/
├── scraper/             # Playwright scripts
├── database/            # SQL schemas & DB connection logic
├── ml/                  # Training scripts and exported model files
├── api/                 # FastAPI backend
├── dashboard/           # Streamlit frontend code
└── requirements.txt     # All the libraries you'll need
🚀 Getting Started
1. Setup
Bash
git clone https://github.com/salmansop123/airbnb-market-expert.git
cd airbnb-market-expert
pip install -r requirements.txt
playwright install chromium
2. Environment
Create a .env file in the root:

Ini, TOML
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=airbnb_expert
3. Run the Pipeline
Scrape: python scraper/airbnb_scraper.py

Train: python ml/price_model.py

API: uvicorn api.main:app --reload

UI: streamlit run dashboard/app.py

🛠️ Tech I Used
Backend: Python, FastAPI, Uvicorn

Frontend: Streamlit, Plotly (for the charts)

Database: MySQL

Machine Learning: XGBoost, Scikit-learn, Pandas

📈 Roadmap / Future Improvements
[ ] Add support for multi-city scraping.

[ ] Implement a cron job to auto-update the database weekly.

[ ] Containerize the whole thing using Docker for easier deployment.

Author: Salman🏠 Airbnb Market Expert
I built this to help Airbnb hosts move away from "gut feeling" pricing and start using actual market data. It’s a full-stack pipeline that handles everything from raw web scraping to deploying a live ML model.

🎯 Key Features
Custom Scraper: Uses Playwright to bypass basic bot detection and pull real-time listing data.

Structured Storage: All raw data is cleaned and piped into a MySQL database for persistence.

Price Intelligence: An XGBoost model trained on local market features (room type, location, amenities) to predict the "sweet spot" price.

Interactive UI: A Streamlit dashboard so users can visualize trends without looking at a terminal.

Production-Ready API: A FastAPI backend that serves model predictions via REST endpoints.

🏗️ How it works
The data flows from the web into a dashboard through these stages:

Scraping: Playwright mimics a browser to grab listings.

Storage: Python scripts handle the SQL insertions.

Training: I use Pandas for feature engineering and XGBoost for the regression task.

Serving: FastAPI loads the saved .json model and serves predictions at /predict.

📁 Repository Map
Plaintext
airbnb-market-expert/
├── scraper/             # Playwright scripts
├── database/            # SQL schemas & DB connection logic
├── ml/                  # Training scripts and exported model files
├── api/                 # FastAPI backend
├── dashboard/           # Streamlit frontend code
└── requirements.txt     # All the libraries you'll need
🚀 Getting Started
1. Setup
Bash
git clone https://github.com/salmansop123/airbnb-market-expert.git
cd airbnb-market-expert
pip install -r requirements.txt
playwright install chromium
2. Environment
Create a .env file in the root:

Ini, TOML
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=airbnb_expert
3. Run the Pipeline
Scrape: python scraper/airbnb_scraper.py

Train: python ml/price_model.py

API: uvicorn api.main:app --reload

UI: streamlit run dashboard/app.py

🛠️ Tech I Used
Backend: Python, FastAPI, Uvicorn

Frontend: Streamlit, Plotly (for the charts)

Database: MySQL

Machine Learning: XGBoost, Scikit-learn, Pandas

📈 Roadmap / Future Improvements
[ ] Add support for multi-city scraping.

[ ] Implement a cron job to auto-update the database weekly.

[ ] Containerize the whole thing using Docker for easier deployment.

Author: Salman