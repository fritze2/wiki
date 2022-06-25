from datetime import date
from urllib.parse import unquote
import logging
import os
import requests
import sys
import traceback


# Constants
RUNTIME_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
)
os.chdir(RUNTIME_DIR)
DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)
LOG_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "tmp",
)
WIKI_PAGES_LIST_FILE = os.path.join(DATA_DIR, "download-wiki-pages.txt")
LOG_FILE = os.path.join(LOG_DIR, "download-wiki.log")
TODAYS_DATE = date.today()


# Logging
if (not os.path.exists(LOG_DIR)):
    os.makedirs(LOG_DIR)
file_handler = logging.FileHandler(filename=LOG_FILE)
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)


# Globals
failed_lines_attempted=[]


def main():
    while True:
        # Open file in read mode to process a line.
        # If wiki page fails to download, then add line to `failed_lines_attempted`.
        file = open(WIKI_PAGES_LIST_FILE, 'r')
        remaining_lines = process_one_line_from(file)
        file.close()

        # Open file in write mode to update remaining lines.
        file = open(WIKI_PAGES_LIST_FILE, 'w')
        file.write("".join(remaining_lines))
        file.close()

        # Exit once all remaining lines match failed lines attempted.
        if failed_lines_attempted is remaining_lines:
            break


def parse_page_and_pdf_from(line):
    line = line.rstrip()
    prefix, last_name, dir, years_page, years, page = '', '', '', '', '', ''

    # Text after last forward slash is the wiki page.
    last_slash = line.rfind('/')
    if (last_slash<0):
        raise Exception(WIKI_PAGES_LIST_FILE + ' contains line with no slash in it')
    
    # Get dir and wiki page from line split by last forward slash.
    dir = line[0:last_slash]
    years_page = line[last_slash+1:]
    split_years_page = years_page.split(' ')
    
    if (len(split_years_page) == 1): # No space means only page given.
        page = split_years_page[0]

    elif (len(split_years_page) == 2): # Space means page and years (or prefix) given.
        # Split the text into a prefix and page.
        # If the prefix matches the "years" format "yyyy-[yyyy]", then
        # set years variable so the page is treated as a person's wiki page.
        prefix = split_years_page[0]
        if ("-" in prefix):
            years = prefix
        if (prefix != ''):
            prefix = prefix + ' '
        page = split_years_page[1]
    
    else: # Too many spaces or no page given.
        raise Exception(WIKI_PAGES_LIST_FILE + ' contains line ' + str(i+1) + ' with invalid syntax for page: must be in the format \"DIR/[YEARS] PAGE\"')
    
    if (years == ''): # Not a person.
        pdf = dir + '/' + str(TODAYS_DATE.year) + " Wikipedia " + prefix + unquote(page) + '.pdf'
    
    else: # Is a person.
        # A person's wiki page.
        split_page = page.split('_')
        last_name = page
        if (len(split_page)>1):
            # Text after last _ is the person's last name.
            last_name = split_page[len(split_page)-1]
        pdf = dir + '/' + years + ' ' + last_name + '.pdf'
    
    # Logging all variables to diagnose troubles.
    logging.debug('dir='+dir)
    logging.debug('years_page='+years_page)
    logging.debug('len(split_years_page)='+str(len(split_years_page)))
    logging.debug('page='+page)
    logging.debug('prefix='+prefix)
    logging.debug('years='+years)
    logging.debug('page='+page)
    logging.debug('last_name='+last_name)
    logging.debug('pdf='+pdf)

    return page, pdf


def download_pdf(line):
    # Example input lines:
    # Science/1620 Physics/1643-1727 Isaac_Newton
    # Science/1620 Physics/General/1. Physics
    try:
        # Determine what Wikipedia page to download and the filepath to write to.
        page, pdf = parse_page_and_pdf_from(line)

        # Makedirs if path doesn't exist.
        dir = line[0:pdf.rfind('/')]
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(pdf, 'wb') as f:
            url = 'https://en.wikipedia.org/api/rest_v1/page/pdf/' + page
            logging.debug('Downloading ' + url)
            response = requests.get(url)
            logging.info('Downloaded ' + url)

            logging.debug('Write to \"' + pdf + '\"')
            f.write(response.content)

            pdf_size = os.path.getsize(pdf)
            logging.debug('pdf_size='+str(pdf_size))
            if (pdf_size==0): # Empty file.
                return False

            if response.status_code == 200: # Successful.
                return True

            else: # Returned an error code.
                logging.error(response)
    except Exception as e:
        st = traceback.format_stack()
        logging.error(e)
        logging.error(st)
        return False
    # Response is not 200 status code or Exception.
    return False


def process_one_line_from(file):
    # Lines read from the file.
    lines = file.readlines()

    # Begin remaining lines at all failed lines attempted.
    remaining_lines = failed_lines_attempted.copy()

    for i, line in enumerate(lines):
        # Skip over failed lines that have already been attempted.
        if line in failed_lines_attempted:
            continue
        
        success = download_pdf(line)
        logging.debug('success=' + str(success))

        if not success:
            failed_lines_attempted.append(line)
            remaining_lines.append(line)
        
        # If we aren't at the end of the file,
        if (i<len(lines)-1):
            # Add remaining lines in the file.
            remaining_lines.extend(lines[i+1:])
        
        return remaining_lines


if __name__ == "__main__":
    main()
