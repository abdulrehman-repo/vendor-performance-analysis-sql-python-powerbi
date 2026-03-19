import sqlite3
import pandas as pd
import logging
from ingestion import ingest_db
import time

logging.basicConfig(
    filename="logs/get_vendor_summary.log", 
    level=logging.DEBUG, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
    filemode="a"
)

def create_vendor_summary(conn):
    '''This table merge the different tables to get the overall vendor summary and adding new columns to the resultant data.'''
    start = time.time()
    vendor_sales_summary = pd.read_sql_query(""" WITH FreightSummary AS (
        Select 
            VendorNumber,
            VendorName,
            sum(Freight) as TotalFreightCost
        FROM vendor_invoice
        GROUP BY VendorNumber
    ),
    
    PurchaseSummary AS (
        SELECT 
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            pp.Price AS ActualPrice,
            p.PurchasePrice AS PurchasePrice,
            pp.Volume,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) as TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
        WHERE p.PurchasePrice>0
        GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
        
    ),
    
    SalesSummary AS (
        SELECT 
            VendorNo,
            Brand,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(ExciseTax) AS TotalExciseTax
        FROM Sales
        GROUP BY VendorNo,Brand
        
    )
    
    
    SELECT
        ps. VendorNumber,
        ps. VendorName,
        ps.Brand,
        ps.Description,
        ps.PurchasePrice,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.TotalFreightCost
    FROM PurchaseSummary ps
    LEFT JOIN SalesSummary ss
        ON ps. VendorNumber = ss. VendorNo
        AND ps.Brand = ss.Brand
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    ORDER BY ps.TotalPurchaseDollars DESC""", conn)
    
    end = time.time()
    print(f"Time taken: {(end - start)/60}")

    return vendor_sales_summary

def clean_data(df):
    '''This function will clean the data'''
    #Changing datatype to float
    df['Volume'] = df['Volume'].astype('float64') 
    
    #Filling missing values with 0
    df.fillna(0, inplace=True)
    
    #For removing irrelevent space from catogerical columns
    df['VendorName'] = df['VendorName'].str.strip() 
    df['Description'] = df['Description'].str.strip() 

    #Creating new columns for better Analysis
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars'] 
    df['ProfitMargin'] = (df['GrossProfit'] / df['TotalSalesDollars']) * 100 
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalesPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']

    return df

if __name__ == '__main__':
    # creating database connection
    conn = sqlite3.connect('inventory.db')
    
    logging.info('Creating Vendor Summary Table.....')
    summary_df = create_vendor_summary(conn)
    conn.close()
    logging.info(summary_df.head())
    
    logging.info('Cleaning Data.....')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())
    
    logging.info('Ingesting data.....')
    conn = sqlite3.connect('inventory.db')
    ingest_db(clean_df, 'vendor_sales_summary',conn)
    conn.close()
    logging.info('Completed')