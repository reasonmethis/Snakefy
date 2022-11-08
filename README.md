# Snakefy

Utility to convert camelCase variables in your Python project to snake_case.

### Disclaimer

It has been successfully tested on a number of projects (with hundreds to thousands of lines of code), but it's not guaranteed that it's bug-free and 
won't make incorrect changes. 

## Features

It won't just modify files right away, it prompts the user to confirm important steps. Main features:

* Leaves untouched variables like ClassName or MYCONSTANT (that start with a capital)
* Warns if converting a particular variable name would create a name collision 
* Before modifying a file, shows a preview of proposed changes, lets the user edit them
* Allows to exclude specific file names and variable names
* Makes backups of files before modifying them
* Allows to configure where to look for *.py files (default - the folder where the Snakefy folder sits)

## Usage

The simplest way to use it is to put the Snakefy folder into the folder with your *.py files. Then run

```
python main.py
```

