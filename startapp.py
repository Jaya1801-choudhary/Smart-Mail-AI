import subprocess

# 'r' makes it a raw string so backslashes don't break things
# We remove the '.\' and just point to the path
command = r"venv\Scripts\activate.bat && streamlit run app.py"

subprocess.run(command, shell=True)