import pandas as pd
import matplotlib.pyplot as plt

file = 'simulated-data.csv'
df = pd.read_csv(file, delimiter=',', header=0)
print(df.head(5))

print(f'lat:{len(df.lat)}')
df.drop_duplicates(subset='lat', keep='first', inplace=True)
print(f'lat:{len(df.lat)}')
# df_tosave = df.copy()
# df_tosave.to_csv('simulated-data.csv',index=False)

plt.plot(df.lng, df.lat)
plt.show()
