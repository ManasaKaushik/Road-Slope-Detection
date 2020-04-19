import csv
import math

def distanceBetweenPoints(start,end):
    long1, latt1, long2, latt2 = map(math.radians, [start[1], start[0], end[1], end[0]])
    dlong = long2 - long1
    dlatt = latt2 - latt1
    a = math.sin(dlatt / 2) ** 2 + math.cos(latt1) * math.cos(latt2) * math.sin(dlong / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km

link_list = []
with open("Partition6467LinkData.csv", "r") as link_file:
    reader_link = csv.reader(link_file, delimiter=",")
    for line in reader_link:
        link_list.append({'linkPVID':line[0],'refNodeId':line[1],'nrefNodeID':line[2],'length':line[3],'class':line[4],
                          'direction':line[5],'speedCategory':line[6],'fromRefSpped':line[7],'toRefSpeed':line[8],
                          'fromRefNumLanes':line[9],'toRefNumLanes':line[10],'multiDigitized':line[11],'urban':line[12],
                          'timezone':line[13],'shapeInfo':line[14],'curvatureInfo':line[15],'slopeInfo':line[16],'probepoints':[]})
link_file.close()
line_cnt = 0
print("Detecting Slope has been started..")
print("Have a cup of coffee as it will take some time")
with open("Partition6467MatchedPoints.csv", "r") as probe_file:
    prev = None
    reader_probe = csv.reader(probe_file, delimiter=",")
    header = next(reader_probe)
    for line in reader_probe:
        probe = {}
        probe['sampleId'] = line[0]
        probe['dateTime'] = line[1]
        probe['sourceCode'] = line[2]
        probe['latitude'] = float(line[3])
        probe['longitude'] = float(line[4])
        probe['altitude'] = line[5]
        probe['speed'] = line[6]
        probe['heading'] = line[7]
        probe['linkPVID'] = line[8]
        probe['direction'] = line[9]
        probe['distFromRef'] = line[10]
        probe['distFromLink'] = line[11]
        probe['street_assigned'] = None
        probe['elevation'] = None
        probe['slope'] = None

        if not prev: probe['slope'] = 'X'
        elif probe['linkPVID'] != prev['linkPVID']: probe['slope'] = 'X'
        else:
            end_point = list(map(float,[prev['longitude'],prev['latitude']]))
            start_point = list(map(float,[probe['longitude'],probe['latitude']]))
            opp = float(probe['altitude']) - float(prev['altitude'])
            hyp = distanceBetweenPoints(start_point,end_point)/1000
            if float(hyp) != 0.0:
                probe['slope'] = math.atan(float(opp)/float(hyp))
                probe['slope'] = (2*math.pi*probe['slope'])/360
                for link in link_list:
                    if probe['linkPVID'] == link['linkPVID'] and link['slopeInfo'] != '':
                        link['probepoints'].append(probe)
                        break
        prev = probe
slope = open("SlopeData.csv","w").close() # Need to add header
slope = open("SlopeData.csv","w")
data_slp = csv.writer(slope)
data_slp.writerow(['LinkPVID','Calc Slope'])
for link in link_list:
    if len(link['probepoints']) > 0:
        sum,sumSlope,cslp,culmulate = 0.0,0.0,0.0,0.0
        prbcnt = 0
        mslpe = []
        for probe in link['probepoints']:
            if probe['direction'] == 'T': probe['slope'] = -probe['slope']
            if probe['slope'] != 'X':
                if probe['slope'] != 0:
                    sum = sum + probe['slope']
                    prbcnt += 1

        if prbcnt != 0:
            cslp = sum/prbcnt
            culmulate = sum
        else: cslp = 0
        slpe = link['slopeInfo'].strip().split('|')
        for slope in slpe:
            sumSlope+=float(slope.strip().split('/')[1])

        mslpe = sumSlope/len(slpe)
        data_slp.writerow([probe['linkPVID'],cslp])
print("Slope file written")
