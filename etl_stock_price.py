# -*- coding: utf-8 -*-
"""etl_stock_price.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1yD4Xi31YWW6sF5TQuTzytoXnBITFe_wa
"""

from airflow import DAG
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime
from airflow.utils.dates import days_ago

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.models import Variable
from airflow.decorators import task
import requests

def return_snowflake_conn():
    hook = SnowflakeHook(snowflake_conn_id='snowflake_conn')
    return hook.get_conn().cursor()

@task
def extract(url):
    res = requests.get(url)
    res_json = res.json()
    results = []
    for d in res_json["Time Series (Daily)"]:
      results.append(res_json["Time Series (Daily)"][d])
      daily_info = res_json["Time Series (Daily)"][d]
      daily_info['6. date'] = d
      results.append(daily_info)
    return results[-90:]

@task
def transform(results):
    for r in results:
        open =   r['1. open'].replace("'", "''")
        high =   r['2. high'].replace("'", "''")
        low =    r['3. low'].replace("'", "''")
        close =  r['4. close'].replace("'", "''")
        volume = r['5. volume'].replace("'", "''")
        date =   r['6. date'].replace("'", "''")
        print(open, "-", high, "-", low, "-", "close", "-", volume, "-", date)
    return results

@task
def load(con, results, target_table):
  try:
    con.execute("BEGIN")
    con.execute(f"""CREATE OR REPLACE TABLE {target_table} (
            open DECIMAL(10, 4) NOT NULL,
            high DECIMAL(10, 4) NOT NULL,
            low DECIMAL(10, 4) NOT NULL,
            close DECIMAL(10, 4) NOT NULL,
            volume BIGINT NOT NULL,
            date DATE NOT NULL,
            PRIMARY KEY (date)
        )""")
    for r in results:
        open =   r['1. open'].replace("'", "''")
        high =   r['2. high'].replace("'", "''")
        low =    r['3. low'].replace("'", "''")
        close =  r['4. close'].replace("'", "''")
        volume = r['5. volume'].replace("'", "''")
        date =   r['6. date'].replace("'", "''")

        sql = f"INSERT INTO {target_table} (open, high, low, close, volume, date) VALUES ('{open}', '{high}', '{low}', '{close}', '{volume}', '{date}')"
        con.execute(sql)
    con.execute("COMMIT")
  except Exception as e:
        con.execute("ROLLBACK")
        print(e)
        raise(e)

with DAG (
    dag_id = 'etl_flow_realtime_stock_price',
    description = 'ETL Pipeline from AlphaVantage to Snowflake',
    start_date = datetime(2024,10,6),
    catchup=False,
    tags=['ETL'],
    schedule = '30 15 * * *'
) as dag:
    target_table = "dev.raw_data.alphavantage_stockprice"
    api_key = Variable.get("alphavantage_apikey")
    url = Variable.get("url")
    cur = return_snowflake_conn()

    output = extract(url)
    transformed_output = transform(output)
    load(cur, results = transformed_output, target_table=target_table)
