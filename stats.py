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
reported = 0 # For print defects reported downstream
failCount = (data['Status'].isin(['ERROR', 'ABORTED', ''])).sum() + reported # For unfinished as stated in STATUS and downstream defects
finished = (data['Status'] == 'FINISHED').sum() # Prints successfully completed
failRate = (failCount/(failCount + finished))*100
uptime = data['Print time (min)'].where(~data['Status'].isin(['ABORTED', 'ERROR'])).sum()/99

# Print out stats
#print(data.head())
print(totalArches, 'arches in', finished, 'prints.')
print("Number of arches per print:", round(arches, 2))
print("Print time in minutes:", round(printTime, 2))
print('Percentage of failed prints:', round(failRate, 2), "%")
print(f'{round(uptime, 2)}% percent of work hours were spent printing')
