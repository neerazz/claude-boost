# Self-Learn Memory Storage

> **Purpose**: Single source of truth for all self-learning session data and trends.

## Directory Structure

```
memory/self-learn/
├── README.md              # This file
├── ratings-history/       # Historical skill ratings by date
│   └── {YYYY-MM-DD}.json  # Daily ratings snapshot
├── improvements-archive/  # Proposed improvements archive
│   └── {YYYY-MM-DD}.json  # Daily improvement proposals
├── duplicates/            # Detected duplicate skills
│   └── {YYYY-MM-DD}.json  # Daily duplicate detection
└── cumulative-stats.json  # Aggregated trends over time
```

## Schema: Ratings History

```json
{
  "date": "2025-01-05",
  "skills": {
    "skill-name": {
      "rating": 85,
      "change": "+5",
      "notes": "Improved error handling"
    }
  }
}
```

## Usage

The `self-improvement-loop` skill reads/writes to this directory to track learning over time.
