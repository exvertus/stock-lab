"""
Grab lists of companies from a variety of sources.
Each source returns a panda df and includes ticker symbols.
but differ in terms of breadth, recency, and additional data.
"""

import json
import pandas as pd

import grabbers.common

def sec():
    """
    About 9500 companies. Includes cik numbers for grabbing from EDGAR.
    """
    source_url = r"https://www.sec.gov/files/company_tickers.json"
    session = grabbers.common.get_sec_session()
    resp = grabbers.common.fetch_sec_data(source_url, session)
    data = resp.json()
    records = [v for k, v in data.items()]
    df = pd.DataFrame.from_records(records)
    # TODO: zero-pad CIK to 10 digits here? Or when building links?
    print("break")

def wsj():
    """
    """
    url_format = r"https://www.wsj.com/market-data/quotes/company-list/country/united-states/{page}"
    print("break")

def nasdaqtrader():
    """
    """
    print("break")
