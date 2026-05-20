import pandas as pd
import glob
import re

csv_file = glob.glob("*.csv")
df = pd.read_csv(csv_file[0])
data = pd.DataFrame()

data[['Batch', 'No. of Arches','Batch ID']] = df['Print name'].str.split('_', n = 2, expand = True)
data = data.drop(columns=['Batch ID'])
data['No. of Arches'] = data['No. of Arches'].str[:-1].astype(int)

data['Start time'] = pd.to_datetime(df['Start time'])
data['Finish time'] = pd.to_datetime(df['Finish time'])
data['Print time (min)'] = (data['Finish time'] - data['Start time']).dt.total_seconds() / 60

data['Status'] = df['Status']
data['Printer Serial'] = df['Printer'].str.split('-', n=1).str[1]
data['Model list'] = df['Parts'].str.split(', ').apply(lambda x: ['-'.join(name.split('_')[:1]) for name in x if name != 'Dentsply-form-spin-frame-punched'])
data['Volume (L)'] = df['Volume (ml)']/1000

arches = data['No. of Arches'].mean() 
totalArches = data['No. of Arches'].sum()
printTime = data['Print time (min)'].where(~data['Status'].isin(['ABORTED', 'ERROR'])).mean() 
resinAvg = data['Volume (L)'].mean()
resinTot = data['Volume (L)'].sum()
reported = 0 
checks = 0 
pDowntime = 0.3 
upDowntime = 0 
failCount = (data['Status'].isin(['ERROR', 'ABORTED', ''] or data['Print time (min)']<10)).sum() 
finished = (data['Status'] == 'FINISHED').sum() 
failedArch = (reported/(totalArches + failCount*arches))*100 

# --- TRUE OPERATOR THROUGHPUT CALCULATOR ---
first_start = data['Start time'].min()
last_start = data['Start time'].max()
operator_span_hours = (last_start - first_start).total_seconds() / 3600
avg_print_hours = printTime / 60
breaks_hours = 2 
total_active_hours = operator_span_hours + avg_print_hours - breaks_hours

if total_active_hours > 0:
    archesPH = totalArches / total_active_hours
else:
    archesPH = 0

data_sorted = data.sort_values(by=['Printer Serial', 'Start time']).copy() 
data_sorted['Previous Finish'] = data_sorted.groupby('Printer Serial')['Finish time'].shift(1)
data_sorted['Idle Time'] = data_sorted['Start time'] - data_sorted['Previous Finish']

valid_idle = data_sorted['Idle Time'].dropna()
valid_idle = valid_idle[valid_idle.dt.total_seconds() > 0]
avg_idle_time = valid_idle.mean()
avg_idle_minutes = avg_idle_time.total_seconds() / 60

valid_idle_filtered = data_sorted['Idle Time'].dropna()
valid_idle_filtered = valid_idle_filtered[(valid_idle_filtered.dt.total_seconds() > 0) & (valid_idle_filtered.dt.total_seconds() <= 1800)]
median_idle_time = valid_idle_filtered.median()
median_idle_minutes = median_idle_time.total_seconds() / 60

uptime = ((data['Print time (min)'].where(~data['Status'].isin(['ABORTED', 'ERROR'])).sum()/60)/(12*16.5))*100 

print(totalArches, 'arches in', finished, 'prints.')
print('Average of', round(archesPH, 2), 'arches per hour')
print('Total active printing hours', round(total_active_hours, 2))
print("Number of arches per print:", round(arches, 2))
print("Print time in minutes:", round(printTime, 2))
print(f'~{round(uptime, 2)}% percent of work hours spent printing')
print('Estimated resin use per print (L):', round(resinAvg, 2))
print('Estimated total resin used (L):', round(resinTot, 2))
print(f"Average time between prints: {round(avg_idle_minutes, 2)} minutes")
print(f"Median time between prints: {round(median_idle_minutes, 2)} minutes")

target_file = 'SO-SR03000831-Arch-018-074'
matching_rows = data[data['Model list'].apply(lambda models: target_file in models if isinstance(models, list) else False)]

if not matching_rows.empty:
    print(f"\nFile '{target_file}' found in:")
    unique_matches = matching_rows[['Batch', 'Printer Serial']].drop_duplicates()
    for _, row in unique_matches.iterrows():
        print(f" - Batch: {row['Batch']} | Printer: {row['Printer Serial']}")
else:
    print(f"\nFile '{target_file}' was not found in any batch.")

data_sorted = data.sort_values(by=['Printer Serial', 'Start time']).copy()
data_sorted['Previous Finish'] = data_sorted.groupby('Printer Serial')['Finish time'].shift(1)
data_sorted['Idle Time'] = (data_sorted['Start time'] - data_sorted['Previous Finish']).dt.total_seconds() / 60

def get_avg_idle(series):
    valid = series[series > 0]
    return valid.mean()

def get_median_idle(series):
    valid = series[(series > 0) & (series <= 60)]
    return valid.median()

printer_stats = data_sorted.groupby('Printer Serial').agg(
    Total_Prints=('Printer Serial', 'count'),
    Avg_Print_Time=('Print time (min)', 'mean'),
    Avg_Idle_Time=('Idle Time', get_avg_idle),
    Median_Idle_Time=('Idle Time', get_median_idle)
).reset_index()

printer_stats['Avg_Print_Time'] = printer_stats['Avg_Print_Time'].round(2)
printer_stats['Avg_Idle_Time'] = printer_stats['Avg_Idle_Time'].round(2)
printer_stats['Median_Idle_Time'] = printer_stats['Median_Idle_Time'].round(2)

printer_stats.columns = ['Printer', 'Total Prints', 'Avg Print Time (min)', 'Avg Time Between (min)', 'Median Time Between (min)']

print("\n--- STATS BY PRINTER ---")
print(printer_stats.to_string(index=False))