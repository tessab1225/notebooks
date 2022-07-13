#%%
import pandas as pd
from pathlib import Path


#%%
# Make a list of all csv files in the relevant folder using pathlib
all_files = Path('data/PIP_percentiles_raw').glob('*.csv')

# Read in and concat (append together) all the files
df = pd.concat((pd.read_csv(f) for f in all_files))

#%%
# Cleaning - see notebook for discussion

# Drop El Salvador and Sierra Leone (negative poverty lines)
df = df[~df['entity'].isin(['El Salvador', 'Sierra Leone'])]

# Drop headcount=0 observations
df = df[df['headcount']!=0]

# Drop duplicate rows (generated by the different requested
# percentiles returning the same `headcount`).
cols = [i for i in df.columns if i not in ['requested_p']]

df = df.drop_duplicates(subset=['entity', 'year', 'reporting_level', 'welfare_type', 'poverty_line','headcount'], keep='first')


#%%
# Write to .CSV
df.to_csv('data/PIP_percentiles_raw_aggregated.csv', index=False)
#%%


