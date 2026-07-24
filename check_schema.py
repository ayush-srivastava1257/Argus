import duckdb
df = duckdb.query("SELECT * FROM read_csv_auto('data/ibm_aml/HI-Small_Trans.csv') LIMIT 2").df()
print("Columns:", df.columns.tolist())
print(df.head())
