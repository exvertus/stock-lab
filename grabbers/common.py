"""
Common code shared by other grabbers.
"""
import os
import requests
from dotenv import load_dotenv
from ratelimit import limits, sleep_and_retry

load_dotenv()

SEC_CALLS_PER_SECONDS = (10, 1)

def get_sec_session():
    """
    Returns Session with headers for sec requests.
    """
    user_agent_name = os.getenv("SEC_USER_AGENT_NAME")
    user_agent_email = os.getenv("SEC_USER_AGENT_EMAIL")

    if not user_agent_name or not user_agent_email:
        raise EnvironmentError("Set SEC_USER_AGENT_NAME and SEC_USER_AGENT_EMAIL environment variables.")

    user_agent = f"{user_agent_name} {user_agent_email}"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent
    })
    return session

@sleep_and_retry
@limits(calls=SEC_CALLS_PER_SECONDS[0], period=SEC_CALLS_PER_SECONDS[1])
def fetch_sec_data(url, session=None):
    """
    Use for grabbing SEC data according to fair access rules. See:
    https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
    """
    if session is None:
        session = get_sec_session()
    resp = session.get(url)
    resp.raise_for_status()
    return resp
