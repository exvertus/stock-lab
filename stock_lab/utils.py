import os
from pathlib import Path

from edgar import Filing, Company, get_filings
from edgar.xbrl.xbrl import XBRL

REPO_ROOT = Path(__file__).parent.parent

def save_latest_quarters(ticker, n, save_dir):
    """
    Save n latest quarterly filings instances to disk as pkl files.
    """
    company = Company(ticker)
    quarterly_filings = company.get_filings().filter(form=["10-K", "10-Q"])
    for quarter in quarterly_filings.latest(n):
        quarter.save(save_dir)

def load_filing_from_file(pkl_file):
    """
    Load previously saved quarterly filings .pkl file.
    """
    return Filing.load(Path(pkl_file))

def load_filings_from_dir(load_dir):
    """
    Load previously saved quarterly filings .pkl files from a directory.
    Returns list of filings.
    """
    filings = []
    for p in Path(load_dir).glob("*.pkl"):
        filings.append(Filing.load(p))
    return filings

def filings_facts_to_csv(filing, save_path=REPO_ROOT/".inspect"):
    """
    Export filing fact data to a csv file.
    """
    facts_df = XBRL.from_filing(filing).facts.to_dataframe()
    if save_path.is_dir():
        facts_df.to_csv(save_path/f"{filing.accession_no}.csv")
    else:
        facts_df.to_csv(save_path)
