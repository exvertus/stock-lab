from dotenv import load_dotenv
from edgar.reference.tickers import get_company_tickers

load_dotenv()

sec_companies = get_company_tickers()

print("break")