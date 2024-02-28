import matplotlib.pyplot as plt
import csv
import argparse
import glob
import math
import os
import numpy as np
import bq.biquad as bq
from scipy.signal import savgol_filter
from scipy import interpolate

from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import LogFormatter

# No impedance EQ
zeq = None

# X-Axis minor ticks labels
def myformatter(x, pos):
    if x == args.xmin:
        return str(int(args.xmin))
    if x == args.xmax:
        return str(int(args.xmax))
    return ''


# On legend pick event, highlight curve (first click), hide curve (second click) or switch back to default (third click)
def on_pick(event):
    legend_line = event.artist

    # Do nothing if the source of the event is not a legend line.
    if legend_line not in map_legend_to_ax:
        return

    ax_line = map_legend_to_ax[legend_line]
    lw = ax_line.get_linewidth()
    visible = ax_line.get_visible()
    if visible and lw < 2.0:
        # Higlight
        ax_line.set_linewidth(4.0)
        legend_line.set_alpha(1.0)
        ax_line.set_zorder(10)
    if visible and lw > 2.0:
        # Hide
        ax_line.set_linewidth(1.5)
        ax_line.set_visible(False)
        legend_line.set_alpha(0.2)
        ax_line.set_zorder(2)
    if not visible:
        # Back to default
        ax_line.set_visible(True)
        ax_line.set_zorder(2)
        legend_line.set_alpha(1.0)
    fig.canvas.draw()

def calcImpedanceCurve(filename, ax, resistance, csv_delimiter=','):
    xz = []
    yz = []
    csvfile = open(filename, newline='')
    c = csv.reader(csvfile, delimiter=csv_delimiter)
    nrows = 0
    zmin = 0
    zmax = 0
    for row in c:
        try:
            xf = float(row[0])
            yf = float(row[1])
            xz.append(xf)
            yz.append(yf)
            if nrows == 0:
                zmin = yf
                zmax = yf
            if yf < zmin:
                zmin = yf
            if yf > zmax:
                zmax = yf
            nrows = nrows + 1
        except ValueError as ve:
            print( 'Ignoring: ', row, 'in ' , filename)
    csvfile.close()

    length = len(yz)
    normalize = (resistance+zmin)/zmin
    for i in range(length):
        yz[i] = 20 * np.log10(yz[i]/(resistance+yz[i]) * normalize)
    # Define Impedance EQ
    zeq = interpolate.interp1d(xz, yz, fill_value='extrapolate', assume_sorted=True)
    # show impedance EQ curve
    (line, ) = ax.plot(xz, yz, '-', lw=1.5, label='EQ by impedance ('+ str(resistance) +' Ohm source)')
    lines.append(line)
    return zeq

