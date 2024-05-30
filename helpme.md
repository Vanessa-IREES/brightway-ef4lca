# Project Setup and Installation Guide

This guide provides a step-by-step process for setting up and running a Python/Jupyter project on windows.

## Prerequisites

You may not need to install all the tools listed below, depending on your existing setup.

## Windows

### 1. Install Python

1. Download Python from [python.org](https://www.python.org/downloads/windows/).
2. During installation, select "Customize installation" and choose the following options:
   - Install for all users
   - Add Python to environment variables

### 2. Install Conda

1. Download and install Miniconda from [Anaconda's documentation](https://docs.anaconda.com/free/miniconda/).
2. Add Conda to the system PATH:
   - Search for "Environment Variables" in the Windows taskbar and edit the system PATH variable.
   - Add the path & script path of your installation, eg.: `C:\ProgramData\miniconda3\Scripts` and `C:\ProgramData\miniconda3`
3. Set the execution policy in PowerShell (run as Administrator):
   ```powershell
   Set-ExecutionPolicy RemoteSigned
   ```

### 3. Install Visual Studio Code (VS Code)

1. Download and install VS Code from [code.visualstudio.com](https://code.visualstudio.com/download).

### 4. Install Git for Windows

1. Download and install Git from [gitforwindows.org](https://gitforwindows.org/).
2. Follow the default installation settings.

##  Linux

The installation process for Linux (at least fedora) is straight forward:
Instead of downloading installers, use your distros package manager to install the above mentioned packages (if contained, otherwise include 3rd party repos or just google it, all packages should be availiable for most distros in one way or another...).
Git: Git is typically pre-installed on most Linux distributions. If not, you can easily install it via your package manager. The Git Credential Manager however might not be included. Instead use eg. SSH keys for authentication, which is straightforward and secure. Refer to GitHub's guide for setting up SSH keys.

## Project Setup

### 1. Clone the Project Repository

1. Open a terminal.
2. Clone the repository:
   ```bash
   git clone https://github.com/m0e161/brightway-ef4lca.gi
   ```
3. For **Windows**: Follow the prompts to log in to your GitHub account if required (Git Credential Manager will assist with this). For **linux** use ssh adress if you have setup ssh keys.


### 2. Open the Project in VS Code

1. Open VS Code.
2. Navigate to `File > Open Folder` and select the cloned project folder.

### 3. Install VS Code Extensions

1. Open the command palette (Ctrl+Shift+P).
2. Search for and install the following extensions:
   - Python
   - Jupyter
3. You may also install additional extensions as needed (VS Code will often suggest these).

### 4. Create a Python Environment

1. Open the command palette (Ctrl+Shift+P).
2. Search for "Create Environment" and follow the prompts.

### 5. Install Project Dependencies

1. In the terminal, navigate to the project folder.
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

### 6. Run the Jupyter Notebook

1. Open the Jupyter notebook file in VS Code.
2. If prompted to install additional dependencies (like IPython kernel), follow the recommendations provided by VS Code.
3. Select the appropriate environment and run the notebook.
