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

    If using Conda, you should install the different libraries found in the piprequirements.txt file individually. If the device is an Apple Silicon, it is **crucial** to install brightway_nosolver instead of brightway2. This is because the super-fast linear algebra software library pypardiso that brightway2 uses is not compatible with the M1 ARM architecture.

## Usage

Once everything is installed, the following command can be used to start the dashboard. When running the dashboard for the first time, it will take some time to initialize. It is important to run the command in the dashboard folder

```bash
shiny run app.py
```

## How to change some of the data files

All the important data files are located in the data folder, located in pythonshinyproject/dashboard. For instance, if there is a new updated database to upload, you would upload it in the data/brightway folder. **It is very important that, when uploading, the name of the updated database remains identical to the previous iteration.**

## How are the different tabs implemented

Each tab has it's own python file associated with it, located in the pythonshinyproject/dashboard/tabs folder. That is where a tab can be modified. To add a new tab, a new file must be created in the tabs folder, and the tab must be added in the app.py file, which handles overlying architecture of the shiny application. The init.py file, on the other hand, handles all the important preprocessing procedures that are completed when running the project for the first time