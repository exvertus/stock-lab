from dotenv import load_dotenv
from edgar import Company
from edgar.reference.tickers import get_company_tickers

from common.edgar import QuarterlyData

load_dotenv()

sec_companies = get_company_tickers()

#TODO: Add tqdm for progress bar
for index, row in sec_companies.iterrows():
    cik = row['cik']
    ticker = row['ticker']
    company_name = row['company']

    company = Company(cik)
    quarterly_filings = company.get_filings(form=['10-K', '10-Q'])

    # TODO: Split by 10-Q vs 10-K
    for quarter in quarterly_filings:
        quarter_data = QuarterlyData(
            accession_number=quarter
        )

    print("break")
