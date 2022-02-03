import pandas as pd
data = pd.read_csv('20220104-212027-UTC_0-CAT3-IVER3-3089.log', header=0)
print(data.columns)

if 'Latitude' not in data.columns:
    print('no lat data')
    data = data.rename(columns={"Latitude (Deg N)": "Latitude", "Longitude (Deg W)": "Longitude"})
else:
    data = pd.read_csv(data, header=0, delimiter=';')  # IVERlog

data = data.astype({'Time': 'str', 'Latitude': 'float', 'Longitude': 'float'})
data['tme'] = data['Time'].map(lambda x: ''.join(x.split(':')))
# lat = daa['Latitude']
# lng = daa['Longitude']
# tme = daa['Time']
print(data.columns)
print(data.head(5))

