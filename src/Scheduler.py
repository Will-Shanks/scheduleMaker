import MySQLdb
from collections import defaultdict
import itertools
import json
from flask import Flask, render_template, request, abort
import secrets

import argparse
import logging
import pprint

db = MySQLdb.connect(host=secrets.DBHOST, user=secrets.DBUSER, passwd=secrets.DBPASSWD, db=secrets.DBNAME)
cur = db.cursor()

app = Flask(__name__,
            static_url_path='',
            static_folder='web/static',
            template_folder='web/templates')

class Node:
    def __init__(self, sections):
        self.days = {'M': [], 'T': [], 'W': [], 'R': [], 'F': []}
        self.sections = sections
        if isinstance(sections, int):
            self.addSection(sections)
        else:
            for section in sections:
                self.addSection(section)
        for day in self.days:
            self.days[day].sort()

    def addSection(self, sectionID):
        cur.execute("SELECT start, finish, days FROM section WHERE id='" + str(sectionID) + "';")
        sectionInfo = cur.fetchone()
        if sectionInfo[2] == "ONLINE":
            return
        for day in sectionInfo[2]:
            self.days[day].append([sectionInfo[0], sectionInfo[1]])

    def isCompat(self, b):
        for day in self.days:
            if self.days[day] != [] and b.days[day] != []:
                for timeRange in self.days[day]:
                    i = 0
                    while i < len(b.days[day]):
                        if timeRange[0] == b.days[day][i][0] or timeRange[1] == b.days[day][i][1]:
                            return False
                        if timeRange[0] < b.days[day][i][0]: # self starts before b
                            if timeRange[1] > b.days[day][i][0]:
                                return False
                        if timeRange[0] > b.days[day][i][0]:
                            if timeRange[1] < b.days[day][i][1]:
                                return False
                        i += 1
        return True

    def computeRank(self):
        self.daysOfClass = 0
        self.longestDay = 0
        self.avgDayLen = 0
        self.earliestStart = None
        self.latestFinish = None
        self.longestGap = 0
        for day in self.days.values():
            if not day == []:
                if len(day) >= 2:
                    for i in range(len(day)-1):
                        if(self.longestGap < (day[i+1][0].seconds - day[i][1].seconds)):
                            self.longestGap = day[i+1][0].seconds - day[i][1].seconds
                if (self.earliestStart is None) or (day[0][0].seconds < self.earliestStart.seconds):
                    self.earliestStart = day[0][0]
                if (self.latestFinish is None) or (day[len(day)-1][1].seconds > self.latestFinish.seconds):
                    self.latestFinish = day[len(day)-1][1]
                self.daysOfClass += 1
                dayLen = day[len(day)-1][1].seconds - day[0][0].seconds
                self.avgDayLen += dayLen
                if dayLen > self.longestDay:
                    self.longestDay = dayLen
        self.avgDayLen = (self.avgDayLen/self.daysOfClass)/3600
        self.longestDay /= 3600
        self.longestGap /= 3600

    def stats(self):
        return{'avgDayLen': self.avgDayLen, 'daysOfClass': self.daysOfClass, 'earliestStart': self.earliestStart.seconds, 'latestFinish': self.latestFinish.seconds, 'longestDay':self.longestDay, 'longestGap': self.longestGap}


# Takes course/section ID
# Returns matrix of Nodes (course component x section) (each section is a node)
def getCourseComponents(course):
    courseComponents = []
    sectionCode = False
    sectionComp = False
    courseCode = course
    if '-' in course:
        courseCode = course.split('-')
        sectionCode = courseCode[1]
        courseCode = courseCode[0]

    cur.execute("SELECT id FROM course WHERE code='" + courseCode + "';")
    courseID = str(cur.fetchone()[0])
    if sectionCode:
        sectionCode = sectionCode.lstrip('0')
        cur.execute(
            "SELECT component FROM SECTION WHERE section = '" + sectionCode + "' and  course_id='" + courseID + "';")
        sectionComp = cur.fetchone()[0]

    cur.execute(("SELECT Distinct component FROM section WHERE course_id='" + courseID + "';"))
    sectionID = cur.fetchall()
    # add each component of each class to sections as its own list
    for sect in sectionID:
        if sectionComp == sect[0]:
            cur.execute(
                "SELECT id FROM section WHERE course_id='" + courseID + "' AND section ='" + sectionCode + "';")
        else:
            cur.execute(
                "SELECT id FROM section WHERE course_id='" + courseID + "' AND component ='" + sect[0] + "';")
        componentSectionIDs = cur.fetchall()
        component = []
        for compSectID in componentSectionIDs:
            component.append(Node(compSectID))
        courseComponents.append(component)
    return courseComponents

