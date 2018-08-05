# IMPORTS
import os
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import sqlite3
from sqlite3 import Error

# GLOBAL VARIABLES
## Site URL
url = "https://www.raleighnc.gov/parks/content/PRecDesignDevelop/Articles/GreenwayRepairs.html"

## Database
cwd = os.getcwd()
db = "{}/gw_closures.db".format(cwd)

## Get time of run
run_time = datetime.now()
run_id = int(run_time.strftime("%Y%m%d%H%M%S"))

# HELPER FUNCTIONS

## Get the HTML for the Greenway closure page
def retrieve_gw_closure_html(url):
    r = requests.get(url)
    return BeautifulSoup(r.text, features='html5lib')

## Create connection to database
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None

## Create new row in database table
def create_row(connection, sql, project):
    cursor =  connection.cursor()
    cursor.execute(sql, project)

# MAIN FUNCTION BODY
def main():
    # Retrieve the full site
    print("Retrieving HTML from the greenway closures page...")
    try:
        full_site = retrieve_gw_closure_html(url)
    except Exception as e:
        print(e)
    finally:
        print("Success!")

    # Gather all the divs with section class
    closures = full_site.find_all("div", {"class": "section"})

    # Create a connection to the database
    connection = create_connection(db)

    # Add rows to closure table
    print("Adding rows to table \'closure\'")
    for closure in closures:
        website_id = closure.find_all('h3')[0].get('id')
        name = closure.find_all("h3")[0].text.replace("\n", "")
        description = closure.select(".collapse")[0].text.replace("\n", "")

        with connection:
            try:
                closure_sql = ''' INSERT INTO closure(run_id,website_id,name,description)
                                  VALUES(?,?,?,?) '''
                closure_project = (run_id, website_id, name, description)
                create_row(connection, closure_sql, closure_project)
            except Exception as e:
                print(e)
    print("Success!")

    print("Adding rows to table \'closure_links\'")
    # Add rows to links table
    for closure in closures:
        closure_info_list = []

        website_id = closure.find_all('h3')[0].get('id')
        name = closure.find_all("h3")[0].text.replace("\n", "")
        description = closure.select(".collapse")[0].text.replace("\n", "")
        closure_links = closure.find_all("a")
        for link in closure_links:
            href = link.get("href")
            if href[0:4] != "http":
                if href[0] == "/":
                    href = href[1:]
                closure_link = "https://www.raleighnc.gov/{}".format(href)
            else:
                closure_link = href

            with connection:
                try:
                    closure_links_sql = ''' INSERT INTO closure_links(run_id,website_id,url)
                              VALUES(?,?,?) '''
                    closure_links_project = (run_id, website_id, closure_link)
                    create_row(connection, closure_links_sql, closure_links_project)
                except Error as e:
                    print(e)
    print("Success!")

    print("Adding rows to table \'closure_update\'")
    # Add row for run info
    ## Parse updated date header
    updated_date = full_site.find_all("div", {"class": "updatedDate"})[0].text
    replacements = (("Last updated ", ""), (".", ""), (",", ""), ("- ", ""))
    updated_date_clean = updated_date

    for r in replacements:
        updated_date_clean = updated_date_clean.replace(*r)
    updated_date_list = updated_date_clean.split()
    updated_date_datetime = datetime.strptime(updated_date_clean, "%b %d %Y %I:%M %p")
    updated_date_timestamp = updated_date_datetime.timestamp()

    ## Add row
    with connection:
        try:
            closure_update_sql = ''' INSERT INTO closure_update(run_id,updated)
                                     VALUES(?,?) '''
            closure_update_project = (run_id,int(updated_date_timestamp))
            create_row(connection, closure_update_sql, closure_update_project)
        except Error as e:
            print(e)
    print("Success!")

# MAIN FUNCTION CALL
if __name__ == '__main__':
    main()
