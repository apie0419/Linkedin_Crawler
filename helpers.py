import re

def check_if_short_url(url):
    return url[0] == '/'

def check_if_correct_domain(country_code,url):
    if check_if_short_url(url): # short URL
        return True
    domain = re.compile('^(https://|http://)?'+country_code+'.linkedin.com')
    m = domain.search(url)
    if m is not None:
        return True
    return False

# From URL to id
def get_linkedin_id(url):
    find_index = url.find("linkedin.com/in/")
    if find_index >= 0:
        return url[find_index + 13:].replace('/', '_')

    find_index = url.find("linkedin.com/")
    if find_index >= 0:
        return url[find_index + 17:].replace('/', '_')
    return None

def get_company_linkedin_id(url):
    template = "/company/"
    find_index = url.find(template)
    if find_index >= 0:
        start_index = find_index + len(template)
        end_index_1 = url.find('/', start_index)
        end_index_2 = url.find('?', start_index)
        tempList = list()
        if end_index_1 >= 0:
            tempList.append(end_index_1)
        if end_index_2 >= 0:
            tempList.append(end_index_2)
        if len(tempList) >0:
            end_index = min(tempList)
            return url[start_index:end_index]
        return url[start_index:]
    return None

def get_school_linkedin_id(url):
    template = "linkedin.com/edu/"
    find_index = url.find(template)
    if find_index >= 0:
        start_index = find_index + len(template)
        end_index_1 = url.find('/', start_index)
        end_index_2 = url.find('?', start_index)
        tempList = list()
        if end_index_1 >= 0:
            tempList.append()
        if end_index_2 >= 0:
            tempList.append()
        if len(tempList) >0:
            end_index = min(tempList)
            return url[start_index:end_index]
        return url[start_index:]
    return None

def get_HTTP_url(url, country_code):
    if url[:5] == 'https':
        return 'http' + url[5:]
    if url[0] == '/':
        return 'http://' +country_code+ '.linkedin.com' + url
    return url

def get_HTTPS_url(url, country_code):
    if url[:5] == 'http:':
        return 'https' + url[4:]
    if url[0] == '/':
        return 'https://' +country_code+ '.linkedin.com' + url
    return url

def areUrlsEqual(url1, url2):
    template = "linkedin.com/"
    find_index_1 = url1.find(template)
    find_index_2 = url2.find(template)
    main_part_1 = None
    main_part_2 = None
    if find_index_1 >= 0:
        start_index_1 = find_index_1 + len(template)
        main_part_1 = url1[start_index_1:]
    if find_index_2 >= 0:
        start_index_2 = find_index_2 + len(template)
        main_part_2 = url2[start_index_2:]
    return main_part_1 == main_part_2


pComp = re.compile('/company/(\d+)')
def parseCompanyIdFromUrl(url):
    global pComp
    m = pComp.search(url)
    if m is not None:
        return int(m.group(1))
    return None

pSchool = re.compile('id=(\d+)')
def parseSchoolIdFromUrl(url):
    global pSchool
    m = pSchool.search(url)
    if m is not None:
        return int(m.group(1))
    return None

pGroup = re.compile('gid=(\d+)')
def parseGroupIdFromUrl(url):
    global pGroup
    m = pGroup.search(url)
    if m is not None:
        return int(m.group(1))
    return None