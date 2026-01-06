# Python Chart Templates

## Table of Contents
- [Prerequisites](#prerequisites)
- [Bar Charts](#bar-charts)
- [Line Charts](#line-charts)
- [Pie Charts](#pie-charts)
- [Scatter Plots](#scatter-plots)
- [Heatmaps](#heatmaps)
- [Tables](#tables)
- [Gantt Chart (Plotly)](#gantt-chart-plotly)
- [Network Graph](#network-graph)
- [Box Plot](#box-plot)
- [Saving Best Practices](#saving-best-practices)
- [Color Palettes](#color-palettes)



Ready-to-use Python code templates for common data visualizations.

## Prerequisites

```bash
pip install matplotlib seaborn pandas plotly networkx
```

## Bar Charts

### Vertical Bar Chart
```python
import matplotlib.pyplot as plt

categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]

plt.figure(figsize=(10, 6))
bars = plt.bar(categories, values, color='steelblue', edgecolor='navy')

# Add value labels on bars
for bar, val in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
             str(val), ha='center', va='bottom', fontsize=10)

plt.title('Category Comparison', fontsize=14, fontweight='bold')
plt.xlabel('Category')
plt.ylabel('Value')
plt.tight_layout()
plt.savefig('bar_chart.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Horizontal Bar Chart
```python
import matplotlib.pyplot as plt

categories = ['Slack Intelligence', 'AWS Infra', 'Notion Meeting', 'GitHub Work']
values = [450, 820, 380, 290]
colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']

plt.figure(figsize=(10, 6))
bars = plt.barh(categories, values, color=colors)

for bar, val in zip(bars, values):
    plt.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
             f'{val}ms', va='center', fontsize=10)

plt.xlabel('Execution Time (ms)')
plt.title('Skill Execution Times', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('horizontal_bar.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Grouped Bar Chart
```python
import matplotlib.pyplot as plt
import numpy as np

categories = ['Q1', 'Q2', 'Q3', 'Q4']
series1 = [20, 35, 30, 35]
series2 = [25, 32, 34, 20]

x = np.arange(len(categories))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, series1, width, label='2023', color='steelblue')
bars2 = ax.bar(x + width/2, series2, width, label='2024', color='coral')

ax.set_xlabel('Quarter')
ax.set_ylabel('Value')
ax.set_title('Year over Year Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()

plt.tight_layout()
plt.savefig('grouped_bar.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Line Charts

### Simple Line Chart
```python
import matplotlib.pyplot as plt

x = [1, 2, 3, 4, 5, 6, 7]
y = [10, 15, 13, 18, 20, 17, 25]

plt.figure(figsize=(10, 6))
plt.plot(x, y, marker='o', linewidth=2, markersize=8, color='steelblue')

plt.title('Trend Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Day')
plt.ylabel('Value')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('line_chart.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Multi-Line Chart
```python
import matplotlib.pyplot as plt

x = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
y1 = [100, 120, 115, 140, 160, 155]
y2 = [80, 95, 110, 105, 130, 145]
y3 = [60, 70, 85, 90, 100, 120]

plt.figure(figsize=(10, 6))
plt.plot(x, y1, marker='o', label='Service A', linewidth=2)
plt.plot(x, y2, marker='s', label='Service B', linewidth=2)
plt.plot(x, y3, marker='^', label='Service C', linewidth=2)

plt.title('Service Performance Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Month')
plt.ylabel('Requests (K)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('multi_line.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Pie Charts

### Simple Pie Chart
```python
import matplotlib.pyplot as plt

labels = ['Mermaid', 'Python', 'Gemini', 'Other']
sizes = [45, 30, 20, 5]
colors = ['#4CAF50', '#2196F3', '#FF9800', '#9E9E9E']
explode = (0.05, 0, 0, 0)  # Explode first slice

plt.figure(figsize=(8, 8))
plt.pie(sizes, explode=explode, labels=labels, colors=colors,
        autopct='%1.1f%%', shadow=True, startangle=90)
plt.title('Visualization Tool Usage', fontsize=14, fontweight='bold')
plt.axis('equal')
plt.tight_layout()
plt.savefig('pie_chart.png', dpi=150, bbox_inches='tight')
plt.show()
```

### Donut Chart
```python
import matplotlib.pyplot as plt

labels = ['Layer 1', 'Layer 2', 'Layer 3']
sizes = [30, 15, 5]
colors = ['#66BB6A', '#42A5F5', '#AB47BC']

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
        pctdistance=0.85, startangle=90)

# Draw circle for donut
centre_circle = plt.Circle((0, 0), 0.60, fc='white')
plt.gca().add_artist(centre_circle)

plt.title('Skills by Layer', fontsize=14, fontweight='bold')
plt.axis('equal')
plt.tight_layout()
plt.savefig('donut_chart.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Scatter Plots

### Basic Scatter Plot
```python
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
x = np.random.rand(50) * 100
y = x + np.random.randn(50) * 15

plt.figure(figsize=(10, 6))
plt.scatter(x, y, c='steelblue', alpha=0.7, s=100, edgecolors='navy')

# Add trend line
z = np.polyfit(x, y, 1)
p = np.poly1d(z)
plt.plot(x, p(x), "r--", alpha=0.8, label='Trend')

plt.title('Correlation Plot', fontsize=14, fontweight='bold')
plt.xlabel('Variable X')
plt.ylabel('Variable Y')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('scatter_plot.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Heatmaps

### Correlation Heatmap
```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Create sample correlation data
data = np.random.rand(5, 5)
data = (data + data.T) / 2  # Make symmetric
np.fill_diagonal(data, 1)

labels = ['Metric A', 'Metric B', 'Metric C', 'Metric D', 'Metric E']
df = pd.DataFrame(data, index=labels, columns=labels)

plt.figure(figsize=(10, 8))
sns.heatmap(df, annot=True, cmap='RdYlBu_r', center=0,
            square=True, linewidths=0.5, fmt='.2f')
plt.title('Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Tables

### Styled Table
```python
import matplotlib.pyplot as plt
import pandas as pd

data = {
    'Skill': ['slack-intelligence', 'aws-infra', 'notion-meeting', 'github-work'],
    'Layer': [2, 2, 2, 2],
    'Coverage': ['70%', '80%', '80%', '75%'],
    'Status': ['Active', 'Active', 'Active', 'Beta']
}
df = pd.DataFrame(data)

fig, ax = plt.subplots(figsize=(10, 4))
ax.axis('tight')
ax.axis('off')

table = ax.table(
    cellText=df.values,
    colLabels=df.columns,
    cellLoc='center',
    loc='center',
    colColours=['#4CAF50']*4,
    colWidths=[0.3, 0.15, 0.2, 0.15]
)

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.5)

# Style header
for i in range(len(df.columns)):
    table[(0, i)].set_text_props(color='white', fontweight='bold')

plt.title('Layer 2 Skills Overview', fontsize=14, fontweight='bold', y=0.8)
plt.tight_layout()
plt.savefig('table.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Gantt Chart (Plotly)

```python
import plotly.express as px
import pandas as pd

df = pd.DataFrame([
    dict(Task="Research", Start='2024-01-01', Finish='2024-01-15', Resource="Phase 1"),
    dict(Task="Design", Start='2024-01-10', Finish='2024-01-25', Resource="Phase 1"),
    dict(Task="Implementation", Start='2024-01-20', Finish='2024-02-15', Resource="Phase 2"),
    dict(Task="Testing", Start='2024-02-10', Finish='2024-02-28', Resource="Phase 2"),
    dict(Task="Deployment", Start='2024-02-25', Finish='2024-03-05', Resource="Phase 3"),
])

fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Resource",
                  title="Project Timeline")
fig.update_yaxes(autorange="reversed")
fig.write_image("gantt_chart.png", scale=2)
fig.show()
```

## Network Graph

```python
import networkx as nx
import matplotlib.pyplot as plt

# Create graph
G = nx.DiGraph()

# Add nodes with layers
G.add_node("daily-planner", layer=3)
G.add_node("slack-intel", layer=2)
G.add_node("aws-infra", layer=2)
G.add_node("slack-fetch", layer=1)
G.add_node("slack-analyze", layer=1)
G.add_node("task-create", layer=1)

# Add edges
G.add_edges_from([
    ("daily-planner", "slack-intel"),
    ("daily-planner", "aws-infra"),
    ("slack-intel", "slack-fetch"),
    ("slack-intel", "slack-analyze"),
    ("slack-intel", "task-create"),
])

# Position nodes by layer
pos = nx.multipartite_layout(G, subset_key="layer")

# Color by layer
colors = {'daily-planner': '#AB47BC', 'slack-intel': '#42A5F5',
          'aws-infra': '#42A5F5', 'slack-fetch': '#66BB6A',
          'slack-analyze': '#66BB6A', 'task-create': '#66BB6A'}
node_colors = [colors[node] for node in G.nodes()]

plt.figure(figsize=(12, 8))
nx.draw(G, pos, with_labels=True, node_color=node_colors,
        node_size=3000, font_size=10, font_weight='bold',
        arrows=True, arrowsize=20, edge_color='gray')

plt.title('Skill Call Graph', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('network_graph.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Box Plot

```python
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
data = [np.random.normal(100, 10, 100),
        np.random.normal(90, 20, 100),
        np.random.normal(85, 15, 100),
        np.random.normal(95, 12, 100)]

labels = ['Skill A', 'Skill B', 'Skill C', 'Skill D']

fig, ax = plt.subplots(figsize=(10, 6))
bp = ax.boxplot(data, labels=labels, patch_artist=True)

colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.set_title('Execution Time Distribution', fontsize=14, fontweight='bold')
ax.set_ylabel('Time (ms)')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('box_plot.png', dpi=150, bbox_inches='tight')
plt.show()
```

## Saving Best Practices

```python
# High-quality PNG
plt.savefig('output.png', dpi=300, bbox_inches='tight', facecolor='white')

# SVG for web (scalable)
plt.savefig('output.svg', bbox_inches='tight', facecolor='white')

# PDF for print
plt.savefig('output.pdf', bbox_inches='tight', facecolor='white')

# Transparent background
plt.savefig('output.png', dpi=300, bbox_inches='tight', transparent=True)
```

## Color Palettes

```python
# Material Design colors
COLORS = {
    'red': '#F44336',
    'pink': '#E91E63',
    'purple': '#9C27B0',
    'deep_purple': '#673AB7',
    'indigo': '#3F51B5',
    'blue': '#2196F3',
    'light_blue': '#03A9F4',
    'cyan': '#00BCD4',
    'teal': '#009688',
    'green': '#4CAF50',
    'light_green': '#8BC34A',
    'lime': '#CDDC39',
    'yellow': '#FFEB3B',
    'amber': '#FFC107',
    'orange': '#FF9800',
    'deep_orange': '#FF5722',
    'brown': '#795548',
    'grey': '#9E9E9E',
    'blue_grey': '#607D8B',
}

# Layer colors (for architecture diagrams)
LAYER_COLORS = {
    'L0': '#78909C',  # Blue Grey - External APIs
    'L1': '#66BB6A',  # Green - Atomic skills
    'L2': '#42A5F5',  # Blue - Composite skills
    'L3': '#AB47BC',  # Purple - Meta orchestrators
}
```