# Draw given CSV file frequency response
def drawCurve(filename, ax, alignmin, alignmax, isref, csv_delimiter=',', xref = None, yref = None, biquads = None, hidepeq = True, smooth = -1, smoothstr = '', smootheonly = False):
    #  X/Y data to be drawn 
    x = []
    y = []

    # Alignment calculation
    minalignDistance = 1000000
    alignOffset = 0
    alignCount = 0

    # Read CSV file
    csvfile = open(filename, newline='')
    c = csv.reader(csvfile, delimiter=csv_delimiter)
    if xref != None:
        xreflen = len(xref)
    nrows = 0
    for row in c:
        try:
            xf = float(row[0])
            yf = float(row[1])
            if xref != None:
                # Compensate values according to reference curve
                if (nrows < xreflen) and (xf == xref[nrows]):
                    # Simple fast match found => use it to save time
                    yf = yf - yref[nrows]
                else:
                    compindex = np.searchsorted(xref,xf)
                    if compindex >= xreflen:
                        # Out of xrange of reference curve (value too big) => skip data point
                        continue
                    if xref[compindex] == xf:
                        # Exact match in reference curve found => use its value
                        yf = yf - yref[compindex]
                    else:
                        if compindex > 0:
                            # Use linear interpolation of reference curve 
                            yf = yf - (((yref[compindex] - yref[compindex-1])/(xref[compindex] - xref[compindex-1]) * (xf-xref[compindex-1])) + yref[compindex-1])
                        else:
                            # Out of xrange of reference curve (value too small) => skip data point
                            continue
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
            nrows = nrows + 1
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

    # Smooth data
    if smooth > 0 and not isref :
        freq_steps = []
        for i in range(1, len(x)):
            freq_steps.append(x[i] / x[i - 1])
        freq_step_size = sum(freq_steps) / len(freq_steps)
        window_size = round(np.log(2 ** (smooth)) / np.log(freq_step_size))

        window_size_octave = round(np.log(2 ** 1.0) / np.log(freq_step_size))
        # Highest octave obove initial frequency in data set
        check_octave = math.floor(len(x)/window_size_octave)
        # Check in frequency matches with expected logarithmic scaling
        check_error = x[check_octave * window_size_octave] / (2 **check_octave * x[0])
        if check_error > 1.2 or check_error < 0.8:
            # Data not in logrithmic frequency scale => create new data set in logarithmic scale with similar length to apply smoothing
            f = interpolate.interp1d(x, y)
            freq = x[0]
            freq_step_size = np.power(x[len(x)-1]/x[0],1/len(x))
            x_smoothed = []
            y_smoothed = []
            while freq <= x[len(x)-1]:
                x_smoothed.append(freq)
                y_smoothed.append(f(freq))
                freq *= freq_step_size
            window_size = round(np.log(2 ** (smooth)) / np.log(freq_step_size))
        else:
            # Data already have logarithmic frequency scale
            x_smoothed = x
            y_smoothed = y

        if(window_size > 1):
            # Smooth curve using Savitzky-Golay filter of calculated window size, run it from bottom to top and vice versa
            y_smoothed = savgol_filter(y_smoothed, window_size, 1, mode='nearest')
            y_smoothed = np.flip(y_smoothed)
            y_smoothed = savgol_filter(y_smoothed, window_size, 1, mode='nearest')
            y_smoothed = np.flip(y_smoothed)
        # Show smoothed curve
        (line, ) = ax.plot(x_smoothed, y_smoothed, '-', lw=1.5, label=os.path.basename(filename)+' ('+ smoothstr + ' oct smoothed)')
        lines.append(line)
        if zeq != None:
            yz = y_smoothed
            length = len(y_smoothed)
            for i in range(length):
                yz[i] += zeq(x[i])
            # Show impedance equalized smoothed curve
            (line, ) = ax.plot(x_smoothed, yz, '-', lw=1.5, label=os.path.basename(filename)+' (Impedance equalized, ' + smoothstr + ' oct smoothed)')
            lines.append(line)
        if biquads != None:
            # Apply biquad PEQ  to smoothed curve
            length = len(y_smoothed)
            for i in range(length):
                for b in biquads:
                    y_smoothed[i] = y_smoothed[i] + b.log_result(x_smoothed[i])
            # Show peq equalized smoothed curve
            (line, ) = ax.plot(x_smoothed, y_smoothed, '-', lw=1.5, label=os.path.basename(filename)+' (Equalized, ' + smoothstr + ' oct smoothed)')
            lines.append(line)

    # Show PEQ
    if not hidepeq:
        ypeq = []
        length = len(y)
        for i in range(length):
            ypeq.append(0)
            for b in biquads:
                ypeq[i] = ypeq[i] + b.log_result(x[i])
        (line, ) = ax.plot(x, ypeq, '-', lw=1.5, label='Equalizer')
        lines.append(line)

    if smooth > 0 and smootheonly:
        # Don't show raw curve(s)
        return

    # Draw graph
    if isref:
        # Show reference curve
        (line, ) = ax.plot(x, y, '--k', lw=1.5, label=os.path.basename(filename))
        lines.append(line)
    else:
        # Show curve
        (line, ) = ax.plot(x, y, '-', lw=1.5, label=os.path.basename(filename))
        lines.append(line)
        if zeq != None:
            yz = y
            length = len(y)
            for i in range(length):
                yz[i] += zeq(x[i])
            # Show impedance equalized curve
            (line, ) = ax.plot(x, yz, '-', lw=1.5, label=os.path.basename(filename)+' (Impedance equalized)')
            lines.append(line)

        if biquads != None:
            # Apply biquad PEQ
            length = len(y)
            for i in range(length):
                for b in biquads:
                    y[i] = y[i] + b.log_result(x[i])
            # Show peq equalized curve
            (line, ) = ax.plot(x, y, '-', lw=1.5, label=os.path.basename(filename)+' (Equalized)')
            lines.append(line)


