# Project Sentry: Social Media Campaign Analyzer

## Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd cybershelid
```

2. **Set up Python Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install Requirements**
```bash
pip install -r requirements.txt
```

## Running the Application

1. **Start the Streamlit app**
```bash
streamlit run app.py
```

2. **Access the Application**
- The app will automatically open in your default web browser
- If not, open: http://localhost:8501

## Using the Application

1. In the sidebar, enter a hashtag (without the # symbol)
2. Click "Run Analysis" button
3. View the generated network graph and data analysis

## Requirements
- Python 3.7+
- Internet connection for Twitter API access
- Dependencies listed in requirements.txt:
  - streamlit
  - pandas
  - tweepy
  - networkx
  - transformers
  - torch
  - graphviz

## Troubleshooting
- If you see import errors, ensure all requirements are installed
- Make sure your virtual environment is activated
- Check your internet connection for API access
