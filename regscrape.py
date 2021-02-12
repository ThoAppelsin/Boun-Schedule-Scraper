from pprint import pprint
from bs4 import BeautifulSoup
import requests
import re
import sys
import json
import pandas
import csv
from collections import OrderedDict
import traceback
from urllib.parse import quote_plus

def makesoup(address):
    raw = requests.get(address)
    print(raw.apparent_encoding)
    raw.encoding = 'iso8859-9'
    # raw.encoding = 'utf-8'
    # raw.encoding = raw.apparent_encoding
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
    soup = makesoup(deptaddress)

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
            if course['name'] == 'ASIA520.02':
                print(course['parentName'])
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

def intfromrange(intable, minval, maxval):
    intable = int(intable)
    if minval <= intable <= maxval:
        return intable
    else:
        raise Exception(f"Valid range is [{minval}, {maxval}]. {intable} was given.")

def inputfromrange(prompt, minval, maxval):
    while True:
        try:
            return intfromrange(input(prompt), minval, maxval)
        except Exception as e:
            print(e, "Please try again.")

def validatestring(string, strings):
    if string in strings:
        return string
    else:
        raise Exception(f"Valid inputs are {strings}. {string} was given.")

def inputfromstrings(prompt, strings):
    while True:
        try:
            return validatestring(input(prompt), strings)
        except Exception as e:
            print(e, "Please try again.")

def printarguments():
    print("1) Start year (i.e. 2010 for year 2010/2011)")
    print("2) Start semester (1/2/3 for Fall/Spring/Summer)")
    print("3) End year")
    print("4) End semester")
    print("5) Output format (csv or json)")

def newmain():
    deptcodesnames = getdeptcodesnames()
    
    if len(sys.argv) > 1:
        interactive = False

        if len(sys.argv) == 6:
            try:
                startyear     = intfromrange(sys.argv[1], 2000, 2020)
                startsemester = intfromrange(sys.argv[2], 1, 3)
                endyear       = intfromrange(sys.argv[3], startyear, 2020)
                endsemester   = intfromrange(sys.argv[4], startsemester if startyear == endyear else 1, 3)
                formatstring  = validatestring(sys.argv[5].lower(), ['csv', 'json'])
            except Exception as e:
                print(e, "Please try again. Arguments should be:")
                printarguments()
                sys.exit()
        else:
            print("Either run without arguments (interactive mode) or with exactly the following arguments:")
            printarguments()
            sys.exit()
    else:
        interactive = True

        startyear     = inputfromrange("Year to start from (enter 2010 for year 2010/2011): ", 2000, 2020)
        startsemester = inputfromrange("Semester to start from (enter 1/2/3 for Fall/Spring/Summer: ", 1, 3)

        endyear       = inputfromrange("Year to finish at (enter 2010 for year 2010/2011): ", startyear, 2020)
        endsemester   = inputfromrange("Semester to finish at (enter 1/2/3 for Fall/Spring/Summer: ", startsemester if startyear == endyear else 1, 3)

        formatstring  = inputfromstrings("Output format (csv or json): ", ['csv', 'json'])

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

    outfile = open(f'output.{formatstring}', 'w', encoding='utf-8') if interactive else sys.stdout
    if formatstring == 'json':
        print(json.dumps(data), file=outfile)
    elif formatstring == 'csv':
        writer = csv.writer(outfile)
        headerprinted = False
        for year in data:
            yeardata = data[year]
            for sem in yeardata:
                semdata = yeardata[sem]
                for deptdata in semdata:
                    for deptcoursedata in deptdata['deptcourses']:
                        if not headerprinted:
                            headerprinted = True
                            writer.writerow('year term deptcode'.split() + [str(v) for v in deptcoursedata.keys()])
                        writer.writerow([str(v) for v in [year, sem, deptdata['deptcode']] + list(deptcoursedata.values())])

newmain()

# import itertools
# cs = list(itertools.chain(*(d['courses'] for d in depts)))
# pprint(sorted(cs, key=lambda c: max([int(x) for x in c['Hours']], default=0), reverse=True)[0:75])
