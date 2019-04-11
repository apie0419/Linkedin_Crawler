import re, time, traceback, helpers, logging, json
from lxml.html import fromstring, tostring
from urllib3 import util
from w3lib.url import url_query_cleaner
from constants import PYTHON_DATETIME_FORMAT

# PARSE DIRECTORY PAGEs
def parseDirectory(url, rawHtml, country_code):
    type = getUrlType(url)
    if type == 1:
        return parseDirectoryType1(rawHtml, country_code)
    elif type == 2:
        return parseDirectoryType2(rawHtml, country_code)
    return None

def parseDirectoryType1(rawHtml, country_code):
    t = fromstring(rawHtml)
    result = {'profile_url':[], 'directory_url':[]}
    linkList = t.xpath('//div[contains(@class,"section") and contains(@class,"last")]/div/ul/li[contains(@class,"content")]/a')
    if linkList is not None and len(linkList) > 0:
        for link in linkList:
            temp = link.xpath('@href')
            if temp is not None and len(temp) > 0:
                url = temp[0]
                if helpers.check_if_correct_domain(country_code, url):
                    t = getUrlType(url)
                    isShortUrl = helpers.check_if_short_url(url)
                    if t == 3:
                        if isShortUrl:
                            url = 'https://' +country_code+ '.linkedin.com'+url
                        result['profile_url'].append((url, None))
                    elif t == 1 or t == 2:
                        if isShortUrl:
                            url = 'http://' +country_code+ '.linkedin.com'+url
                        result['directory_url'].append(url)
    return result

def parseDirectoryType2(rawHtml, country_code):
    t = fromstring(rawHtml)
    result = {'profile_url':[], 'directory_url':[]}
    profileList = t.xpath('//ul[@class="content"]/li/div[@class="profile-card"]')
    if profileList is not None and len(profileList) > 0:
        for profile in profileList:
            link = profile.xpath("div[@class='content']/h3/a/@href")
            metaHeaderDiv = profile.xpath("div[@class='content']/dl[@class='basic']/dt")
            metaDataDiv = profile.xpath("div[@class='content']/dl[@class='basic']/dd")

            if link is not None and len(link) > 0:
                url = link[0]
                if helpers.check_if_correct_domain(country_code, url):
                    t = getUrlType(url)
                    isShortUrl = helpers.check_if_short_url(url)
                    if t == 3:
                        metaData = None
                        if metaHeaderDiv is not None and len(metaHeaderDiv) > 0 and metaDataDiv is not None and len(metaDataDiv) > 0:
                            metaData = dict()
                            for hDiv, dDiv in zip(metaHeaderDiv, metaDataDiv):
                                field = hDiv.text_content().strip().lower()
                                data = dDiv.text_content().strip()
                                metaData[field] = data
                        if isShortUrl:
                            url = 'https://' +country_code+ '.linkedin.com'+url
                        result['profile_url'].append((url, metaData))
                    elif t == 1 or t == 2:
                        if isShortUrl:
                            url = 'http://' +country_code+ '.linkedin.com'+url
                        result['directory_url'].append(url)
    return result

def getUrlType(url):
    if re.match(".+/people-[a-z]", url):
        return 1
    elif re.match(".+/people-[0-9]", url):
        return 1
    elif "/pub/dir/" in url:
        return 2
    elif "/search/" in url:
        return 2
    elif "/pub/" in url:
        return 3
    elif "/in/" in url:
        return 3
    return None

def _cleanUrl(url):
    try:
        index = url.index('?')
        return url[:index]
    except ValueError:
        return url

