import sys
sys.path.insert(0, '.')
from tools.data_loader import DataLoader
from tools.rule_tool import RuleTool
from tools.eda_tool import EDATool

dl = DataLoader()
df = dl.load_transactions()
print(f"Dataset: {len(df)} rows x {df.shape[1]} cols")
print(f"Columns: {list(df.columns[:8])}")

eda_tool = EDATool(dl)
ov = eda_tool.get_dataset_overview()
print(f"Overview quality={ov.get('quality_score')} rows={ov.get('total_rows')}")

rule_tool = RuleTool(dl)
top_accounts = df["sender_account_id"].value_counts().head(3).index.tolist()
print(f"Testing account: {top_accounts[0]}")

res = rule_tool.evaluate_account(str(top_accounts[0]))
print(f"Flagged rules: {res['flagged_rules']}")
print(f"Score: {res['risk_score_contribution']}")
print("Pipeline validation SUCCESS")
