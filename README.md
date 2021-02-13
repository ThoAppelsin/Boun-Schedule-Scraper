This is a tool to scrape off the data from the Boğaziçi University registrar office's tables for the course schedules.

**Users beware #1:** Going by their [`robots.txt`](https://registration.boun.edu.tr/robots.txt) and the Google CAPTCHA on the [semester selection page](https://registration.boun.edu.tr/BUIS/General/schedule.aspx?p=semester), they apparently do not approve of this practice.

**Users beware #2:** This tool may provide inaccurate information or fail to operate altogether with changes in how the registrar office decides to represent the schedule data.

# Quick Start

## Setup
1) *[Optional, but recommended]* Create a virtual environment for Python:
2) Install the required packages listed under the [requirements.txt](https://github.com/ThoAppelsin/Boun-Schedule-Scraper/blob/master/requirements.txt):

You can do those in PowerShell with the following commands:
```powershell
# Creates a virtual environment folder called 'env'
python -m venv env

# Activates the virtual environment
./env/Scripts/activate

# Installs the requirements
pip install -r requirements.txt
```

They should be similar for macOS and Linux.

## Running

There are two modes of running the tool.  Either way, make sure that your virtual environment is active before continuing.

### Interactive mode

Run the following command and the script will guide you through.

```powershell
python regscrape.py
```

When it finishes, the output will be written into `output.json` or `output.csv`, depending on your choices.

### Tool mode

The tool mode is automatically enabled when the required arguments are passed directly via the command-line as in the following example:

```powershell
python regscrape.py 2017 1 2019 3 csv
```

This example will scrape off the schedule data for all the semesters between the Fall (1) semester of 2017/2018 and the Summer (3) semester of 2019/2020, and then print the results in the CSV format directly to the standart output.