def parseProfile(rawHtml, logger_name):
    t = fromstring(rawHtml)
    profile = dict()

    logger = logging.getLogger(logger_name)
    try:
        ## TopCard
        # PROFILE PICTURE
        profilePictureSrc = t.xpath('//div[@class="pv-profile-sticky-header__mini-profile-container EntityLockup-circle-3-ghost-person"]/figure/img/@src')
        if profilePictureSrc is not None and len(profilePictureSrc) > 0:
            profile['profile_picture'] = profilePictureSrc[0]

        # NAME
        nameDiv = t.xpath('//div[@class="display-flex align-items-center"]/h1')
        if nameDiv is not None and len(nameDiv) > 0:
            profile['fullname'] = nameDiv[0].text_content().strip()

        # TITLE
        titleDiv = t.xpath("//div[@class='pv-top-card-v2-section__info mr5']/h2")
        if titleDiv is not None and len(titleDiv) > 0:
            profile['title'] = titleDiv[0].text_content().split(" at ")[0].strip()

        # CONNECTIONS
        connections = t.xpath("//span[@class='pv-top-card-v2-section__entity-name pv-top-card-v2-section__connections ml2 Sans-15px-black-85%']")
        if connections is not None and len(connections) > 0:
            profile['connections'] = connections[0].text_content().strip().split(' ')[0].strip()
            try:
                if profile['connections'][-1] == '+':
                    profile['connections_number'] = int(profile['connections'][:-1])
                elif profile['connections'][0] == '>':
                    profile['connections_number'] = int(profile['connections'][1:].strip())
                else:
                    profile['connections_number'] = int(profile['connections'])
            except ValueError:
                pass

        ## SUMMARY
        summaryDiv = t.xpath("//p[@class='pv-top-card-section__summary-text mt4 ember-view']")
        if summaryDiv is not None and len(summaryDiv) > 0:
            profile['summary'] = summaryDiv[0].text_content().strip()
        else:
            summaryDiv = t.xpath("//p[@class='pv-top-card-section__summary-text text-align-left mt4 ember-view']")
            if summaryDiv is not None and len(summaryDiv) > 0:
                profile['summary'] = summaryDiv[0].text_content().replace('...', '').strip()

        ## SKILLS
        skillsDiv = t.xpath("//section[@class='pv-profile-section pv-skill-categories-section artdeco-container-card ember-view']//li")
        skillList = list()
        if skillsDiv is not None and len(skillsDiv) >0:
            for sDiv in skillsDiv:
                skill = dict()
                nameDiv = sDiv.xpath(".//span[@class='Sans-17px-black-100%-semibold']")
                if nameDiv is not None and len(nameDiv) > 0:
                    skill['name'] = nameDiv[0].text_content().strip()
                    countDiv = sDiv[0].xpath(".//span[@class='pv-skill-category-entity__endorsement-count Sans-15px-black-70%']")
                    if countDiv is not None and len(countDiv) > 0:
                        skill['endorsement_count'] = countDiv[0].text_content().strip()
                    skillList.append(skill)
                else:
                    nameDiv = sDiv.xpath(".//p[@class='pv-skill-category-entity__name Sans-17px-black-100%-semibold']")
                    if nameDiv is not None and len(nameDiv) > 0:
                        skill['name'] = nameDiv[0].text_content().strip()
                        skill['endorsement_count'] = '0'
                        skillList.append(skill)
            profile['skills'] = skillList

        ## EXPERIENCE
        experienceDiv = t.xpath("//section[@class='pv-profile-section experience-section ember-view']/ul/li")
        if experienceDiv is not None and len(experienceDiv) > 0:
            expList = list()
            for experience in experienceDiv:
                je = dict()
                # title
                titleDiv = experience.xpath(".//h3[@class='Sans-17px-black-85%-semibold']")
                if titleDiv is not None and len(titleDiv) > 0:
                    je['title'] = titleDiv[0].text_content().strip()
                # organisation
                orgLinkDiv = experience.xpath(".//a[@class='ember-view']")
                org = dict()
                if orgLinkDiv is not None and len(orgLinkDiv) > 0:
                    orgLink = orgLinkDiv[0].get("href")
                    org['url'] = "https://www.linkedin.com" + orgLink
                    org['id_string'] = helpers.get_company_linkedin_id(org['url'])
                    org['name'] = orgLinkDiv[0].xpath(".//span[@class='pv-entity__secondary-title']")[0].text_content().strip()
                logoDiv = experience.xpath(".//div[@class='pv-entity__logo company-logo']/img")
                if logoDiv is not None and len(logoDiv) > 0:
                    # org['imgUrl'] = logoDiv[0].xpath("@src")
                    org['imgUrl'] = logoDiv[0].get("src")
                je['organisation'] = org
                # location
                locationDiv = experience.xpath(".//h4[@class='pv-entity__location Sans-15px-black-70% block']/span")
                if locationDiv is not None and len(locationDiv) > 0:
                    je['location'] = locationDiv[1].text_content().strip()
                # time
                timeDiv = experience.xpath(".//h4[@class='pv-entity__date-range inline-block Sans-15px-black-70%']/span")
                if timeDiv and len(timeDiv) > 0:
                    je['start'] = timeDiv[1].text_content().split("–")[0].strip()
                    if len(timeDiv) > 1:
                        je['end'] = timeDiv[1].text_content().split("–")[1].strip()
                # desc
                descDiv = experience.xpath(".//p[@class='pv-entity__description Sans-15px-black-70% mt4']")
                if descDiv is not None and len(descDiv) > 0:
                    je['desc'] = descDiv[0].text_content().replace('     ', '').strip()
                expList.append(je)
            profile['experience'] = expList

        ## EDUCATION
        educationDiv = t.xpath("//section[@class='pv-profile-section education-section ember-view']/ul/li")
        if educationDiv is not None and len(educationDiv) > 0:
            eduList = list()
            for education in educationDiv:
                edu = dict()
                # school name
                nameDiv = education.xpath(".//h3[@class='pv-entity__school-name Sans-17px-black-85%-semibold']")
                if nameDiv is not None and len(nameDiv) > 0:
                    nameDiv = nameDiv[0]
                    edu['name'] = nameDiv.text_content().strip()
                    schoolLink = education.xpath(".//a[@class='ember-view']")
                    if schoolLink is not None and len(schoolLink) > 0:
                        schoolLink = schoolLink[0]
                        edu['url'] = schoolLink.xpath("@href")[0]
                        edu['id_string'] = helpers.get_school_linkedin_id(edu['url'])
                # degree
                degreeDiv = education.xpath(".//span[@class='pv-entity__comma-item']")
                if degreeDiv is not None and len(degreeDiv) > 0:
                    degreeInfo = degreeDiv[0].text_content().strip()
                    if len(degreeInfo) > 0:
                        edu['degree'] = degreeInfo
                # time
                timeDiv = education.xpath(".//p[@class='pv-entity__dates Sans-15px-black-70%']/span/time")
                if timeDiv and len(timeDiv) > 0:
                    edu['start'] = timeDiv[0].text_content().strip()
                    if len(timeDiv) > 1:
                        edu['end'] = timeDiv[1].text_content().strip()
                # desc
                descDiv = education.xpath(".//p[@class='pv-entity__secondary-title Sans-15px-black-70%']/span")
                if descDiv is not None and len(descDiv) > 0:
                    for desc in descDiv:
                        textContent = desc.text_content()
                        edu['activities'] = textContent.strip()
                eduList.append(edu)
            profile['education'] = eduList

        ## PROJECT
        projectSection = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block projects pv-accomplishments-block--expanded ember-view']")
        if projectSection is not None and len(projectSection) > 0: # Means expanded
            projectDiv = projectSection[0].xpath(".//div[@class='pv-accomplishments-block__list-container']/ul/li")
            if projectDiv is not None and len(projectDiv) > 0:
                projectList = list()
                for project in projectDiv:
                    p = dict()
                    # project title
                    titleDiv = project.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                    if titleDiv is not None and len(titleDiv) > 0:
                        titleDiv = titleDiv[0]
                        p['title'] = titleDiv.text_content().split('Project name')[1].strip()
                    # time
                    timeDiv = project.xpath(".//p[@class='pv-accomplishment-entity__date pv-accomplishment-entity__subtitle']")
                    if timeDiv and len(timeDiv) > 0:
                        p['date'] = dict()
                        timeList = timeDiv[0].text_content().split('–')
                        p['date']['start'] = timeList[0].strip()
                        p['date']['end'] = timeList[1].strip()
                    # members
                    memberDiv = project.xpath(".//div[@class='facepile facepile-row xsmall ember-view']")
                    if memberDiv is not None and len(memberDiv) > 0:
                        p['team_members'] = list()
                        for members in memberDiv:
                            members = members.xpath(".//img")
                            if members is not None and len(members) > 0:
                                for m in members:
                                    member = dict()
                                    member['name'] = m.xpath("@alt")[0].strip()
                                    if member['name'] is not None and len( member['name']) > 0:
                                        p['team_members'].append(member)
                    # description
                    descDiv = project
                    if descDiv is not None and len(descDiv) > 0 and len(descDiv.text_content().split("Project description")) > 1:
                        p['description'] = descDiv.text_content().split("Project description")[1].strip()
                    projectList.append(p)
                profile['project'] = projectList
        else: # Means it is not expanded
            projectSection = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block projects ember-view']")
            if projectSection is not None and len(projectSection) > 0:
                projectDiv = projectSection[0].xpath(".//div[@class='pv-accomplishments-block__list-container']/ul/li")
                projectList = list()
                if projectDiv is not None and len(projectDiv) > 0:
                    for project in projectDiv:
                        p = dict()
                        textContent = project.text_content().strip()
                        p['title'] = textContent
                        projectList.append(p)
                    profile['project'] = projectList
                

        ## COURSES
        courseDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block courses pv-accomplishments-block--expanded ember-view']//ul[@class='pv-accomplishments-block__list ']/li")
        courseList = list()
        if courseDiv is not None and len(courseDiv) > 0:
            for course in courseDiv:
                entry = dict()
                # course name
                listDiv = course.xpath("h4[@class='pv-accomplishment-entity__title']")
                if listDiv is not None and len(listDiv) > 0:
                    entry['courses'] = listDiv[0].text_content().split("Course name")[1].strip()
                # course number
                listDiv = course.xpath("p[@class='pv-accomplishment-entity__course-number pv-accomplishment-entity__subtitle']")
                if listDiv is not None and len(listDiv) > 0:
                    entry['number'] = listDiv[0].text_content().split("Course number")[1].strip()
            profile['course_list'] = courseList
        else:
            courseDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block courses ember-view']//ul[@class='pv-accomplishments-block__summary-list Sans-15px-black-70% ']/li")
            if courseDiv is not None and len(courseDiv) > 0:
                for schoolEntry in courseDiv:
                    textContent = schoolEntry.text_content().strip()
                    courseList.append(textContent)
                profile['course_list'] = courseList

        ## LANGUAGES
        languagesDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block languages pv-accomplishments-block--expanded ember-view']//li")
        languages = list()
        if languagesDiv is not None and len(languagesDiv) > 0:
            for lDiv in languagesDiv:
                language = dict()
                # name
                nameDiv = lDiv.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                if nameDiv is not None and len(nameDiv) > 0:
                    language['language'] = nameDiv[0].text_content().split("Language name")[1].strip()
                # proficiency
                proficiencyDiv = lDiv.xpath(".//p[@class='pv-accomplishment-entity__proficiency pv-accomplishment-entity__subtitle']")
                if proficiencyDiv is not None and len(proficiencyDiv) > 0:
                    language['proficiency'] = proficiencyDiv[0].text_content().strip()
                languages.append(language)
            profile['language'] = languages
        else:
            languagesDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block languages ember-view']//ul[@class='pv-accomplishments-block__summary-list Sans-15px-black-70% ']/li")
            if languagesDiv is not None and len(languagesDiv) > 0:
                for lDiv in languagesDiv:
                    textContent = lDiv.text_content().strip()
                    languages.append(textContent)
                profile['language'] = languages
            
        ## ORGANIZATION
        organizationDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block organizations pv-accomplishments-block--expanded ember-view']//li")
        organizations = list()
        if organizationDiv is not None and len(organizationDiv) > 0:
            for oDiv in organizationDiv:
                organization = dict()
                # organization
                nameDiv = oDiv.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                if nameDiv is not None and len(nameDiv) > 0:
                    organization['name'] = nameDiv[0].text_content().split("organization name")[1].strip()
                # # title
                # titleDiv = oDiv.xpath("header/h5[@class='item-subtitle']")
                # if titleDiv is not None and len(titleDiv) > 0:
                #     organization['title'] = titleDiv[0].text_content().strip()
                # time
                timeDiv = oDiv.xpath(".//span[@class='pv-accomplishment-entity__date']")
                if timeDiv is not None and len(timeDiv) > 0:
                    organization['time'] = dict()
                    timeStringList = timeDiv[0].text_content().split("organization date")[1].split("–")
                    organization['time']['start'] = timeStringList[0].strip()
                    organization['time']['end'] = timeStringList[1].strip()
                # # description
                # descDiv = oDiv.xpath("p[@class='description']")
                # if descDiv is not None and len(descDiv) > 0:
                #     organization['description'] = descDiv[0].text_content()
                organizations.append(organization)
            profile['organization'] = organizations
        else:
            organizationDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block organizations ember-view']//li")
            if organizationDiv is not None and len(organizationDiv) > 0:
                for oDiv in organizationDiv:
                    textContent = oDiv.text_content().strip()
                    organizations.append(textContent)
                    profile['organization'] = organizations
                profile['organization'] = organizations

        ## INTERESTS
        interestsDiv = t.xpath("//section[@class='pv-profile-section pv-interests-section artdeco-container-card ember-view']/ul/li")
        if interestsDiv is not None and len(interestsDiv) > 0:
            interests = list()
            for iDiv in interestsDiv:
                interest = dict()
                # name
                nameDiv = iDiv.xpath(".//span[@class='pv-entity__summary-title-text']")
                interest['name'] = nameDiv[0].text_content().strip()
                # url
                linkDiv = iDiv.xpath(".//a[@class='pv-interest-entity-link block full-width ember-view']/@href")
                if linkDiv is not None and len(linkDiv) > 0:
                    if linkDiv[0].find("www.linkedin.com") == -1:
                        interest['url'] = "https://www.linkedin.com" + linkDiv[0]
                    else:
                        interest['url'] = linkDiv[0]
                interests.append(interest)
            profile['interest'] = interests

        ## PUBLICATIONS

        publicationsDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block publications pv-accomplishments-block--expanded ember-view']//li")
        publications = list()
        if publicationsDiv is not None and len(publicationsDiv) > 0:
            for pDiv in publicationsDiv:
                publication = dict()
                # title
                titleDiv = pDiv.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                if titleDiv is not None and len(titleDiv) > 0:
                    titleDiv = titleDiv[0]
                    publication['title'] = titleDiv.text_content().split("publication title")[1].strip()
                    linkDiv = pDiv.xpath(".//a[@class='pv-accomplishment-entity__external-source']//@href")
                    if linkDiv is not None and len(linkDiv) > 0:
                        publication['url'] = linkDiv[0]
                # publisher
                publisherDiv = pDiv.xpath(".//span[@class='pv-accomplishment-entity__publisher']")
                if publisherDiv is not None and len(publisherDiv) > 0:
                    publication['publisher'] = publisherDiv[0].text_content().split("publication description")[1].strip()
                # date
                dateDiv = pDiv.xpath(".//span[@class='pv-accomplishment-entity__date']")
                if dateDiv is not None and len(dateDiv) > 0:
                    publication['date'] = dateDiv[0].text_content().split("publication date")[1].strip()
                # description
                descDiv = pDiv.xpath(".//p[@class='pv-accomplishment-entity__description Sans-15px-black-70%']")
                if descDiv is not None and len(descDiv) > 0:
                    publicationDesc = '\n'.join([x.text_content() for x in descDiv])
                    publication['description'] = publicationDesc.split("publication description")[1].strip()
                publications.append(publication)
            profile['publication'] = publications
        else:
            publicationsDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block publications ember-view']")
            if publicationsDiv is not None and len(publicationsDiv) > 0:
                publicationsDiv = publicationsDiv[0].xpath(".//ul[@class='pv-accomplishments-block__summary-list Sans-15px-black-70% ']/li")
                for pDiv in publicationsDiv:
                    publication = pDiv.text_content().strip()
                    publications.append(publication)
                profile['publication'] = publications

        ## HONORS
        honorDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block honors pv-accomplishments-block--expanded ember-view']//li")
        honors = list() 
        if honorDiv is not None and len(honorDiv) > 0:
            honorDiv = honorDiv[0].xpath(".//ul[@class='pv-accomplishments-block__summary-list Sans-15px-black-70% ']/li")
            for hDiv in honorDiv:
                honor = dict()
                # title
                titleDiv = hDiv.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                if titleDiv is not None and len(titleDiv) > 0:
                    honor['title'] = titleDiv[0].text_content().split('honor title')[1].strip()

                # organisation
                organisationDiv = hDiv.xpath(".//span[@class='pv-accomplishment-entity__issuer']")
                if organisationDiv is not None and len(organisationDiv) > 0:
                    honor['organisation'] = organisationDiv[0].text_content().split('honor issuer')[1].strip()
                # time
                timeDiv = hDiv.xpath(".//span[@class='pv-accomplishment-entity__date']")
                if timeDiv is not None and len(timeDiv) > 0:
                    honor['time'] = timeDiv[0].text_content().split('honor date')[1].strip()
                # description
                descDiv = hDiv.xpath(".//p[@class='pv-accomplishment-entity__description Sans-15px-black-70%']")
                if descDiv is not None and len(descDiv) > 0:
                    honor['description'] = descDiv[0].text_content().split('honor description')[1].strip()
                honors.append(honor)
            profile['honor'] = honors
        else:
            honorDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block honors ember-view']//li")
            for hDiv in honorDiv:
                honor = dict()
                # title
                if titleDiv is not None and len(titleDiv) > 0:
                    honor['title'] = hDiv.text_content().strip()
                honors.append(honor)
            profile['honor'] = honors

        ## VOLUNTEERING
        volunteeringDiv = t.xpath("//section[@class='pv-profile-section volunteering-section ember-view']//ul[@class='pv-profile-section__section-info section-info pv-profile-section__section-info--has-no-more']")
        volunteering = dict()
        if volunteeringDiv is not None and len(volunteeringDiv) > 0:
            volunteeringExp = list  ()
            for vDiv in volunteeringDiv:
                exp = dict()
                # role
                roleDiv = vDiv.xpath(".//h3[@class='Sans-17px-black-85%-semibold']")
                if roleDiv is not None and len(roleDiv) > 0:
                    exp['role'] = roleDiv[0].text_content().strip()
                # organisation
                orgDiv = vDiv.xpath(".//span[@class='pv-entity__secondary-title']")
                if orgDiv is not None and len(orgDiv) > 0:
                    exp['organization'] = orgDiv[0].text_content().strip()
                # time
                timeDiv = vDiv.xpath(".//h4[@class='pv-entity__date-range detail-facet inline-block Sans-15px-black-70%']/span")
                if timeDiv is not None and len(timeDiv) > 0:
                    exp['time'] = dict()
                    exp['time']['start'] = timeDiv[1].text_content().split('–')[0].strip()
                    if len(timeDiv) > 1:
                        exp['time']['end'] = timeDiv[1].text_content().split('–')[1].strip()
                # cause
                causeDiv = vDiv.xpath(".//h4[@class='pv-entity__cause Sans-15px-black-70%']/span[@class='ember-view']")
                if causeDiv is not None and len(causeDiv) > 0:
                    exp['cause'] = causeDiv[0].text_content().strip()
                # description
                descDiv = vDiv.xpath(".//p[@class='pv-entity__description Sans-15px-black-70% mt4']")
                if descDiv is not None and len(descDiv) > 0:
                    exp['description'] = descDiv[0].text_content().strip()
                volunteeringExp.append(exp)
            volunteering['experience'] = volunteeringExp

        ## CERTIFICATIONS
        certDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block certifications pv-accomplishments-block--expanded ember-view']//li")
        certifications = list()
        if certDiv is not None and len(certDiv) > 0:
            for cDiv in certDiv:
                cert = dict()
                # logo
                logoDiv = cDiv.xpath(".//a[@class='pv-accomplishment-entity__photo mt3 ember-view']")
                if logoDiv is not None and len(logoDiv) > 0:
                    cert['logo_url'] = logoDiv[0].xpath('@href')[0]
                # title
                titleDiv = cDiv.xpath(".//h4[@class='pv-accomplishment-entity__title']")
                if titleDiv is not None and len(titleDiv) > 0:
                    titleDiv = titleDiv[0]
                    cert['title'] = titleDiv.text_content().split('Title')[1].strip()
                # license no
                licenseDiv = cDiv.xpath(".//span[@class='pv-accomplishment-entity__license']")
                if licenseDiv is not None and len(licenseDiv) > 0:
                    cert['license_no'] = licenseDiv[0].text_content().split("License")[1].strip()
                # time
                timeDiv = cDiv.xpath(".//span[@class='pv-accomplishment-entity__date']")
                if timeDiv is not None and len(timeDiv) > 0:
                    cert['time'] = dict()
                    timeStringList = timeDiv[0].text_content().split("Certification Date")[1].split("–")
                    cert['time']['start'] = timeStringList[0].strip()
                    cert['time']['end'] = timeStringList[1].strip()
                # organisation
                orgDiv = cDiv.xpath(".//a[@class='pv-accomplishment-entity__photo mt3 ember-view']")
                if orgDiv is not None and len(orgDiv) > 0:
                    cert['organisation'] = dict()
                    cert['organisation']['organisation_name'] = orgDiv[0].xpath(".//p[@class='Sans-15px-black-55% ml2']")[0].text_content().split("Certification authority")[1].strip()
                    cert['organisation']['organisation_url'] = orgDiv[0].xpath("@href")[0]
                    cert['organisation']['organisation_id_string'] = helpers.get_company_linkedin_id(cert['organisation']['organisation_url'])
                # details
                detailDiv = cDiv.xpath(".//a[@class='pv-accomplishment-entity__external-source']")
                if detailDiv is not None and len(detailDiv) > 0:
                    cert['detail_url'] = detailDiv[0].xpath("@href")[0]
                certifications.append(cert)
            profile['certification'] = certifications
        else:
            certDiv = t.xpath("//section[@class='accordion-panel pv-profile-section pv-accomplishments-block certifications ember-view']//ul[@class='pv-accomplishments-block__summary-list Sans-15px-black-70% ']/li")
            if certDiv is not None and len(certDiv) > 0:
                for cDiv in certDiv:
                    cert = dict()
                    # title
                    cert['title'] = cDiv.text_content().strip()
                    certifications.append(cert)
                profile['certification'] = certifications
        
        ## People Also Viewed
        alsoViewDiv = t.xpath("//section[@class='pv-profile-section pv-browsemap-section profile-section artdeco-container-card ember-view']//li")
        if alsoViewDiv is not None and len(alsoViewDiv) > 0:
            alsoViews = list()
            for avDiv in alsoViewDiv:
                alsoView = dict()
                # name
                nameDiv = avDiv.xpath(".//a[@class='pv-browsemap-section__member ember-view']")
                if nameDiv is not None and len(nameDiv) > 0:
                    alsoView['name'] = nameDiv[0].xpath(".//span[@class='name actor-name']")[0].text_content().strip()
                    tmpUrl = nameDiv[0].xpath("@href")[0]
                    if tmpUrl is not None:
                        alsoView['url'] = tmpUrl
                        alsoView['linkedin_id'] = helpers.get_linkedin_id(alsoView['url'])
                # photo
                photoDiv = avDiv.xpath(".//img[@class='lazy-image pv-browsemap-section__member-image EntityPhoto-circle-4 loaded']")
                if photoDiv is not None and len(photoDiv) > 0:
                    alsoView['img_url'] = photoDiv[0].xpath("@src")[0]
                # headline
                headLineDiv = avDiv.xpath(".//p[@class='browsemap-headline Sans-15px-white-100%']")
                if headLineDiv is not None and len(headLineDiv) > 0:
                    alsoView['title'] = headLineDiv[0].text_content().split(" at ")[0].strip()
                    if len(headLineDiv[0].text_content().split(" at ")) == 2:
                        alsoView['company'] = headLineDiv[0].text_content().split(" at ")[1].strip()
                alsoViews.append(alsoView)
            profile['people_also_viewed'] = alsoViews
        
        ## Recommendations Received
        RecommDiv = t.xpath("//section[@class='pv-profile-section pv-recommendations-section artdeco-container-card ember-view']")
        if RecommDiv is not None and len(RecommDiv) > 0:
            RecommReceivedDiv = RecommDiv[0].xpath(".//artdeco-tabpanel[@class='active ember-view']//ul[@class='section-info']/li")
            # RecommReceivedDiv = RecommDiv[0].xpath(".//ul[@class='section-info']/li")
            recommendation = list()
            for rDiv in RecommReceivedDiv:
                rec = dict()
                detailDiv = rDiv.xpath(".//div[@class='pv-recommendation-entity__detail']")
                given_by = dict()
                #name
                nameDiv = detailDiv[0].xpath(".//h3[@class='Sans-17px-black-85%-semibold-dense']")
                if nameDiv is not None and len(nameDiv) > 0:
                    given_by['name'] = nameDiv[0].text_content().strip()
                #company
                comDiv = detailDiv[0].xpath(".//p[@class='pv-recommendation-entity__headline Sans-15px-black-85% pb1']")
                if comDiv is not None and len(comDiv) > 0:
                    given_by['company'] = comDiv[0].text_content().strip()
                #time and relationship
                bgdDiv = detailDiv[0].xpath(".//p[@class='Sans-13px-black-55%']")
                if bgdDiv is not None and len(bgdDiv) > 0:
                    given_by['time_and_relationship'] = bgdDiv[0].text_content().strip()
                rec['given_by'] = given_by
                #text
                textDiv = rDiv.xpath(".//div[@class='pv-recommendation-entity__highlights']")
                if textDiv is not None and len(textDiv) > 0:
                    rec['testimonial'] = textDiv[0].text_content().strip()
                recommendation.append(rec)
            profile["recommendation"] = recommendation

    except Exception:
        logger.error("Parser: error parsing user profile:\n{0}".format(traceback.format_exc()))
    
    profile['crawled_at'] = time.strftime(PYTHON_DATETIME_FORMAT)
    return profile

