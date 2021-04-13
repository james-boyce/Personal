#!/usr/bin/env python
# coding: utf-8
import os
import pandas as pd


#Function to find the helpfulness index
def helpIndex(row):
    if row['total_votes'] == 0:
        val = 0
    else:
        val = (row['helpful_votes'] / row['total_votes']) 
    return val

def filter_dataset(fileNumber):
    ## CHANGE THIS FOR EACH FILE (0-45)
    FILE_NO = fileNumber
    
    print(fileNumber)
    # ## Import and Explore Dataset
    
    
    df = pd.read_feather(str('./Data/Datasets/file' + str(FILE_NO) + '.feather'))
    
    
    
    print("The Number of total reviews = " + str(df.shape))
    
    
    ## Check for null
    df.isnull().sum().sum()
    
    
    
    ##Check for Duplicates
    data_duplicates = df[df.duplicated(subset=['product_id' ,'star_rating','review_headline', 'review_body'])]
    print('\033[34m' + '\033[1m' + '\033[4m' + "\nThe number of duplicate review_body in dataset:\n" + '\033[0m' +     str(data_duplicates.shape[0]))
    
    
    
    #Drop duplicates in dataset and reset index
    clean_df = df
    
    clean_df.drop_duplicates(subset = ['product_id', 'star_rating', 'review_headline', 'review_body'], keep='first', inplace=True)
    clean_df = clean_df.reset_index()

    
    # # Pre-Data Preperation Calculations
    # ## Calculate Customer Activity and Helpful/Total votes ---> Then Export to file
    
    """THESE FILES WILL BE COMBINED LATER TO CALCULATE ACTIVITY AND REPUTATION OF FULL DATASET"""
    
    customer = clean_df.groupby('customer_id')
    activity = customer['review_id'].agg('count')
    helpful = customer['helpful_votes'].agg('sum')
    total = customer['total_votes'].agg('sum')
    
    
    customer_df = pd.DataFrame({'customer_id':activity.index, 'Activity':activity.values, 'Helpful_Votes':helpful.values, 'Total_Votes':total.values})
    
    customer_df
    
    
    customer_df.to_feather(str('./Data/Customer_Data/customer_' + str(FILE_NO) + '.feather'))
    
    
    
    # # Data Prepertation
    # ## Prepare data columns
    
    
    prep_df = clean_df
    
    
    ## Remove Columns that are not to be used
    prep_df = prep_df.drop(["marketplace", "product_parent", ], axis = 1)
    
    
    ##Convert Dates to Date type
    prep_df['review_date'] = pd.to_datetime(prep_df['review_date'])
    
    
    # ## Filter for Products with earliest review in 2015
    
    #Group products together
    product_dates = prep_df.groupby('product_id')
    
    #Create list of the earliest review date of each product 
    min_date = product_dates['review_date'].agg('min')
    
    #Convert to dataframe
    min_df = min_date.to_frame(name='Min').reset_index()
    
    #Add year to the min_df
    min_df['Year'] = pd.DatetimeIndex(min_df['Min']).year
    
    
    #Filter for only products with the earliest review in 2015 (recent products)
    #Reset the index
    recent_products = min_df[min_df['Year'] == 2015]
    recent_products = recent_products.reset_index(drop=True)
    
    
    print("The Number of products = " + str(recent_products.shape))
    
    if recent_products.shape[0] != 0:
    
        #Create a reduced dataframe with only the products in recent_product dataframe
        reduced_df = pd.merge(recent_products, prep_df, on="product_id", how='left')
        
        print("The Number after filtering for 2015" + str(reduced_df.shape))
        
        
        # ## Filter for 10 <= reviews <= 100
        
        ##Find Number of reviews per product
        #Group by products
        product_reviews = reduced_df.groupby('product_id')
        
        #Count the number of review id's (reviews) per product
        product_review_count = product_reviews['review_id'].agg('count')
        
        #Convert to dataframe and reset index
        count_df = pd.DataFrame({'product_id':product_review_count.index, 'Review_count':product_review_count.values})
        count_df.shape
        
        #Filter out entries with less than 10 reviews
        filter_count = count_df[count_df['Review_count'] >= 10]
        filter_count = filter_count[filter_count['Review_count'] <= 100]
        filter_count = filter_count.reset_index(drop=True)
        filter_count
        
        if filter_count.shape[0] != 0:
            
            #Create a reduced dataframe with only the products in filter_count dataframe
            filter_df = pd.merge(filter_count, reduced_df, on="product_id", how='left')
            filter_df
            
            
            # ## Calculate Review Order
            
            ##Set order Dataframe
            order_df = filter_df
            
            
            ## Sort values by product then by date (earliest - oldest)
            order_df.sort_values(['product_id', 'review_date'], ascending=[True, True])
            
            
            ## Generate a list of the order of reviews
            prev_row = order_df['product_id'][0]
            order_num = 1
            order_list = []
            
            for index, row in order_df.iterrows():
                if prev_row == row['product_id']:
                    order_list.append(order_num)
                    order_num += 1
                    prev_row = row['product_id']
                else: 
                    order_num = 1
                    order_list.append(order_num)
                    order_num += 1
                    prev_row = row['product_id']
                
            
            ## Insert the list into df
            order_df.insert(17, 'Review_Order', order_list)
        
            
            # ## Filter Vine and Un-Verified Reviews
            
            verified_df = order_df[order_df['verified_purchase'] == 'Y']
            
            
            verified_df = verified_df[verified_df['vine'] == 'N']
            
            
            print("The Number after filtering vine and verified = " + str(verified_df.shape))
            
            
            # ## Calculate Helpfulness per review
        
            ## Generate helpfulness index for each review
            verified_df['helpfulness_index'] = verified_df.apply(helpIndex, axis=1)
            verified_df = verified_df.round(2)
            verified_df.head()
            
            
            # ## Calculate Review and Summary Length
            
            #Add Review Length
            verified_df['Text_Length'] = verified_df['review_body'].str.split().str.len()
            verified_df['Summary_Length'] = verified_df['review_headline'].str.split().str.len()
            
            verified_df.head()
            
            
            # ## Data Export
            final_df = verified_df.sample(frac=1).reset_index(drop=True)
            final_df.to_feather(str('./Data/Filtered_Data/filter_' + str(FILE_NO) + '.feather'))
    

for num in range(0, 46):
    filter_dataset(num)
    




