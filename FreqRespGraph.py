import matplotlib.pyplot as plt
import csv
import argparse
import glob
import math
import os

from matplotlib.ticker import FuncFormatter

# X-Axis labels
def myformatter(x, pos):
    if x == 20:
        return '20'
    if x == 100:
        return '100'
    if x == 1000:
        return '1k'
    if x == 10000:
        return '10k'
    if x == 20000:
        return '20k'
    return ''

# Draw given CSV file frequency response
def drawCurve(filename, ax, alignmin, alignmax, isref):
    #  X/Y data to be drawn 
    x = []
    y = []

    # Alignment calculation
    minalignDistance = 1000000
    alignOffset = 0
    alignCount = 0

    # Read CSV file
    csvfile = open(filename, newline='')
    c = csv.reader(csvfile)
    for row in c:
        try:
            xf = float(row[0])
            yf = float(row[1])
            if alignmin > 0:
                if alignmax < 0:
                    # Align to frequency point
                    alignDistance = math.fabs(xf - alignmin)
                    if alignDistance < minalignDistance:
                        minalignDistance = alignDistance
                        alignOffset = yf
                else:
                    if xf > alignmin and xf < alignmax:
                        # Align to frequency range
                        alignOffset = alignOffset + yf
                        alignCount = alignCount + 1
            x.append(xf)
            y.append(yf)
        except ValueError as ve:
            print( 'Ignoring: ', row, 'in ' , filename)
    csvfile.close()

    # Align data
    if alignmin > 0:
        if alignmax > 0 and alignCount > 0:
            # Align to frequency range
            alignOffset = alignOffset / alignCount
        length = len(y)
        for i in range(length):
            y[i] = y[i] - alignOffset

    # Draw graph
    if isref:
        ax.plot(x, y, '--k', label=os.path.basename(filename))
    else:
        ax.plot(x, y, '-', label=os.path.basename(filename))

# Parse command line
parser = argparse.ArgumentParser(prog='FreqRespGraph',
                                 description='''
FreqRespGraph can plot single or multiple frequency response graphs given as CSV data files in a single graph.
X and Y Axis limit can be configured. Data can be aligned to 0dB at a given frequency or frequency range. In
addition a reference curve can be specified. The CSV data files needs to contain 2 rows with frequeny and SPL.
'''
)
parser.add_argument('--ymin', nargs='?', type=float, default='-30', help='Y-Axis minumum, default -30db')
parser.add_argument('--ymax', nargs='?', type=float, default='20', help='Y-Axis maximum, default 20db')
parser.add_argument('--xmin', nargs='?', type=float, default='20', help='X-Axis minumum, default 20Hz')
parser.add_argument('--xmax', nargs='?', type=float, default='20000', help='X-Axis maximum, default 20000Hz')
parser.add_argument('--alignmin', nargs='?', type=float, default='-1', help='Align Y-Axis at given frequency to 0 dB, default off')
parser.add_argument('--alignmax', nargs='?', type=float, default='-1', help='Align Y-Axis at frequency range to 0 dB, default off')
parser.add_argument('--hidealignment', action='store_true', help='Do not show aligment arguments in Y-Axis label, default off')
parser.add_argument('--refcurve', nargs='?', default='', help='Plot given CSV file as dotted reference curve, default off')
parser.add_argument('--nolegend', action='store_true', help='Do not show curves legend, default off')
parser.add_argument('--title', nargs='?', default='', help='Set graph title, default off')
parser.add_argument('--files', nargs='*',  required=True, help='CSV filenames to be plotted (supports filename wildcards)')
args = parser.parse_args()

print (args )
# Initialize layout
fig, ax = plt.subplots(figsize = (9, 6))

# Draw curve for each given CSV
for filepattern in args.files:
    files = glob.glob(filepattern)
    for file in files:
        drawCurve(file, ax, args.alignmin, args.alignmax, False)

# Draw refernace curve if given
if args.refcurve != '':
    drawCurve(args.refcurve, ax, args.alignmin, args.alignmax, True)

# Draw Legend if not disabled
if not args.nolegend:
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize='xx-small')

# Set logarithmic scale on the x axis
ax.set_xscale("log");

# Set Axis limits
ax.set_xlim(args.xmin,args.xmax)
ax.set_ylim(args.ymin,args.ymax)

# Set X Axis major and minor ticks
formatter = FuncFormatter(myformatter)
ax.xaxis.set_major_formatter(formatter)
ax.xaxis.set_minor_formatter(formatter)

# Set Axis labels
ax.set_xlabel('Frequency [Hz]')
ylabel = 'SPL [dB]'
if not args.hidealignment and args.alignmin > 0:
    if args.alignmax > 0:
        ylabel = ylabel + '\n(Aligned to 0db at ' + str(int(args.alignmin)) + '...' + str(int(args.alignmax)) + ' Hz)'
    else:
        ylabel = ylabel + '\n(Aligned to 0db at ' + str(int(args.alignmin)) + ' Hz)'
ax.set_ylabel(ylabel)

# Enable grid lines
plt.grid(which='both')

# Set Title if given
if args.title != '':
    plt.title(args.title)

# Show result
plt.show()
