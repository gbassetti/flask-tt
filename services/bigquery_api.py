from flask import url_for
import pandas as pd
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud.exceptions import NotFound



# Google BigQuery authentication
credentials = service_account.Credentials.from_service_account_file('keys/spadotto-f1fdb-e96f694cf185.json')
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

@dataclass
class BigQueryAPI:

    def get_bq_table(self, table_id: str):
        try:
            sql = f"SELECT * FROM `{table_id}`"
            df = client.query(sql).to_dataframe()
            return df
        except: pass

    def get_athlete_ids(self, table_id):
        # Make BigQuery API request to get athletes
        df = self.get_bq_table(table_id)
        athletes_list = df['Id'].tolist()

        i = 0
        for j in athletes_list:
            i = i + 1
        
        return athletes_list, i
    
    def count_athletes(self, list):
        i = 0
        for j in list:
            i = i + 1
        return i

    def upload_response_to_bq(self, data,table_id: str):
        # Make a Dataframe with the response from the TrainingPeaks API request.
        list_data = json.loads(data)   
        df1 = pd.DataFrame(list_data)
        df1['updatedAt'] = datetime.now().replace(tzinfo=timezone.utc)
        
        try: 
            # Make API request to get the current table from BigQuery to a Dataframe.
            df2 = self.get_bq_table(table_id)
            
            # Concatenate Dataframes and remove duplicate entries (by Id), keeping the latest.
            df = pd.concat([df1, df2])
            df = df.sort_values('updatedAt').drop_duplicates('Id',keep='last')
        except NotFound:
            df = df1
        if '__index_level_0__' in df.columns: df = df.drop('__index_level_0__', axis=1)

        # Make BigQuery API request to replace the table.
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config,)  # Make an API request.
        job.result()  # Wait for the job to complete.
        

        #table = client.get_table(table_id)  # Make an API request.
        #print("Loaded {} rows and {} columns to {}".format(table.num_rows, len(table.schema), table_id))

    def upload_df_to_bq(self, df,table_id: str):
        # Make a Dataframe with the response from the TrainingPeaks API request.
        if '__index_level_0__' in df.columns: df = df.drop('__index_level_0__', axis=1)

        # Make BigQuery API request to replace the table.
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config,)  # Make an API request.
        job.result()  # Wait for the job to complete.
        return