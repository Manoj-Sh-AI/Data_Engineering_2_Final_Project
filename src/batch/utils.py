cat > src/batch/utils.py << 'EOF'
"""Utility functions for batch processing"""

import pandas as pd
from google.cloud import storage, bigquery

def read_from_gcs(bucket_name, file_path):
    """Read CSV from GCS"""
    df = pd.read_csv(f'gs://{bucket_name}/{file_path}')
    return df

def write_to_gcs(df, bucket_name, file_path):
    """Write DataFrame to GCS"""
    df.to_csv(f'gs://{bucket_name}/{file_path}', index=False)

def load_to_bigquery(df, project_id, dataset, table):
    """Load DataFrame to BigQuery"""
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    return job.output_rows
EOF
