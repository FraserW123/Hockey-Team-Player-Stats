Welcome to the Hockey Stats Page. Here's how to compile and run the web server

<a name="installation"></a>
## 1. Installation

Download the project, unzip the project, access the folder in a terminal and install the following library
```bash
pip install virtualenv
```
Create a virtual environment
```bash
python -m venv env
```
Activate the environment (Windows CMD)
```bash
env\Scripts\activate.bat
```

Windows Powershell
```bash
env\Scripts\Activate.ps1
```

Unix
```bash
env/bin/activate
```
Install required libraries
```bash
pip install -r requirements.txt
```
Finally, run the following command
```bash
python app.py

```
In the terminal you should see a link like this "http://127.0.0.1:5000" paste it into your browser
