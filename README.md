# linkedin_crawler_2018
Crawls linkedin profiles via selenium from a seed profile_url list and expands the seed list by snowballing from the profiles shown in the 'Also View' section.
1. udpated_linkedin_crawler.py - contains the new code which can get more complete data by expanding profile fields such as certifications, publications etc.
2. extract_profile.py - converts a given html profile file path into a valid structured JSON file.

Dependecies on file paths
1. Change the chrome driver path 
2. Create an empty data directory and empty .txt files (crawled.txt and saved.txt) if they don't exit earlier.
