import pandas as pd


def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def create_multilevel_df(data: list[dict]) -> pd.DataFrame:
    sep = '___'
    flattened_data = [flatten_dict(item, sep=sep) for item in data]
    df = pd.DataFrame(flattened_data)
    multiindex_columns = [tuple(col.split(sep)) for col in df.columns]
    df.columns = pd.MultiIndex.from_tuples(multiindex_columns)
    return df
