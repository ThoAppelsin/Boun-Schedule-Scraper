from pprint import pprint
from bs4 import BeautifulSoup
import requests
import re
import sys
from collections import OrderedDict
import traceback
from urllib.parse import quote_plus

def makesoup(address):
    raw = requests.get(address)
    raw.encoding = 'utf-8'
    html = raw.text
    soup = BeautifulSoup(html, features="html.parser")
    return soup

def getdeptcodesnames():
    ectssoup = makesoup("https://registration.boun.edu.tr/scripts/ectsdepsel.asp")

    deptlinks = ectssoup.select("a.menu2")
    # href attributes has values like: "/scripts/ects.asp?bolum=ASIA"
    return [ (dl['href'].split('=')[1], quote_plus(dl.get_text().strip())) for dl in deptlinks ]

def getcells(tr):
    return [td.text.strip() for td in tr("td")]

def cellids(days, hours):
    TOTAL_HOURS = 14

    return [TOTAL_HOURS * day + hour - 1 for day, hour in zip(days, hours)]

def parsedayshours(ncells):
    days = ['M', 'T', 'W', 'Th', 'F', 'S']
    daysmap = dict(zip(days, range(len(days))))

    ncells['days'] = [daysmap[day] for day in re.findall(r'M|Th?|W|F|S', ncells['days'])]
    possiblehours = [[]]
    for c in ncells['hours']:
        forks = []
        for hs in possiblehours:
            if len(hs) > 0 and hs[-1] == '1':
                fork = hs[:]
                fork[-1] += c
                forks.append(fork)
            hs.append(c)
        possiblehours.extend(forks)
    possiblehours = [list(map(int, hs)) for hs in possiblehours if len(hs) == len(ncells['days'])]

    if len(possiblehours) == 1:
        ncells['hours'] = possiblehours[0]
        ncells['cellIds'] = cellids(ncells['days'], ncells['hours'])
    else:
        ncells['hours'] = possiblehours
        ncells['cellIds'] = [cellids(ncells['days'], hours) for hours in ncells['hours']]

def scrapedept(deptaddress):
    raw = requests.get(deptaddress).text
    soup = BeautifulSoup(raw, features="html.parser")

    titlerow = soup.select(".schtitle")[0] # Hopefully there is just one
    titles = OrderedDict((t, t) for t in getcells(titlerow))
    titles['Hours'] = 'hours'
    titles['Days'] = 'days'
    titles['Rooms'] = 'rooms'
    titles['Name'] = 'fullName'
    titles['Code.Sec'] = 'name'
    titles['Cr.'] = 'credits'
    titles['Ects'] = 'ects'
    titles['Exam'] = 'exam'
    titles['Sl.'] = 'sl'
    titles['Departments'] = 'dep'
    titles['Required for Dept.(*)'] = 'req'
    titles['Instr.'] = 'parentName'
    titles['Course Delivery Method'] = 'place'
    titles['Final Exam Location'] = 'final'

    courses = []

    try:
        course = None
        for row in soup.select(".schtd, .schtd2"):
            namedcells = dict(zip(titles.values(), getcells(row)))
            parsedayshours(namedcells)
            if namedcells['name'] == "":
                course['extras'].append(namedcells)
            else:
                course = namedcells
                course['areaCode'], course['digitCode'], course['sectionCode'] = re.match(r'([A-Z]+)\s*([^.]+)\.(\d+)', course['name']).groups()
                course['extras'] = []
                courses.append(course)
    except Exception as err:
        traceback.print_exc()
        # print(err)
    finally:
        return courses

def main():
    if len(sys.argv) > 1:
        deptcourses = scrapedept(sys.argv[1])
        pprint(deptcourses)
    else:
        depts = []
        for deptcode, deptname in deptcodesnames.items():
            depts.append({'code': deptcode, 'courses': scrapedept(f"https://registration.boun.edu.tr/scripts/sch.asp?donem=2020/2021-1&kisaadi={deptcode}&bolum={deptname}")})
        pprint(depts)

def inputfromrange(prompt, minval, maxval):
    while True:
        x = input(prompt)
        try:
            x = int(x)
            if minval <= x <= maxval:
                return x
        except:
            pass
        print(f"Valid input range is [{minval}, {maxval}]. Please try again.")

def newmain():
    deptcodesnames = getdeptcodesnames()
    
    startyear = inputfromrange("Year to start from (enter 2010 for year 2010/2011): ", 2000, 2020)
    startsemester = inputfromrange("Semester to start from (enter 1/2/3 for Fall/Spring/Summer: ", 1, 3)

    endyear = inputfromrange("Year to finish at (enter 2010 for year 2010/2011): ", startyear, 2020)
    endsemester = inputfromrange("Semester to finish at (enter 1/2/3 for Fall/Spring/Summer: ", startsemester if startyear == endyear else 1, 3)

    data = {}
    year = startyear
    semester = startsemester

    print(len(deptcodesnames), "departments will be queried each semester")
    while year <= endyear:
        yeardata = data[year] = {}
        while semester <= 3 and (year < endyear or semester <= endsemester):
            semdata = yeardata[semester] = []
            for i, (deptcode, deptname) in enumerate(deptcodesnames):
                try:
                    deptcourses = scrapedept(f"https://registration.boun.edu.tr/scripts/sch.asp?donem={year}/{year+1}-{semester}&kisaadi={deptcode}&bolum={deptname}")
                    semdata.append({'deptcode': deptcode, 'deptname': deptname,  'deptcourses': deptcourses})
                except:
                    pass
                print(f"{year}/{year+1}-{semester} {i+1}/{len(deptcodesnames)} departments", end="\r")
            # next semester!
            semester += 1

            print()

        # next year!
        year += 1
        semester = 1

    with open("pprint.out", 'w') as fout:
        pprint(data, stream=fout)

newmain()

# import itertools
# cs = list(itertools.chain(*(d['courses'] for d in depts)))
# pprint(sorted(cs, key=lambda c: max([int(x) for x in c['Hours']], default=0), reverse=True)[0:75])
