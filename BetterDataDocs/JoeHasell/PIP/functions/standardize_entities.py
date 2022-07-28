# %%
# ACCESS TO STORAGE ----

# Acess keys to write to  our s3 cloud storage
from access_key import KEY_ID, SECRET_KEY 

# boto3  allows us to write data to our s3 cloud storage
import boto3

# A function we have written to help upload our data to our s3 cloud storage
from functions.upload import upload_to_s3

# Set up access for writing files to s3  
session = boto3.session.Session()

client = session.client('s3',
                        endpoint_url="https://joeh.fra1.digitaloceanspaces.com",
                        aws_access_key_id=KEY_ID,
                        aws_secret_access_key=SECRET_KEY)

# %%
# Load packages

# Pandas is a standard package used for data manipulation in python code
import pandas as pd
               


# %%
def standardize_entities(orig_df,
                        entity_mapping_url,
                        mapping_varname_raw,
                        mapping_vaname_owid,
                        data_varname_old,
                        data_varname_new):


    # Read in mapping table which maps PWT names onto OWID names.
    df_mapping = pd.read_csv(entity_mapping_url)

    # Merge in mapping to raw
    df_harmonized = pd.merge(orig_df,df_mapping,
      left_on=data_varname_old,right_on=mapping_varname_raw, how='left')
    
    # Drop the old entity names column, and the matching column from the mapping file
    df_harmonized = df_harmonized.drop(columns=[data_varname_old, mapping_varname_raw])
    
    # Rename the new entity column
    df_harmonized = df_harmonized.rename(columns={mapping_vaname_owid:data_varname_new})

    # Move the entity column to front:

    # get a list of columns
    cols = list(df_harmonized)
    
    # move the country column to the first in the list of columns
    cols.insert(0, cols.pop(cols.index(data_varname_new)))
    
    # reorder the columns of the dataframe according to the list
    df_harmonized = df_harmonized.loc[:, cols]

    return df_harmonized

# %%
