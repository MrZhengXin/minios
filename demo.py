import seaborn
import pandas as pd
import matplotlib.pyplot as plt

f, (ax1, ax2) = plt.subplots(figsize=(6, 10), nrows=2)

physical = [0, 0, 0.1, 1, 0.2, 0.4 ,0.1]
virtual = [0, 0, 0.05, 1, 0.1, 0.3 ,0.05]

ax1.plot(physical)
ax1.plot(virtual)
ax1.legend(['physical', 'virtual'])

data = {
    'page #0': [-1, 1, 1, 2, 2, 1, 2, 1, 1, 0],
    'page #1': [-1, 1, 2, 0, 1, 3, 2, 0, 1, 0],
    'page #2': [-1, 0, 2, -1, 0, 4, 4, 4, 1, 0]
}

data = pd.DataFrame(data)

data = pd.DataFrame(data.values.T, index=data.columns, columns=data.index)

seaborn.heatmap(data=data, cbar=None, ax=ax2, annot=True,
                linewidths=0.5, robust=True)

plt.tight_layout()
plt.show()