def parseDynamicCompanyProfile(rawHtml, logger_name):
    rawHtml = rawHtml.encode('ascii', 'ignore')
    t       = fromstring(rawHtml)
    compProfile  = dict()
    jsonCompData = None
    try:
        # dynamically generated comment
        commentDiv = t.xpath("//code[@id='stream-promo-top-bar-embed-id-content']//comment()")
        if commentDiv and len(commentDiv) > 0:
            try:
                jsonCompData = json.loads(get_HTML_comment_content(str(commentDiv[0])))
            except Exception:
                pass
        if jsonCompData is None:
           return None
        
        # company name
        nameDiv = jsonCompData.get('companyName')
        if nameDiv is not None:
            compProfile['name'] = nameDiv
        else:
            return None

        # company overview
        # name, industry, size
        industryDiv    = jsonCompData.get('industry')
        companySizeDiv = jsonCompData.get('size')
        overviewDiv    = nameDiv
        if industryDiv is not None:
           overviewDiv = overviewDiv + ' '+ industryDiv.strip()
        if companySizeDiv is not None:
           overviewDiv = overviewDiv + ' '+ companySizeDiv
        if len(overviewDiv) >0:
            compProfile['overview'] = overviewDiv.strip()

        # description
        descDiv = jsonCompData.get('description')
        if descDiv is not None:
            compProfile['description'] = descDiv.strip()

        # specialities
        specialitiesDiv = jsonCompData.get('specialties')
        if specialitiesDiv is not None and len(specialitiesDiv)>0:
            specialities = ', '.join(specialitiesDiv)
            if specialities is not None:
                compProfile['specialities'] = specialities.strip()
        
        # basic_info_about
        # industry, headquarters, founded, size, type, website
        headquartersDiv = jsonCompData.get('headquarters')
        foundedDiv      = jsonCompData.get('yearFounded')
        typeDiv         = jsonCompData.get('companyType')
        websiteDiv      = jsonCompData.get('website')
        if industryDiv is not None:
           compProfile['industry'] = industryDiv.strip()
        if headquartersDiv and len(headquartersDiv)>0:
            street1 = headquartersDiv.get('street1')
            street2 = headquartersDiv.get('street2')
            city    = headquartersDiv.get('city')
            state   = headquartersDiv.get('state')
            zipCode = headquartersDiv.get('zip')
            country = headquartersDiv.get('country')
            headquarters = ''
            if street1 is not None:
               headquarters = headquarters+' '+ street1
            if street2 is not None:
               headquarters = headquarters+' '+ street2    
            if city is not None:
               headquarters = headquarters+' '+ city
            if state is not None:
               headquarters = headquarters+' '+ state
            if zipCode is not None:
               headquarters = headquarters+' '+ zipCode    
            if country is not None:
               headquarters = headquarters+' '+ country            
            if len(headquarters.strip())>0:
               compProfile['headquarters'] = headquarters.strip()
        if foundedDiv is not None:
           compProfile['founded'] = str(foundedDiv).strip()
        if companySizeDiv is not None:
           compProfile['company_size'] = companySizeDiv
        if typeDiv is not None:
           compProfile['type'] = typeDiv.strip()
        if websiteDiv is not None:
           compProfile['website'] = websiteDiv.strip()
           
        # parent company
        parentDiv = jsonCompData.get('parent')
        if parentDiv is not None:
            parentComp = dict()
            parentNameDiv     = parentDiv.get('name')
            parentIndustryDiv = parentDiv.get('industry')
            parentSizeDiv     = parentDiv.get('size')
            bodyDiv           = ''
            if parentNameDiv is not None:
                bodyDiv = parentNameDiv.strip()
            if  parentIndustryDiv is not None:
                bodyDiv = bodyDiv + ' '+ parentIndustryDiv.strip()
            if parentSizeDiv is not None:
                bodyDiv = bodyDiv + ' '+ parentSizeDiv
            if len(bodyDiv.strip())>0:
                parentComp['overview'] = bodyDiv.strip()
            nameDiv = parentNameDiv.strip()
            if nameDiv is not None:
                parentComp['name'] = nameDiv.strip()
            link = parentDiv.get('homeUrl')
            if link is not None:
                parentComp['url'] = link.strip()
            imgLink = parentDiv.get('legacySquareLogo')
            if imgLink is not None:
                parentComp['img_url'] = 'https://media.licdn.com/mpr/mpr/shrink_100_100'+ imgLink.strip()
            compProfile['parent_company'] = parentComp

        # other brand pages
        otherPagesDiv = jsonCompData.get('relatedBrands')
        if otherPagesDiv and len(otherPagesDiv) > 0:
            compProfile['other_brand_pages'] = list()
            for pageDiv in otherPagesDiv:
                otherPage = dict()
                nameDiv = pageDiv.get('name')
                if nameDiv is not None:
                    otherPage['name'] = nameDiv.strip()
                link = pageDiv.get('homeUrl')
                if link is not None:
                    otherPage['url'] = link.strip()
                brandIndustryDiv  = pageDiv.get('industry')
                brandFollowersDiv = pageDiv.get('followerCount')
                overviewDiv       = ''
                if nameDiv is not None: 
                    overviewDiv = nameDiv.strip()
                if brandIndustryDiv is not None:
                    overviewDiv = overviewDiv + ' '+ brandIndustryDiv.strip()
                if brandFollowersDiv is not None:
                    overviewDiv = overviewDiv + ' '+ str(brandFollowersDiv)+' followers' 
                if len(overviewDiv.strip())>0:
                    otherPage['overview'] = overviewDiv.strip()
                imgLink = pageDiv.get('legacySquareLogo')
                if imgLink is not None:
                    otherPage['img_url'] = 'https://media.licdn.com/mpr/mpr/shrinknp_100_100'+imgLink.strip()
                compProfile['other_brand_pages'].append(otherPage)

    except Exception as e:
        logger = logging.getLogger(logger_name)
        logger.error("Parser: error parsing company profile:\n{0}".format(traceback.format_exc()))

    # timestamp
    compProfile['crawled_at'] = time.strftime(PYTHON_DATETIME_FORMAT)

    return compProfile

