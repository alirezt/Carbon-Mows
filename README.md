# Carbon Footprint of Municipal Organic Waste Systems (Carbon-MOWS) Dashboard

The Carbon-MOWS Dashboard is a work-in-progress dashboard, developed in Python and Shiny, to demonstrate and analyze different type of data. 

The dashboard is divided into different tabs, depending on the type of data to analyze. Currently, there are two active tabs on the dashboard:

1. LCA
2. Food Waste

The following guide will explain how to install and run the application locally, how to change some of the data files, and how to modify/add tabs.

## Installation

There are many Python libraries that must be installed. The user has the choice of using either pip or conda package manager. However, Conda **must** be used if the app is to be installed on an Apple Silicon hardware. If you are on Windows, you must also ensure that the Microsoft C++ Build Tools are installed.

1. Clone the repository:

    ```bash
    git clone https://github.com/alirezt/Carbon-Mows
    ```

2. Navigate to the dashboard directory:

    ```bash
    cd pythonshinyproject/dashboard/
    ```

3. Install the required libraries:

    If using PIP:

    ```bash
    pip install -r piprequirements.txt
    ```