# Parse command line
parser = argparse.ArgumentParser(prog='FreqRespGraph',
                                 description='''
FreqRespGraph can plot single or multiple frequency response graphs given as CSV data files in a single graph.
X and Y Axis limit can be configured. Data can be aligned to 0dB at a given frequency or frequency range. In
addition a reference curve can be specified. Filter settings for a parametric equalizer can be specified to
additionally plot the equalizer response and curve(s) equalized by it. Curves can be smoothed by a given
fraction of an octave using a Savitzky-Golay filter with first order polynom. The CSV data files needs to
contain 2 rows with frequency and SPL. Additionally an impedance curve and amplifier inner resistance can
be specified to calculate the effect on the frequency response.
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
parser.add_argument('--compensate', action='store_true', help='Compensate according to given reference curve, default off')
parser.add_argument('--title', nargs='?', default='', help='Set graph title, default off')
parser.add_argument('--peq', nargs='*', default='', help='Apply given PEQ settings, format for each filter is PEAK|LOWSHELF|HIGHSHELF|LOWPASS|HIGHPASS|BANDPASS|NOTCH,<Freq>,<Q>,<Gain>, default none')
parser.add_argument('--fpeq', nargs='?', type=float, default='48000', help='Sampling frequency used to simulate PEQ, default 48000')
parser.add_argument('--hidepeq', action='store_true', help='Hide equalizer curve')
parser.add_argument('--smooth', nargs='?', default='-1', help='Smooth curves according to given fraction of an octave, e.g. 1/12, 0.5 or 1, default off')
parser.add_argument('--smoothonly', action='store_true', help='Only show smoothed curves')
parser.add_argument('--zeq_file', nargs='?', default='', help='CSV filename with impedance data to calculate EQ due to impedance change, requires zeq_r')
parser.add_argument('--zeq_r', nargs='?', type=float, default='-1', help='Inner resistance of amplifier')
parser.add_argument('--zeq_csvdelimiter', nargs='?', default=',', help='Delimiter character used in impedance data CSV file, default ","')
parser.add_argument('--csvdelimiter', nargs='?', default=',', help='Delimiter character used in CSV files, default ","')
parser.add_argument('--files', nargs='*',  required=True, help='CSV filenames to be plotted (supports filename wildcards)')
args = parser.parse_args()

try:
    smooth = float(eval(args.smooth))
except:
    print( 'Invalid smooth value: ' , args.smooth)
    print( 'Expected numerical expression, e.g 1, 0.33 or 1/12')
    exit(1)
    
biquads = []
for p in args.peq:
    biquad_args = p.split(',')
    if len(biquad_args) == 4:
        try:
            biquads.append(bq.Biquad(bq.Biquad.__dict__[biquad_args[0]], float(biquad_args[1]), args.fpeq, float(biquad_args[2]), float(biquad_args[3])))
        except (ValueError, KeyError) as ve:
            print( 'Invalid PEQ: ' , p)
            print( 'Expected format: PEAK|LOWSHELF|HIGHSHELF|LOWPASS|HIGHPASS|BANDPASS|NOTCH,<Freq>,<Q>,<Gain>')
            exit(1)
    else:
        print( 'Invalid PEQ: ' , p)
        print( 'Expected format: PEAK|LOWSHELF|HIGHSHELF|LOWPASS|HIGHPASS|BANDPASS|NOTCH,<Freq>,<Q>,<Gain>')
        exit(1)
if len(biquads) == 0:
    biquads = None
    args.hidepeq = True

print (args )
# Initialize layout
fig, ax = plt.subplots(figsize = (9, 6))

# No reference curve
xref = None
yref = None
if args.refcurve != '' and args.compensate:
    #  Read reference curve data for compensation
    xref = []
    yref = []
    csvfile = open(args.refcurve, newline='')
    c = csv.reader(csvfile)
    for row in c:
        try:
            xf = float(row[0])
            yf = float(row[1])
            xref.append(xf)
            yref.append(yf)
        except ValueError as ve:
            print( 'Ignoring: ', row, 'in ' , args.refcurve)
    csvfile.close()

# Draw curve for each given CSV
lines = []
if args.zeq_r > 0 and args.zeq_file != '' :
    zeq = calcImpedanceCurve(args.zeq_file, ax, args.zeq_r, args.zeq_csvdelimiter)

for filepattern in args.files:
    files = glob.glob(filepattern)
    for file in files:
        drawCurve(file, ax, args.alignmin, args.alignmax, False,  args.csvdelimiter, xref, yref, biquads, args.hidepeq, smooth, args.smooth, args.smoothonly)
        args.hidepeq = True

# Draw referance curve if given
if args.refcurve != '':
    drawCurve(args.refcurve, ax, args.alignmin, args.alignmax, True,  args.csvdelimiter, xref, yref)

# Draw Legend if not disabled
if not args.nolegend:
    leg=ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize='xx-small', draggable=True)
    map_legend_to_ax = {}  # Will map legend lines to original lines.
    pickradius = 5  # Points (Pt). How close the click needs to be to trigger an event.
    for legend_line, ax_line in zip(leg.get_lines(), lines):
        legend_line.set_picker(pickradius)  # Enable picking on the legend line.
        map_legend_to_ax[legend_line] = ax_line
    fig.canvas.mpl_connect('pick_event', on_pick)


# Set logarithmic scale on the x axis
ax.set_xscale("log");

# Set Axis limits
ax.set_xlim(args.xmin,args.xmax)
ax.set_ylim(args.ymin,args.ymax)

# Set X Axis major and minor ticks
formatter = LogFormatter()
ax.xaxis.set_major_formatter(formatter)
formatter2 = FuncFormatter(myformatter)
ax.xaxis.set_minor_formatter(formatter2)


# Set Axis labels
ax.set_xlabel('Frequency [Hz]')
if args.refcurve != '' and args.compensate:
    ylabel = 'Compensated SPL [dB]'
else:
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