def parseSchoolProfile(rawHtml, logger_name):
    t = fromstring(rawHtml)
    schoolProfile = dict()

    try:
        comments = t.xpath("//div[contains(@class,'edu-wrapper')]/code/comment()")
        if comments and len(comments) > 0:
            header = None
            try:
                jsonData = json.loads(get_HTML_comment_content(comments[0].text_content()))
                schoolProfile['header_content'] = jsonData
                header = jsonData['content']['unifiedHeader']['detail']['header']
            except Exception:
                pass
            if header is not None:
                name = header.get('title')
                if name is not None:
                    schoolProfile['name'] = name
                location = header.get('subtitle')
                if location is not None:
                    schoolProfile['location'] = location
                coverPhoto = header.get('coverPhotoMediaId')
                if coverPhoto is not None:
                    schoolProfile['cover_photo'] = 'https://spdy.linkedin.com/mpr/mpr/shrinknp_674_240' + coverPhoto
                logo = header.get('pictureId')
                if logo is not None:
                    schoolProfile['logo'] = 'https://spdy.linkedin.com/mpr/mpr/shrink_200_200' + logo

        alumniCountDiv = t.xpath("//div[@id='about-school']//div[contains(@class,'alumni-career-outcomes')]/h3/a/text()")
        if alumniCountDiv and len(alumniCountDiv) > 0:
            alumniCountText = alumniCountDiv[0].strip()
            schoolProfile['alumni_count'] = get_number_of_alumni_from_text(alumniCountText)

        careerOutcomeDiv = t.xpath("//div[@id='about-school']//div[contains(@class,'alumni-career-outcomes')]/ul/li")
        if careerOutcomeDiv and len(careerOutcomeDiv) > 0:
            companies = careerOutcomeDiv[0].xpath("ul/li")
            if companies and len(companies) > 0:
                careerCompanies = list()
                for company in companies:
                    rec = dict()
                    name = company.xpath("@title")
                    count = company.xpath("@data-count")
                    if name and len(name) > 0:
                        rec['name'] = name[0].strip()
                    if count and len(count) > 0:
                        rec['count'] = int(count[0].strip())
                    careerCompanies.append(rec)
                schoolProfile['career_outcomes_companies'] = careerCompanies

        if careerOutcomeDiv and len(careerOutcomeDiv) > 1:
            industries = careerOutcomeDiv[1].xpath("ul/li")
            if industries and len(industries) > 0:
                careerIndustries = list()
                for industry in industries:
                    rec = dict()
                    name = industry.xpath("@title")
                    count = industry.xpath("@data-count")
                    if name and len(name) > 0:
                        rec['name'] = name[0].strip()
                    if count and len(count) > 0:
                        rec['count'] = int(count[0].strip())
                    careerIndustries.append(rec)
                schoolProfile['career_outcomes_industries'] = careerIndustries

        # description
        descriptionDiv = t.xpath("//div[@id='about-school']//div[contains(@class,'school-info-wrapper')]/dl/dd[contains(@class,'full-description')]")
        if descriptionDiv and len(descriptionDiv) > 0:
            schoolProfile['description'] = descriptionDiv[0].text_content().strip()

        # other info
        infoDivList = t.xpath("//div[@id='about-school']//div[contains(@class,'school-info-wrapper')]//dl[contains(@class,'meta-list')]")
        if infoDivList and len(infoDivList) > 0:
            infoList = list()
            for infoDiv in infoDivList:
                infoParts = infoDiv.xpath("*")
                lastKey = None
                lastData = None
                for elem in infoParts:
                    rawText = tostring(elem)

                    tag = find_element_tag(rawText)
                    if tag == 'dt':
                        if lastKey is not None and lastData is not None:
                            infoList.append({"name":lastKey,"value":lastData})
                        contentText = elem.text_content().strip()
                        lastKey = get_basic_info_field_name(contentText)
                        lastData = None
                    elif tag == 'dd':
                        contentText = elem.text_content().strip()
                        if lastData is None:
                            lastData = contentText
                        else:
                            lastData += '\n' + contentText
                if lastKey is not None and lastData is not None:
                    infoList.append({"name":lastKey,"value":lastData})
            schoolProfile['meta_info'] = infoList

    except Exception:
        logger = logging.getLogger(logger_name)
        logger.error("Parser: error parsing school profile:\n{0}".format(traceback.format_exc()))

    # timestamp
    schoolProfile['crawled_at'] = time.strftime(PYTHON_DATETIME_FORMAT)

    return schoolProfile

