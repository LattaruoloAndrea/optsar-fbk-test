# REQUIREMENTS

## Python 3.6
* GDAL
* numpy
* h5py
* pandas
* pydtw
* scikit-image
* scikit-learn

To install GDAL on Ubuntu
```
# if installing into virtual environment
sudo apt-get install python3.6-dev
```
```
sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt-get install gdal-bin
sudo apt-get install libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL
```

To install remaining packages from the `requirements.txt` file
```
pip install -r requirements.txt
```



# USAGE

Before running any of the modules, update the `config.ini` file with the correct information regarding data, paths and module parameters considering following example.

[Data] <br />
sensor = S2<br />
tilename = 41WPP<br />
Years = 2015,2016,2017,2018,2019

[Paths] <br />
main_dir = the main directory with all input/outputs<br />
data_path = input data path<br />
output_path = output path where all products will be saved



## Module 1 - Feature Extraction
```
python main.py -c /path/to/config.ini -m1
```

Input: S2 based on acquisitions of 5 years and in particular for the following 5-years periods: 1990-1995, 1995-2000, 2000-2005, 2005-2010, 2010-2015, 2015-2019. Tiling system is identical as the one used for Sentinel-2. <br />
Output: multi-band NDI image for each acquisition date

Extracted features: `(B1-B2)/(B1+B2)`
1. NIR and SWIR1
5. NIR and RED
7. BLUE and SWIR2 



 







