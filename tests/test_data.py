import pandas as pd

from stock_lab.facts import FilingFacts

first_concepts = [val["tags"][0] for val in FilingFacts.gaap_tags.values()]
last_concepts = [val["tags"][-1] for val in FilingFacts.gaap_tags.values()]
period_starts = ["2020-07-01" if val['period_type'] == "duration" 
                 else float('nan') 
                 for val in FilingFacts.gaap_tags.values()]
period_starts_results = [pd.Timestamp(start) for start in period_starts]
period_ends = ["2020-10-01" if val['period_type'] == "duration" 
               else float('nan') 
               for val in FilingFacts.gaap_tags.values()]
period_ends_results = [pd.Timestamp(end) for end in period_ends]
period_instants = ["2020-10-01" if val['period_type'] == "instant" 
                   else float('nan') 
                   for val in FilingFacts.gaap_tags.values()]
period_instants_results = [pd.Timestamp(instant) for instant in period_instants]
period_types = [val["period_type"] for val in FilingFacts.gaap_tags.values()]
acceptable_values = [
                "100000", # revenue
                "1.23",    # eps
                "400000",  # diluted_shares
                "400",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ]
acceptable_results = [
                100000, # revenue
                1.23,    # eps
                400000,  # diluted_shares
                400,     # net_income
                500,     # operating_income
                234,     # operating_cash_flow
                -3000,   # cap_ex
                240,     # gross_profit
                30000    # cash_equivalents
            ]

negative_revenue = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "-100000", # revenue
                "1.23",    # eps
                "400000",  # diluted_shares
                "400",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

eps_non_number = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "NVDA",    # eps
                "400000",  # diluted_shares
                "400",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

zero_shares = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "0",       # diluted_shares
                "400",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

income_non_numeric = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "NaN",     # net_income
                "500",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

op_income_non_numeric = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "400",     # net_income
                "bla",     # operating_income
                "234",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

op_cash_non_numeric = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "400",     # net_income
                "600",     # operating_income
                "ggg",     # operating_cash_flow
                "-3000",   # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

cap_ex_positive = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "400",     # net_income
                "654",     # operating_income
                "234",     # operating_cash_flow
                "3000",    # cap_ex
                "240",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

gross_profit_non_numeric = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "400",     # net_income
                "654",     # operating_income
                "234",     # operating_cash_flow
                "3000",    # cap_ex
                "rrr",     # gross_profit
                "30000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })

negative_cash_eq = pd.DataFrame({
            "concept": first_concepts,
            "value": [
                "100000",  # revenue
                "1.54",    # eps
                "100000",  # diluted_shares
                "400",     # net_income
                "654",     # operating_income
                "234",     # operating_cash_flow
                "3000",    # cap_ex
                "400",     # gross_profit
                "-3000"    # cash_equivalents
            ],
            "period_end": period_ends,
            "period_start": period_starts,
            "period_instant": period_instants,
            "period_type": period_types
        })
