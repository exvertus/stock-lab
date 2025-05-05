import pytest

import grabbers.companies

@pytest.mark.integration
def test_sec():
    companies = grabbers.companies.sec()
