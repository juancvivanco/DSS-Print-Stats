import pandas as pd
import glob

# Getting relevant data
csv_file = glob.glob("*.csv")
df = pd.read_csv(csv_file[0])
data = pd.DataFrame()
data[['Batch', 'No. of Arches','Batch ID']] = df['Print name'].str.split('_', n = 2, expand = True)
data = data.drop(columns=['Batch ID'])
data['No. of Arches'] = data['No. of Arches'].str[:-1].astype(int)
data['Print time (min)'] = df['Elapsed print time (ms)']/60000
data['Status'] = df['Status']
data['Printer Serial'] = df['Printer'].str.split('-', n=1).str[1]
data['Model list'] = df['Parts'].str.split(', ').apply(lambda x: ['-'.join(name.split('_')[:1]) for name in x if name != 'Dentsply-form-spin-frame-punched'])

# Processing relevant data
arches = data['No. of Arches'].mean() # Arches per print
totalArches = data['No. of Arches'].sum()
printTime = data['Print time (min)'].where(~data['Status'].isin(['ABORTED', 'ERROR'])).mean() # Average print time ignoring prints that were aborted or errored out
archesPH = totalArches/47 # Throughput 
reported = 52 # For print defects reported downstream and arches that didn't pass inspection
checks = 0 # False alarms, manually aborted, etc.
pDowntime = 0.3 # Time spent doing maintenance per printer in hours
upDowntime = 0 # Time spent doing unplanned repairs in hours
allPrints = (data['Status'] != '').sum()
failCount = (data['Status'].isin(['ERROR', 'ABORTED', ''] or data['Print time (min)']<10)).sum() # For unfinished as stated in STATUS and downstream defects
finished = (data['Status'] == 'FINISHED').sum() # Prints successfully completed
failedArch = (reported/(totalArches + failCount*arches))*100 # Arches that didn't pass inspection
failRate = (failCount/(allPrints))*100

# Adjust last number here to total number of hours (16.5 per day 80 for a week) being considered for the uptime calculation
uptime = ((data['Print time (min)'].where(~data['Status'].isin(['ABORTED', 'ERROR'])).sum()/60)/(12*47))*100 # Time actually printing over a full week

# Print out stats
#print(data.head())
print(totalArches, 'arches in', finished, 'prints.')
print('Average of', round(archesPH, 2), 'arches per hour')
print("Number of arches per print:", round(arches, 2))
print("Print time in minutes:", round(printTime, 2))
print('Percentage of failed prints:', round(failRate, 2), "%")
print('Percentage of failed arches:', round(failedArch, 2), "%")
print(f'~{round(uptime, 2)}% percent of work hours spent printing')