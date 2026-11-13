# SchoolPlanner

### Plan your days, weeks, even your month!

## About the Project

SchoolPlanner is a smart Canvas schedule task planner. It implements AI features that analyzes your homework assignments along with their estimated completion times to generate an optimal study and work schedule. It prioritizes tasks based on importance, estimated work time, and proximity to due dates so you can focus on the most important tasks.

## Getting Started & Installation

Before doing anything else, clone the GitHub repository to your computer.

### 1. Open Your Terminal or Command Prompt

* **Windows:** Press the **Windows Key**, type `cmd`, and open **Command Prompt**.
* **macOS:** Press **Command + Space** to open Spotlight, type `Terminal`, and press **Enter**.

### 2. Navigate to the Project Directory

Locate the `SchoolPlanner` folder on your computer and run the command corresponding to your operating system:

* **Windows (Command Prompt):**
  ```cmd
  cd C:\Users\"your name"\Downloads\SchoolPlanner
  ```
* **macOS (Terminal):**
  ```bash
  cd ~/Downloads/SchoolPlanner
  ```
  
You can also type `cd` with a space and drag the SchoolPlanner folder directly into the terminal/CMD window.

### 3. Install Required Dependencies

In the same terminal window, run the installation command:

* **Windows:**
  ```cmd
  pip install -r requirements.txt
  ```
* **macOS:**
  ```bash
  pip3 install -r requirements.txt
  ```

## Running the Program

Once the installation is complete, launch the application from the same terminal window:

* **Windows:**
  ```cmd
  python main.py
  ```
* **macOS:**
  ```bash
  python3 main.py
  ```

You are now ready to use SchoolPlanner!

## Implemented Features

* Download the link of Canvas Calendar
* Download and clean the homeworks
* Filter the homeworks for the next 7 days
* Estimate hours with key words
* Priotize the nearest assignments
* Generate a calendar by blocks
* Export to .ics for your preferred calendar tools (Google Calendar, Apple Calendar, Outlook)
* Locally saves data between for future usage of the application.

## Impact of this project

Canvas only shows final deadlines for assignments, which leads to procrastination, stress, dread, and burnout. This affects especially students who struggle with time management or have ADHD.

SchoolPlanner solves this by building a customized schedule tailored to your free time and priority preferences. Our goal is to reduce student stress, build better habits, and boost academic performance across many students.

## Demo Video

[Check out the project demonstration](https://drive.google.com/file/d/1Zyqx58Io2WkDO-PwYeMSOpKwedRa0rbh/view?usp=sharing)
