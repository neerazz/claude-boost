
# User Guide: Getting Started with Claude Boost

Welcome to **Claude Boost**! If you're new to AI agents, Claude, or coding, this guide will help you understand what this project is and how to use it to boost your professional profile.

## What is Claude Boost?

Claude Boost is a framework designed to make AI agents (like Claude) work in a **deterministic** and **reliable** way. 

Think of a standard AI as a very smart but sometimes unpredictable assistant. Claude Boost gives that assistant a **structured playbook** (called "Skills") and a **quality control system** (called "Hooks" and "Gates"). This ensures that every time you ask the AI to do something, it follows a high-quality process and produces consistent results.

## Core Concepts

### 1. Skills
A "Skill" is a specific task the AI has been trained to do perfectly. For example, "Analyze a resume" or "Write a LinkedIn post." Each skill has a clear set of rules it must follow.

### 2. Gates
Before and after every task, the AI passes through a "Gate." 
- **Clear Thinking Gate**: Makes sure the AI understands exactly what you want before it starts.
- **Self-Critique Gate**: Makes sure the AI checks its own work for errors before showing it to you.

### 3. MCP (Model Context Protocol)
MCP is like a "connector" that allows the AI to talk to other apps you use, such as **Slack**, **GitHub**, **Google Calendar**, and **Notion**. This allows the AI to gather real information from your work life to help you better.

## How to Use This Project

### 1. Set Up Your Environment
Make sure you have the necessary tools installed. See the [Quick Start Guide](QUICKSTART.md) for details.

### 2. Run a Pre-flight Check
Before doing anything, run the pre-flight check to make sure everything is ready:
```bash
python3 tools/preflight_gate.py
```

### 3. Ask the AI to Perform a Skill
You can invoke skills by name. For example, if you want to identify gaps in your current profile:
```
/skill gap-analyzer
```

### 4. Review the Results
The AI will follow its internal protocol, perform research, and provide you with a high-quality report. It will also show you its "Self-Critique" so you know how much to trust the output.

## Boosting Your Profile

This project is specifically designed to help you build evidence for career advancement (like the EB1A visa). You can use it to:
- **Discover Award Opportunities**: Find prestigious awards in your field.
- **Identify Speaking Engagements**: Find conferences where you can share your expertise.
- **Analyze Your Projects**: Quantify the impact of your work for your resume.
- **Create Thought Leadership Content**: Generate high-quality articles for LinkedIn or Medium.

## Next Steps

- Explore the different skills in the `skills/` directory.
- Read the [Architecture Overview](ARCHITECTURE.md) to see how the system works under the hood.
- Start using the skills to gather evidence for your professional portfolio!
