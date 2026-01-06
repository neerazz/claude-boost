# Example: Data Chart

## Table of Contents
- [Request](#request)
- [Classification](#classification)
- [Generated Python](#generated-python)
- [Execution](#execution)
- [Output](#output)
- [Variations](#variations)



## Request

"Create a bar chart showing skill execution times across Layer 2 skills"

## Classification

| Pattern Found | Route |
|---------------|-------|
| "bar chart" | PYTHON |
| "execution times" (data) | PYTHON |

**Decision: PYTHON** (code-based, deterministic)

## Generated Python

```python
import matplotlib.pyplot as plt
import numpy as np

# Data
skills = [
    'slack-intelligence',
    'aws-infrastructure',
    'notion-meeting',
    'github-work',
    'holistic-life-tracker'
]
execution_times = [450, 820, 380, 290, 520]
coverage_scores = [85, 92, 78, 88, 75]

# Color based on coverage threshold (80%)
colors = ['#4CAF50' if score >= 80 else '#FF9800' for score in coverage_scores]

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Create bars
bars = ax.barh(skills, execution_times, color=colors, edgecolor='white', height=0.6)

# Add value labels
for bar, time, coverage in zip(bars, execution_times, coverage_scores):
    ax.text(bar.get_width() + 15, bar.get_y() + bar.get_height()/2,
            f'{time}ms', va='center', fontsize=11, fontweight='bold')
    ax.text(bar.get_width() - 50, bar.get_y() + bar.get_height()/2,
            f'{coverage}%', va='center', fontsize=10, color='white')

# Styling
ax.set_xlabel('Execution Time (ms)', fontsize=12)
ax.set_title('Layer 2 Skill Performance', fontsize=14, fontweight='bold', pad=20)
ax.set_xlim(0, max(execution_times) + 100)

# Add threshold line
ax.axvline(x=500, color='#F44336', linestyle='--', linewidth=2, alpha=0.7, label='SLA Threshold')

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#4CAF50', label='Coverage >= 80%'),
    Patch(facecolor='#FF9800', label='Coverage < 80%'),
    plt.Line2D([0], [0], color='#F44336', linestyle='--', label='SLA (500ms)')
]
ax.legend(handles=legend_elements, loc='lower right')

# Grid
ax.grid(True, axis='x', alpha=0.3)
ax.set_axisbelow(True)

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('skill_performance.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
```

## Execution

```bash
python3 generate_chart.py
```

## Output

![Skill Performance Chart](skill_performance.png)

```json
{
  "visualization_type": "PYTHON",
  "output": {
    "file_path": "skill_performance.png",
    "format": "png",
    "dimensions": {"width": 1800, "height": 1050}
  },
  "quality_metrics": {
    "route_confidence": 0.95,
    "tool_used": "matplotlib",
    "generation_method": "code",
    "deterministic": true,
    "execution_time_ms": 245,
    "data_points": 5
  },
  "code_generated": "...(full script above)...",
  "reasoning": "Request contains 'bar chart' and 'execution times' - routed to Python matplotlib"
}
```

## Variations

### Stacked Bar Chart

```python
import matplotlib.pyplot as plt
import numpy as np

skills = ['slack', 'aws', 'notion', 'github']
fetch_time = [120, 280, 95, 80]
analyze_time = [180, 320, 150, 120]
execute_time = [150, 220, 135, 90]

x = np.arange(len(skills))
width = 0.6

fig, ax = plt.subplots(figsize=(10, 6))

ax.bar(x, fetch_time, width, label='Fetch', color='#66BB6A')
ax.bar(x, analyze_time, width, bottom=fetch_time, label='Analyze', color='#42A5F5')
ax.bar(x, execute_time, width, bottom=np.array(fetch_time)+np.array(analyze_time),
       label='Execute', color='#AB47BC')

ax.set_ylabel('Time (ms)')
ax.set_title('Skill Phase Breakdown')
ax.set_xticks(x)
ax.set_xticklabels(skills)
ax.legend()

plt.tight_layout()
plt.savefig('stacked_bar.png', dpi=150)
```

### Comparison Chart

```python
import matplotlib.pyplot as plt
import numpy as np

skills = ['Slack', 'AWS', 'Notion', 'GitHub']
q1 = [420, 780, 350, 260]
q2 = [450, 820, 380, 290]

x = np.arange(len(skills))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width/2, q1, width, label='Q1', color='#90CAF9')
bars2 = ax.bar(x + width/2, q2, width, label='Q2', color='#1976D2')

ax.set_ylabel('Execution Time (ms)')
ax.set_title('Quarterly Performance Comparison')
ax.set_xticks(x)
ax.set_xticklabels(skills)
ax.legend()

# Add value labels
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('comparison_chart.png', dpi=150)
```