# Takes matrix of Nodes
# Returns dict of lists node: [edges]
def buildGraph(vertexNodes):
    graph = defaultdict(set)
    if len(vertexNodes) == 1:
        for vertex in vertexNodes[0]:
            graph[vertex] = None
    else:
        for i in range(len(vertexNodes) - 1):
            for j in range(len(vertexNodes[i])):
                k = len(vertexNodes) - 1
                while k > i:
                    for l in range(len(vertexNodes[k])):
                        if vertexNodes[i][j].isCompat(vertexNodes[k][l]):
                            graph[vertexNodes[i][j]].add(vertexNodes[k][l])
                            graph[vertexNodes[k][l]].add(vertexNodes[i][j])
                    k -= 1
    return graph

# Takes dict of lists of nodes and their edges
# Returns list of nodes where each node is a clique of size <numNodesToChoose> of the input nodes
def getCliques(graphEdges, numNodesToChoose):
    def addComplete():
        courses = defaultdict(list)
        for item in compsub:
            for sectID in item.sections:
                cur.execute("SELECT course_id FROM SECTION WHERE id = '" + str(sectID) + "';")
                courseCode = cur.fetchone()[0]
                courses[str(courseCode)].append(sectID)
        for course in list(courses.keys())[:]:
            cur.execute("SELECT COUNT(DISTINCT component) FROM section WHERE course_id =" + course + ";")
            if (len(courses[course]) != cur.fetchone()[0]):
                courses.pop(course)
        if len(courses) < numNodesToChoose:
            return
        courseCombos = list(itertools.combinations(courses, numNodesToChoose))
        nonlocal solutions
        for combo in courseCombos:
            option = []
            for thing in combo:
                option += courses[thing]
                option.sort()
            solutions.add(tuple(option))

    def recurfunct(candidates, nays):
        nonlocal compsub
        if not candidates and not nays:
            addComplete()
        else:
            u = max(candidates, key=lambda x: len([x for x in graphEdges[x] if x in candidates]))
            # u = max(candidates, key=lambda x: len(graphEdges[x]))
            uConn = getConnected(u, candidates)
            for selected in [x for x in candidates.copy() if x not in uConn]:
                candidates.remove(selected)
                candidatesTemp = getConnected(selected, candidates)
                naysTemp = getConnected(selected, nays)
                compsub.append(selected)
                recurfunct(candidatesTemp, naysTemp)
                compsub.pop()
                nays.append(selected)
                pass

    def getConnected(vertex, oldSet):
        newSet = []
        for neighbor in graphEdges[vertex]:
            try:
                if neighbor in oldSet:
                    newSet.append(neighbor)
            except Exception as inst:
                pass
        if newSet is None:
            pass
        return newSet

    solutions = set()

    if all(v is None for v in graphEdges.values()):
        for x in graphEdges.keys():
            compsub = [x]
            addComplete()
    else:
        compsub = []
        possibles = list(graphEdges.keys())
        recurfunct(possibles, [])
    results = [Node(x) for x in solutions]
    return results

def getScheds(choices):
    choices = json.loads(choices)# options will be matrix of section nodes
    options = []

    logging.info(pprint.pformat(choices))

    # choice == ["course1", ... "coursen"], numToChoose
    # makes matrix of nodes where each node is a clique
    for choice in choices:
        # getSections will return list of lists of nodes sections[course component][section]
        if isinstance(choice[0], str):
            components = getCourseComponents(choice[0])
        else:
            components = []
            for courseID in choice[0]:
                components += getCourseComponents(courseID)

        if len(components) == 1:
            # if only 1 section then only 1 node in graph and no edges
            options.append([components[0][0]])
        else:
            components.sort(key=lambda comp: len(comp))
            # edges is a list of edges for each node
            # edges[i] = [[edges], [sectionIDs]]
            edges = buildGraph(components)
            # getCliques returns list of nodes (each possible clique is a node
            #getCliques(list of edges, num of nodes to choose
            options.append(getCliques(edges, choice[1]))

    options.sort(key=lambda comp: len(comp))
    edges = buildGraph(options)
    numToChoose = 0
    for choice in choices:
        numToChoose += choice[1]
    options = getCliques(edges, numToChoose)
    for x in options:
        x.computeRank()
    schedules = []
    for sched in options:
        schedule = {}
        scheds = []
        for section in sched.sections:
            cur.execute("SELECT course_id, section, start, finish, days FROM section WHERE id='" + str(section) + "';")
            schedInfo = (cur.fetchone())
            cur.execute("SELECT code FROM course WHERE id='" + str(schedInfo[0]) + "';")
            coursename = cur.fetchone()
            f = lambda x: x.seconds if x else None
            schedInfo = [coursename[0]+'-'+schedInfo[1], f(schedInfo[2]), f(schedInfo[3]), schedInfo[4]]
            scheds.append(schedInfo)
        schedule['scheds'] = scheds
        schedule['stats'] = sched.stats()
        schedules.append(schedule)
    return schedules

