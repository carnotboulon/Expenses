#!/usr/local/bin/python
# coding: latin-1
import shutil, datetime, os.path, time

DB_PATH = r"/home/pi/Github/Expenses/db.sqlite3"
ARCHIVE_FOLDER = r"/home/pi/Desktop/ExpenseDB-Archive"
ARCHIVE_NAMING = "Expenses-DATE.sqlite3"
MAX_NUMBER_OF_ARCHIVES = 10
DATE_FORMAT = "%d%b%Y"

### Save the current DB
currentDate = datetime.datetime.strftime(datetime.datetime.now(),DATE_FORMAT)
archive_name = ARCHIVE_NAMING.replace("DATE",currentDate)
shutil.copy(DB_PATH, os.path.join(ARCHIVE_FOLDER, archive_name))                # copy2 copies file and its metadata.

### Remove the oldest one if needed.
db_list = []
# Get all the sqlite3 files.
for f in os.listdir(ARCHIVE_FOLDER):
    if f.split(".")[-1] == "sqlite3":
        db_list.append(os.path.join(ARCHIVE_FOLDER,f))

        
# Remove the oldest one if too many files.        
if len(db_list) > MAX_NUMBER_OF_ARCHIVES:
    db_list = sorted(db_list, key = os.path.getmtime)
    os.remove(db_list[0])
