import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class EDAAnalyzer:
    def __init__(self, data_loader):
        self.dl = data_loader

    def generate_dataset_profiling(self, df_override: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Generates comprehensive dataset profiling, descriptive statistics matrix,
        correlation heatmaps, column type inference, and distribution metrics.
        Never uses placeholder data. Performs 100% real calculations on the active dataset.
        """
        df = df_override if df_override is not None else self.dl.load_transactions()
        if df is None or df.empty:
            return {"empty": True, "error": "No dataset loaded.\nUpload a CSV, Excel, or Parquet file to begin analysis."}

        rows, cols = df.shape
        if rows < 5:
            return {"insufficient_rows": True, "error": "Dataset is too small for meaningful statistical analysis."}

        # -------------------------------------------------------------
        # 1. COLUMN TYPE INFERENCE
        # -------------------------------------------------------------
        numeric_cols: List[str] = df.select_dtypes(include=[np.number]).columns.tolist()
        bool_cols: List[str] = df.select_dtypes(include=['bool']).columns.tolist()
        
        date_cols = []
        for col in df.columns:
            if col not in numeric_cols and col not in bool_cols:
                if 'date' in col.lower() or 'time' in col.lower() or 'timestamp' in col.lower():
                    date_cols.append(col)

        id_cols = []
        for col in df.columns:
            col_l = col.lower()
            if ('id' in col_l or 'account' in col_l or 'customer' in col_l or 'num' in col_l) and col not in date_cols:
                id_cols.append(col)

        categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in bool_cols and c not in date_cols and c not in id_cols]

        # -------------------------------------------------------------
        # 2. DATASET QUALITY & PROFILING METRICS
        # -------------------------------------------------------------
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / rows) * 100, 2)
        
        missing_counts = df.isnull().sum().to_dict()
        total_missing = sum(missing_counts.values())
        total_cells = rows * cols
        missing_pct = round((total_missing / total_cells) * 100, 2)
        
        missing_pcts_by_col = {k: round((v / rows) * 100, 2) for k, v in missing_counts.items()}
        completeness_by_col = {k: round(100.0 - v, 2) for k, v in missing_pcts_by_col.items()}
        
        unique_cols_count = int(sum(1 for col in df.columns if df[col].nunique() == rows))
        memory_usage_mb = round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 2)
        data_types = {col: str(df[col].dtype) for col in df.columns}
        
        quality_score = float(max(0.0, min(100.0, round(100.0 - missing_pct - (duplicate_pct * 0.5), 1))))

        # -------------------------------------------------------------
        # 3. DESCRIPTIVE STATISTICAL SUMMARY MATRIX
        # -------------------------------------------------------------
        desc_stats = {}
        for col in numeric_cols:
            series = df[col].dropna()
            if not series.empty:
                cnt = int(series.count())
                mean_v = float(series.mean())
                std_v = float(series.std()) if cnt > 1 else 0.0
                var_v = float(series.var()) if cnt > 1 else 0.0
                med_v = float(series.median())
                mode_res = series.mode()
                mode_v = float(mode_res.iloc[0]) if not mode_res.empty else mean_v
                min_v = float(series.min())
                max_v = float(series.max())
                q25_v = float(series.quantile(0.25))
                q50_v = float(series.quantile(0.50))
                q75_v = float(series.quantile(0.75))
                iqr_v = float(q75_v - q25_v)
                skew_v = float(series.skew()) if cnt > 2 else 0.0
                kurt_v = float(series.kurtosis()) if cnt > 3 else 0.0
                miss_cnt = int(df[col].isnull().sum())
                uniq_cnt = int(series.nunique())

                desc_stats[col] = {
                    "Count": cnt,
                    "Missing Count": miss_cnt,
                    "Unique Count": uniq_cnt,
                    "Mean": round(mean_v, 4),
                    "Median": round(med_v, 4),
                    "Mode": round(mode_v, 4),
                    "Min": round(min_v, 4),
                    "Max": round(max_v, 4),
                    "Std Dev": round(std_v, 4),
                    "Variance": round(var_v, 4),
                    "25%": round(q25_v, 4),
                    "50%": round(q50_v, 4),
                    "75%": round(q75_v, 4),
                    "IQR": round(iqr_v, 4),
                    "Skewness": round(skew_v, 4),
                    "Kurtosis": round(kurt_v, 4)
                }

        # -------------------------------------------------------------
        # 4. CORRELATION MATRICES (PEARSON & SPEARMAN)
        # -------------------------------------------------------------
        corr_pearson = {}
        corr_spearman = {}
        if len(numeric_cols) >= 2:
            num_df = df[numeric_cols].dropna()
            if not num_df.empty:
                corr_pearson = num_df.corr(method='pearson').round(3).to_dict()
                corr_spearman = num_df.corr(method='spearman').round(3).to_dict()

        # -------------------------------------------------------------
        # 5. TRANSACTION AMOUNT DISTRIBUTION ANALYTICS
        # -------------------------------------------------------------
        amount_cols = [c for c in numeric_cols if any(term in c.lower() for term in ['amount', 'amt', 'val', 'volume', 'price', 'cost', 'balance', 'sum'])]
        if not amount_cols and numeric_cols:
            amount_cols = [numeric_cols[0]]

        amount_stats = {}
        for amt_c in amount_cols:
            s = df[amt_c].dropna()
            if not s.empty:
                q25 = float(s.quantile(0.25))
                q75 = float(s.quantile(0.75))
                iqr = q75 - q25
                outlier_mask = (s < (q25 - 1.5 * iqr)) | (s > (q75 + 1.5 * iqr))
                outlier_count = int(outlier_mask.sum())
                
                amount_stats[amt_c] = {
                    "column_name": amt_c,
                    "mean": float(round(s.mean(), 2)),
                    "median": float(round(s.median(), 2)),
                    "min": float(round(s.min(), 2)),
                    "max": float(round(s.max(), 2)),
                    "std": float(round(s.std(), 2)) if len(s) > 1 else 0.0,
                    "p95": float(round(s.quantile(0.95), 2)),
                    "p99": float(round(s.quantile(0.99), 2)),
                    "outlier_count": outlier_count,
                    "outlier_pct": float(round((outlier_count / len(s)) * 100, 2)),
                    "series_values": s.sample(min(2000, len(s)), random_state=42).tolist()
                }

        # Time series hourly aggregate if timestamp present
        hourly_velocity = []
        if date_cols:
            try:
                time_col = date_cols[0]
                df_time = df.copy()
                df_time['datetime'] = pd.to_datetime(df_time[time_col], errors='coerce')
                df_time['hour'] = df_time['datetime'].dt.hour
                if 'amount' in df_time.columns:
                    h_agg = df_time.groupby('hour')['amount'].agg(['count', 'sum']).reset_index()
                    hourly_velocity = h_agg.to_dict(orient="records")
            except Exception:
                pass

        return {
            "empty": False,
            "insufficient_rows": False,
            "dimensions": {"rows": rows, "cols": cols},
            "column_types": {
                "numeric": numeric_cols,
                "categorical": categorical_cols,
                "date": date_cols,
                "bool": bool_cols,
                "id": id_cols
            },
            "quality_metrics": {
                "total_rows": rows,
                "total_cols": cols,
                "duplicate_rows": duplicate_rows,
                "duplicate_pct": duplicate_pct,
                "missing_values": total_missing,
                "missing_pct": missing_pct,
                "unique_cols_count": unique_cols_count,
                "memory_usage_mb": memory_usage_mb,
                "quality_score": quality_score,
                "missing_pcts_by_col": missing_pcts_by_col,
                "completeness_by_col": completeness_by_col,
                "data_types": data_types
            },
            "descriptive_statistics": desc_stats,
            "corr_pearson": corr_pearson,
            "corr_spearman": corr_spearman,
            "amount_cols": amount_cols,
            "amount_stats": amount_stats,
            "hourly_velocity": hourly_velocity
        }

    def generate_summary(self, account_id: str) -> str:
        """
        Generates a human-readable profile summary of an account for the LLM.
        """
        try:
            cust_df = self.dl.load_customers()
            profile_text = ""
            if not cust_df.empty:
                cust_info = duckdb.query(f"SELECT * FROM cust_df WHERE customer_id = '{account_id}'").df()
                if not cust_info.empty:
                    row = cust_info.iloc[0]
                    profile_text = f"Customer Profile: {row.get('age', 'Unknown')} yr old {row.get('customer_type', 'Unknown')} in {row.get('city', 'Unknown')}.\n"
            
            tx_df = self.dl.load_transactions()
            stats = duckdb.query(f"""
                SELECT 
                    COUNT(*) as total_tx,
                    SUM(CASE WHEN receiver_account_id = '{account_id}' THEN amount ELSE 0 END) as total_in,
                    SUM(CASE WHEN sender_account_id = '{account_id}' THEN amount ELSE 0 END) as total_out
                FROM tx_df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """).df()
            
            if stats.empty or stats['total_tx'].iloc[0] == 0:
                return f"No transaction history found for {account_id}."
                
            total_in = stats['total_in'].iloc[0] or 0
            total_out = stats['total_out'].iloc[0] or 0
            total_tx = stats['total_tx'].iloc[0]
            
            summary = f"Account {account_id} Analysis:\n"
            summary += profile_text
            summary += f"Total Transactions: {total_tx}\n"
            summary += f"Total Money In: ${total_in:,.2f}\n"
            summary += f"Total Money Out: ${total_out:,.2f}\n"
            summary += f"Net Flow: ${(total_in - total_out):,.2f}\n"
            
            return summary
        except Exception as e:
            return f"Error generating EDA: {str(e)}"
