#!/usr/bin/python3
import os
import argparse
import tempfile

class padcount:
    def __init__(self, desc):
       geometry = desc.split('x')
       self.x = int(geometry[0])
       self.y = int(geometry[1])

class pad:
    # Column alphabet, skips characters that may overlap with digits.
    alphabet = 'ABCDEFGHJKLMNPRTUVWY'
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def name(self):
        base = len(self.alphabet)
        if (self.y >= base):
            row = self.alphabet[(self.y // base)-1]
            row += self.alphabet[self.y % base]
        else:
            row = self.alphabet[self.y]
        return row + str(self.x + 1)

# Pad globbing class.
class padglob:
    # Column alphabet, skips characters that may overlap with digits.
    alphabet = 'ABCDEFGHJKLMNPRTUVWY'
    
    def rownum(self, name):
        row = self.alphabet.find(name[0])
        if len(name) > 1:
            row = (row + 1) * len(self.alphabet)
            row += self.alphabet.find(name[1])
        return row

    def __init__(self, glob):
        # Get leading alphanumerics for the starting column.
        glob = glob.upper()
        rowstart = ''
        rowend = ''
        colstart = ''
        colend = ''
        
        # Get the leading alphabetical characters for the starting row.
        while glob[0] in self.alphabet:
            rowstart += glob[0]
            glob = glob[1:]
        # If the next character is a hyphen, we have a row range.
        if glob[0] == '-':
            glob = glob[1:]
            while glob[0] in self.alphabet:
                rowend += glob[0]
                glob = glob[1:]
        else:
            rowend = rowstart

        # Get the leading numerical characters for the starting row.
        while len(glob) and glob[0].isdigit():
            colstart += glob[0]
            glob = glob[1:]
        
        # If the next character is a hyphen, we have a row range.
        if len(glob) == 0:
            colend = colstart
        elif glob[0] == '-':
            colend += glob[1:]
      
        # Create ranges for matching.
        self.rowrange = range(self.rownum(rowstart), self.rownum(rowend)+1)
        self.colrange = range(int(colstart)-1, int(colend))

    def match(self, name):
        base = len(self.alphabet)
        rowlen = 0
        for ch in name:
            if ch in self.alphabet:
               rowlen += 1
            else:
               break
        row = self.rownum(name[0:rowlen])
        col = int(name[rowlen:])
        
        return (col in self.colrange) and (row in self.rowrange)

    def matchxy(self, x, y):
        return (x in self.colrange) and (y in self.rowrange)

# Check if the pad should be skipped.
def padskip(globlist, x, y):
    if not globlist:
       return False
    for g in globlist:
       if g.matchxy(x, y):
           return True
    return False

parser = argparse.ArgumentParser(description='Generate BGA Package models')
parser.add_argument('padcount', metavar='COLSxROWS', type=padcount, nargs='?',
                    help='Number of rows and columns to generate')

# Arguments for package dimensions.
parser.add_argument('-A', '--height', metavar='HEIGHT', type=float, nargs='?',
                    help='Total package height', default=1.0)
parser.add_argument('-D', '--width', metavar='WIDTH', type=float, nargs='?',
                    help='Package width (horizontal)')
parser.add_argument('-E', '--length', metavar='LENGTH', type=float, nargs='?',
                    help='Package length (vertical)')
parser.add_argument('-Z', '--zplane', metavar='HEIGHT', type=float, nargs='?',
                    help='Package starting height above board')

# Arguments for ball dimensions.
parser.add_argument('-b', '--ball', metavar='DIA', type=float, nargs='?',
                    help='BGA Ball diameter')
parser.add_argument('-e', '--pitch', metavar='PITCH', type=float, nargs='?',
                    help='BGA Ball pitch', default=0.8)

# Arguments for omitted balls.
parser.add_argument('--skip', metavar='RANGE', type=padglob, action='append',
                    help='Range of balls to skip')

args = parser.parse_args()
xcount = args.padcount.x
ycount = args.padcount.y

# Compute sensible defaults based on pitch and count.
if args.ball is None:
    args.ball = args.pitch / 2
if args.width is None:
    args.width = (xcount + 2) * args.pitch
if args.length is None:
    args.length = (ycount + 2) * args.pitch
if args.zplane is None:
    args.zplane = (args.ball * 3) / 4

# Generate the BGA package OpenSCAD file.
scadfile = tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False)
print("Creating SCAD file at %s" % (scadfile.name))

# Use the BGA library template.
template = os.path.join(os.path.dirname(__file__), "bga.scad")
scadfile.write("use <%s>\n" % (os.path.abspath(template)))

# Write the BGA parameters.
scadfile.write("ball_top = %f;\n" % (args.zplane))

# Generate the BGA package.
scadfile.write("union() {\n")
scadfile.write("    bga_package(%f, %f, %f);\n" % (args.length, args.width, args.height))
xoffset = -(xcount - 1) * args.pitch / 2
yoffset = (ycount - 1) * args.pitch / 2
for x in range(0, xcount):
    for y in range(0, ycount):
        if not padskip(args.skip, x, y):
            xpos = xoffset + (x * args.pitch)
            ypos = yoffset - (y * args.pitch)
            scadfile.write("    bga_ball(%f, %f, d=%f);\n" % (xpos, ypos, args.ball))
        else:
            p = pad(x, y)
            print("Skipping ball %s" % (p.name))

scadfile.write("}\n")
scadfile.close()

# Run OpenSCAD to generate the 3D model.
os.system("openscad %s" % (scadfile.name))