# HELPER FUNCTIONs
def remove_url_parameter(url):
    return url_query_cleaner(url)

def get_also_view_item(dirtyUrl):
    item = {}
    url = remove_url_parameter(dirtyUrl)
    item['url'] = url
    item['linkedin_id'] = helpers.get_linkedin_id(url)
    return item

def get_HTML_comment_content(comment):
    s = None
    e = None
    try:
        s = comment.index("<!--")
        e = comment.index("-->")
    except Exception:
        pass

    if s is not None and e is None:
        return comment[s+4:]
    elif s is None and e is not None:
        return comment[:e]
    elif s is not None and e is not None:
        return comment[s+4:e]
    else:
        return comment

def get_number_of_alumni_from_text(rawText):
    pAlumniCount = re.compile('([0-9,]+)')
    m = pAlumniCount.search(rawText)
    if m is not None:
        return int(m.group(1).replace(',',''))
    return 0

def get_int_value(rawText):
    pNum = re.compile('([0-9,]+)')
    m = pNum.search(rawText)
    if m is not None:
        return int(m.group(1).replace(',',''))
    return 0

def find_element_tag(textData):
    s = None
    e = None
    try:
        s = textData.index('<')
        e = textData.index('>')
    except Exception:
        pass

    if s is None or e is None or e <= (s+1):
        return None
    return textData[s+1:e]

def get_redirect_url(link):
    url_parse = util.parse_url(link).query
    query_parse = util.parse_url.parse_qs(url_parse)
    if 'url' in query_parse:
         return query_parse['url'][0]
    return None

def get_basic_info_field_name(rawText):
    return rawText.lower().replace(' ','_')