def filterByStart(scheds, earliestStart):
    earliestStart = earliestStart.split(":")
    earliestStart = int(earliestStart[0]) * 3600 + int(earliestStart[1]) * 60
    scheds = [x for x in scheds if x.earliestStart.seconds >= earliestStart]
    return scheds

def filterByFinish(scheds, finishTime):
    finishTime = finishTime.split(':')
    finishTime = int(finishTime[0]) * 3600 + int(finishTime[1]) * 60
    scheds = [x for x in scheds if x.latestFinish.seconds <= finishTime]
    return scheds

def filterByLongestGap(scheds, maxGap):
    maxGap = maxGap.split(':')
    maxGap = int(maxGap[0]) + (int(maxGap[1]) / 3600)
    scheds = [x for x in scheds if x.longestGap <= maxGap]
    return scheds



@app.route('/')
def root():
    classes = ['HIND1020-001', 'CSCI3104-100', 'CSCI3155-100']
    return render_template('schedules.html', classes=map(json.dumps, classes))

@app.route('/', methods=['POST'])
def classForm():
   result = request.get_json()
   logging.info(pprint.pformat(result))

   choices = []
   selection =[]
   choice = []

   for section in result['classList']:
      choice.append(section)
   selection.append(choice)
   selection.append(int(result['classNum']))
   choices.append(selection)

   schedules = getScheds(json.dumps(choices))

   dayIndex = {'M':1,'T':2, 'W':3, 'R':4, 'F':5}

   startEarliest = 8
   startLatest = 18
   startStep = 1

   n = startLatest - startEarliest + 1   # !!! TODO Use startStep
   m = 6
   weekViews = []
   for num, schedule in enumerate(schedules, start=1):
       week = {}
       weekSched = [[''] * m for i in range(n)]
       for i in range(n):
          weekSched[i][0] = '{:02d}'.format(startEarliest + i*startStep) + ':00'  ## !!! TODO

       logging.debug(pprint.pformat(schedule))
       for sched in schedule['scheds']:
           logging.debug(pprint.pformat(sched))

           for day in sched[3]:
               weekSched[startIndex(sched[1], startEarliest)][dayIndex[day]] = sched[0]
               # !!! TODO Add something for End, ie may be a double period etc
       week['sched'] = weekSched
       week['stats'] = schedule['stats']
       weekViews.append(week)

   logging.debug(pprint.pformat(weekViews))
   return json.dumps(weekViews)

def startIndex(seconds, startEarliest):
    hours = seconds / 3600
    return int(hours-startEarliest)

def getTimeString(seconds):
    hours = seconds / 3600
    mins = (seconds%3600)/60
    sec = (seconds%3600)%60
    return '{:02d}'.format(int(hours)) + ':' '{:02d}'.format(int(mins))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        help="Run in debug mode and print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        app.run(debug = True)
    else:
        app.run(host='0.0.0.0', port=80)

    #choices = [[["HIND1020-001", "CSCI3104-100", "CSCI3155-100"],3]]
    #scheds = getScheds(choices)

    #exit(0)
    #scheds = filterByStart(scheds, '9:00')
    #scheds = filterByFinish(scheds, '17:00')
    #scheds = filterByLongestGap(scheds, '3:00')

    #scheds.sort(key=lambda x: x.longestDay)
    #scheds.sort(key=lambda x: x.latestFinish.seconds, reverse=True)
    #scheds.sort(key=lambda x: x.earliestStart.seconds)
    #scheds.sort(key=lambda x: x.avgDayLen)
    #scheds.sort(key=lambda x: x.longestGap)
    #scheds.sort(key=lambda x: x.daysOfClass)
'''
    schedules = []
    for sched in scheds:
        schedule = []
        for section in sched.sections:
            cur.execute("SELECT course_id, section, start, finish, days FROM section WHERE id='" + str(section) + "';")
            schedInfo = (cur.fetchone())
            cur.execute("SELECT code FROM course WHERE id='" + str(schedInfo[0]) + "';")
            coursename = cur.fetchone()
            schedInfo = [coursename[0]+'-'+schedInfo[1], schedInfo[2].seconds, schedInfo[3].seconds, schedInfo[4]]
            schedule.append(schedInfo)
        schedules.append(schedule)

    print(json.dumps(schedules))
    '''
