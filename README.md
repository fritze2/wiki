I want to view Wikipedia's vital articles as PDFs in an organized local filesystem.

1. First, I want to download each page in the Vital Articles (Level 5).
2. Then I want to put each page into a location I've configured a text file.
3. Each line in this text file contains: the page to be downloaded, the location to put it, and any prefix information. (ordered list numbers, date of birth/death, etc.)
4. Process lines in the text file one-by-one. Leave any lines that failed to process in the file. Log debug information into a file for diagnosis of errors.