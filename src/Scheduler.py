import MySQLdb
from collections import defaultdict
import itertools
import secrets

db = MySQLdb.connect(host=secrets.DBHOST, user=secrets.DBUSER, passwd=secrets.DBPASSWD, db=secrets.DBNAME)
cur = db.cursor()

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


def getSections(courses):
    def getCourse(course):
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
            cur.execute(
                "SELECT component FROM SECTION WHERE section = '" + sectionCode + "' and  course_id='" + courseID + "';")
            sectionComp = cur.fetchone()[0]

        cur.execute(("SELECT Distinct component FROM section WHERE course_id='" + courseID + "';"))
        sectionID = cur.fetchall()
        # add each component of each class to sections as its own list
        for sect in sectionID:
            if sectionComp == sect[0]:
                cur.execute(
                    "SELECT * FROM section WHERE course_id='" + courseID + "' AND section ='" + sectionCode + "';")
            else:
                cur.execute(
                    "SELECT * FROM section WHERE course_id='" + courseID + "' AND component ='" + sect[0] + "';")
            sections.append(cur.fetchall())
    sections = []
    if isinstance(courses, str):
        getCourse(courses)
    else:
        for course in courses:
            getCourse(course)
    sections.sort(key=lambda course: len(
        course))  # sorts sections so the courses with least sections are first for performance
    return sections

def buildChoiceGraph(sections):
    def isCompat(a, b):
        # index 6 is string of days section meets ex: MTWRF
        # index 4 is start time of section meeting (24hr)
        # index 5 is finish time of section meeting (24hr)
        if (a[6] == "ONLINE" or b[6] == "ONLINE"):  # online classes don't have time conflicts
            return True
        for day in a[6]:
            if day in b[6]:
                if (a[4] < b[4]):  # if a starts before b starts
                    if (a[5] > b[4]):  # a must finish before b starts
                        return False
                elif (a[4] < b[5]):  # b must finish before a starts
                    return False
                break  # if compatible on 1 day where both meet, always compatible
        return True

    intersect = defaultdict(set)
    for i in range(len(sections)):  # traverse through each course
        for j in range(len(sections[i])):  # traverse through each section of a course

            sectID = str(sections[i][j][0])
            for k in range(1, len(
                    sections) - i):  # traverse relevant courses (row i + 1 is first row below self in matrix)
                for l in range(len(sections[k + i])):  # traverse through sections of each course
                    if isCompat(sections[i][j], sections[i + k][l]):
                        newSectID = str(sections[i + k][l][0])
                        intersect[sectID].add(newSectID)
                        intersect[newSectID].add(sectID)
    return intersect

def getCliques(edges, minCourses, numSections):
    def addComplete():
        nonlocal solutions
        if isinstance(compsub[0], Node):
            if len(compsub) < minCourses:
                return
            solutions.add(tuple(compsub))
            return
        courses = defaultdict(list)
        for section in compsub:
            cur.execute("SELECT course_id FROM SECTION WHERE id = '" + section + "';")
            courseCode = cur.fetchone()[0]
            courses[str(courseCode)].append(section)
        for course in list(courses.keys()):
            cur.execute("SELECT COUNT(DISTINCT component) FROM section WHERE course_id =" + course + ";")
            if (len(courses[course]) != cur.fetchone()[0]):
                courses.pop(course)
        if minCourses == -1:
            if len(compsub) < (numSections - 1):
                return
        if len(courses) < minCourses:
            return

        courseCombos = list(itertools.combinations(courses, minCourses))
        for combo in courseCombos:
            option = []
            for thing in combo:
                option.append(courses[thing])
            option = [item for sublist in option for item in sublist]
            option.sort(key=lambda x: int(x))
            option = tuple(option)
            solutions.add(option)

    def recurfunct(candidates, nays):
        nonlocal compsub
        if not candidates and not nays:
            addComplete()
        else:
            for selected in candidates.copy():
                candidates.remove(selected)
                candidatesTemp = getConnected(selected, candidates)
                naysTemp = getConnected(selected, nays)
                compsub.append(selected)
                recurfunct(candidatesTemp, naysTemp)
                compsub.pop()
                nays.add(selected)

    def getConnected(vertex, oldSet):
        newSet = set()
        if isinstance(vertex, Node):
            for neighbor in edges[vertex]:
                if neighbor in oldSet:
                    newSet.add(neighbor)
        else:
            for neighbor in edges[str(vertex)]:
                if neighbor in oldSet:
                    newSet.add(neighbor)
        return newSet

    compsub = []
    solutions = set()
    possibles = set(edges.keys())
    recurfunct(possibles, set())
    return solutions

def getChoiceOptions(choice):
    sections = getSections(choice[0])
    if len(sections) == 1:
        return set([sections[0][0][0]])
    edges = buildChoiceGraph(sections)
    options = getCliques(edges, choice[1], len(sections))
    return options

def buildSchedGraph(choiceCliques):
    vertexNodes = []
    for choiceList in choiceCliques:
        choiceNodes = []
        for choice in choiceList:
            choiceNodes.append(Node(choice))
        vertexNodes.append(choiceNodes)
    graph = defaultdict(set)
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

def getScheds(choiceCliques, minChoices, hasRequired):
    graph = buildSchedGraph(choiceCliques)
    scheds = getCliques(graph, minChoices, len(choiceCliques))
    return scheds

def printSched(scheds):
    for sectionID in scheds:
        cur.execute("SELECT course_id, component, section FROM SECTION WHERE id = '" + str(sectionID) + "';")
        sectionInfo = cur.fetchone()
        cur.execute("SELECT name, code FROM course WHERE id='" + str(sectionInfo[0]) + "';")
        courseInfo = cur.fetchone()
        print(courseInfo[1] + "-" + str(sectionInfo[2]) + "     " + courseInfo[0] + "  " + sectionInfo[1])
    print("============================================")


def main():
    choices = [[["Math3510", "CSCI3104"], 2], [["HIND1020"], 1]]#, [["CSCI3155"], 1], [["CSCI3022"], 1], [["PHYS1140"], 1]]
    # a choice is given as: [[<courses>], <number to choose>]
    # if choice[1] is not an int, and is == -1 then this is the list of required courses/sections
    choiceOptions = []
    for choice in choices:
        choiceOptions.append(getChoiceOptions(choice))
    scheds = getScheds(choiceOptions, len(choices), -1 == choices[0][1]) #if choices[0][1] == -1 then there is a list of required

    sorted = []
    for sched in scheds:
        temp = []
        for choice in sched:
            if isinstance(choice.sections, int):
                temp.append(choice.sections)
            else:
                for sect in choice.sections:
                    temp.append(int(sect))
        temp.sort()
        sorted.append(temp)
    sorted.sort()
    for sched in sorted:
        printSched(sched)
    #print("bye!")
    print(len(scheds))

if __name__== "__main__":
    main()
    exit(0)
