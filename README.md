# FreqRespGraph

FreqRespGraph is a simple tool to plot and compare frequency response measurement data from CSV files. It is written in [Python 3](https://www.python.org/) using [matplotlib](https://matplotlib.org/).

# Installation
1. Download and install Python 3.X on your system: [https://www.python.org/downloads/](https://www.python.org/downloads/)
1. Open a shell / command prompt and install matplotlib: `pip install matplotlib`
1. Optionally install git command line client: [https://github.com/git-guides/install-git](https://github.com/git-guides/install-git)
1. Download FreqRespGraph:
   - Clone git repository: `git clone https://github.com/rwhomeaudio/FreqRespGraph` or
   - Download ZIP archive from [https://github.com/rwhomeaudio/FreqRespGraph](https://github.com/rwhomeaudio/FreqRespGraph) using "Code->Download ZIP" button.
1. Test the installation by running: `python FreqRespGraph.py -h`
# Usage
```
python FreqRespGraph.py -h
usage: FreqRespGraph [-h] [--ymin [YMIN]] [--ymax [YMAX]] [--xmin [XMIN]] [--xmax [XMAX]] [--alignmin [ALIGNMIN]]
                     [--alignmax [ALIGNMAX]] [--hidealignment] [--refcurve [REFCURVE]] [--nolegend] [--title [TITLE]]
                     --files [FILES ...]

FreqRespGraph can plot single or multiple frequency response graphs given as CSV data files in a single graph. X and Y Axis
limit can be configured. Data can be aligned to 0dB at a given frequency or frequency range. In addition a reference curve
can be specified. The CSV data files needs to contain 2 rows with frequency and SPL.

options:
  -h, --help            show this help message and exit
  --ymin [YMIN]         Y-Axis minumum, default -30db
  --ymax [YMAX]         Y-Axis maximum, default 20db
  --xmin [XMIN]         X-Axis minumum, default 20Hz
  --xmax [XMAX]         X-Axis maximum, default 20000Hz
  --alignmin [ALIGNMIN]
                        Align Y-Axis at given frequency to 0 dB, default off
  --alignmax [ALIGNMAX]
                        Align Y-Axis at frequency range to 0 dB, default off
  --hidealignment       Do not show aligment arguments in Y-Axis label, default off
  --refcurve [REFCURVE]
                        Plot given CSV file as dotted reference curve, default off
  --nolegend            Do not show curves legend, default off
  --title [TITLE]       Set graph title, default off
  --files [FILES ...]   CSV filenames to be plotted (supports filename wildcards)
  ```
# Examples
The following examples use the headphone measurment and target curves provided by [AutoEq](https://github.com/jaakkopasanen/AutoEq).

1. Show all RTings measurements of Sennheiser over ear headphones (already alighned to 1kHz): `python FreqRespGraph\FreqRespGraph.py --files AutoEq\measurements\Rtings\data\over-ear\Sennheiser*.csv`
![Sennheiser1](./examples/Sennheiser1.JPG)   
3. Show all RTings measurements of Sennheiser over ear headphones aligned to 440Hz): `python FreqRespGraph\FreqRespGraph.py --alignmin 440 --files AutoEq\measurements\Rtings\data\over-ear\Sennheiser*.csv`
![Sennheiser2](./examples/Sennheiser2.JPG) 
5. Since aligning to a single frequency is misleading align to frequency range instead and additionally plot harman target curve: `python FreqRespGraph\FreqRespGraph.py --alignmin 200 --alignmax 2000 --title "All Rtings Sennheiser measurements" --refcurve "AutoEq\targets\Harman over-ear 2018.csv" --title "All Rtings Sennheiser measurements" --files AutoEq\measurements\Rtings\data\over-ear\Sennheiser*.csv`
![Sennheiser3](./examples/Sennheiser3.JPG) 
7. All Rtings measurments without legend: `python FreqRespGraph\FreqRespGraph.py --alignmin 200 --alignmax 2000 --title "All Rtings Sennheiser measurements" --refcurve "AutoEq\targets\Harman over-ear 2018.csv" --nolegend --title "All Rtings measurements" --files AutoEq\measurements\Rtings\data\over-ear\*.csv`
![AllRtings](./examples/AllRtings.JPG) 
9. All Sennheiser HD 650 measurements: `python FreqRespGraph\FreqRespGraph.py --alignmin 200 --alignmax 2000 --title "All Rtings Sennheiser measurements" --refcurve "AutoEq\targets\Harman over-ear 2018.csv" --nolegend --title "All Sennheiser HD 650" --files "AutoEq\measurements\oratory1990\data\over-ear\Sennheiser HD 650.csv" "AutoEq\measurements\Rtings\data\over-ear\Sennheiser HD 650.csv" "AutoEq\measurements\Kuulokenurkka\data\over-ear\Sennheiser HD 650.csv" "AutoEq\measurements\Innerfidelity\data\over-ear\Sennheiser HD 650.csv" "AutoEq\measurements\Headphone.com Legacy\data\over-ear\Sennheiser HD 650.csv""AutoEq\measurements\Headphone.com Legacy\data\over-ear\Sennheiser HD 650 (balanced).csv"`
![SennheiserHD650](./examples/SennheiserHD650.JPG)

# Tips
1. Often the legend on the right side doesn't fit in the plot. You can just disable it using `--nolegend` or adjust the size by using the "right" slider in "Configure subplots" menu.
2. Complex wildcard file patterns could be used. It is implemented using [glob](https://docs.python.org/3/library/glob.html). E.g. something like `--files AutoEq\measurements\*\*\*\Sennheiser*.csv` can be used.
  
