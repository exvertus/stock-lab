import pandas as pd

# example: revenue pipeline
# first_tag > check_duration > max_end_date > max_start_date > max_value > 

def match_first_in_column(df, column, candidates):
    """
    Return all rows where the given column matches the first value found in `candidates`.
    Subsequent values are ignored once a match is found.
    """
    # Create an empty DataFrame with the same columns and types
    results = pd.DataFrame(columns=df.columns)
    for cand in candidates:
        results = df[df[column] == cand]
        if not results.empty:
            return results
    return results

