import os
import numpy as np
from osgeo import gdal, ogr
from shapely.geometry import mapping, Polygon
from libs.RSdatamanager import filemanager as fm
from libs.RSdatamanager.Landsat.Landsatimage import Landsatimg

#---------------------------------------------------------------------------------------------------#
# Landsat_L2SP Image
class LandsatL2SPimg(Landsatimg):

    def read_Landsat_L2SP(self, filepath, temppath):
        features = {}

        fnames = []
        for _, _, filenames in os.walk(filepath):
            for f in filenames:
                if (f.endswith('.TIF')) or (f.endswith('.tif')) :
                    fnames.append(f)

        #READ EACH SELECTED BAND and QA_PIXEL
        bandnames = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']

        for fn in fnames:
            if 'QA_PIXEL' in fn:
                fp = fm.joinpath(filepath, fn)
                features['QA_PIXEL'] = fp
            else:
                band = fn.split('.')[0]
                band = band.split('_')[-1]
                if band in bandnames:
                    fp = fm.joinpath(filepath, fn)
                    features[band] = fp
        
        self._populate(features, temppath)
        if self.flag():
            self._getmask()
            self._savemetadata()
            self.flag(False)
        
        return self


#---------------------------------------------------------------------------------------------------#
# Landsat_L2SP Time Series 
class LandsatL2SPts:
    
    def __init__(self, temppath=None, filepaths=None):
        self._metadata = {}

        if temppath:
            self._metadata['temppath'] = temppath
            self._ts = []
            
            #POPULATE TS
            totimg = len(filepaths)
            for idx,fp in enumerate(filepaths):
                print('Reading image %i/%i   ' %((idx+1), totimg) , end='\r')
                #READ AND APPEND IMAGE
                img = LandsatL2SPimg().read_Landsat_L2SP(fp, temppath)
                self._ts.append(img)
            print('\nReading image: DONE!')


    #LIST SPECIFIC METHODS
    def __len__(self):
        return len(self._ts)

    def __getitem__(self, key):
        return self._ts[key]
        
    def append(self, img):
        if type(img) is LandsatL2SPimg:            
            self._ts.append(img)
        else:
            raise Exception('Type Error: non-LandsatL2SPimg type was passed!')

    
    #LIST SORTING METHODS
    def sort(self, ts=None):
        if (ts==None):
            ts = self._ts
        ts.sort(key= self._sortKey)

    def sorted(self, reference):
        sl = sorted(self._list, key=lambda x:self.euclideandate(reference, x))
        return sl

    def _sortKey(self, e):
        return e.date(ordinal=True)

    def euclideandate(self, ref, img):
        refdate = ref.date(ordinal=True)
        imgdate = img.date(ordinal=True)
        return abs(refdate-imgdate)

    
    #METHODS RETURNING CLASS INFORMATION
    def tile(self):
        return self[0]._metadata['tile']

    def temppath(self):
        return self._metadata['temppath']
    
    def getdays(self, firstday=None):
        ts = self._ts
        self.sort(ts)
        if firstday:
            firstday = fm.string2ordinal(firstday) - 1
        else:
            firstday = ( ts[0].date() ).toordinal() - 1
        days = [(f.date().toordinal() - firstday) for f in ts]

        return np.array(days)

    def find(self, **kwargs):
        options = {}.fromkeys(['year', 'month','day','month','hour','minute','second'])
        options.update( kwargs )

        results = self._ts
        if options['year']: 
            results = [f for f in results if (f.date().year==options['year'])]
        if options['month']: 
            results = [f for f in results if (f.date().month==options['month'])]
        if options['day']: 
            results = [f for f in results if (f.date().day==options['day'])]
        if options['hour']: 
            results = [f for f in results if (f.date().hour==options['hour'])]
        if options['minute']: 
            results = [f for f in results if (f.date().minute==options['minute'])]
        if options['second']: 
            results = [f for f in results if (f.date().second==options['second'])]
        
        return results

    def getyear(self, year, option='default', buffer=None, fmt="%Y%m%d"):
        if (option=='default'):
            start = fm.string2ordinal(str(year) + '0101', fmt)
            end = fm.string2ordinal(str(year) + '1231', fmt)
        if (option=='farming'):
            y = str( int(year)-1 )
            start = fm.string2ordinal(str(y) + '1111', fmt)
            end = fm.string2ordinal(str(year) + '1110', fmt)
        if buffer:
            start -= buffer
            end += buffer

        TS = LandsatL2SPts()
        TS._metadata.update(self._metadata)  
        TS._ts = [f for f in self._ts if ((f.date(ordinal=True)>=start) & (f.date(ordinal=True)<=end))]
        
        return TS, fm.ordinal2string(start), fm.ordinal2string(end)

#--------------------------------------------------------------------------------------------#
    #METHODS FOR DATA MANIPULATION
    def cropdataset_E(self, savepath):
        """
        In order to properly crop images belonging to the same TS, follow this example: 
            sp = fm.check_folder(datapath,"CROPPED")

            tile.gettimeseries().cropdataset(projection=projection, geoTransform=geoTransform, savepath=sp)
        """
        ts = self._ts
        totimg = len(ts)
        f_left = np.zeros((totimg))
        f_right = np.zeros((totimg))
        f_up = np.zeros((totimg))
        f_low = np.zeros((totimg))
        for idx,fp in enumerate(ts):
            filepath = ts[idx].featurepath('B02')
            info =  gdal.Info(filepath, format='json')
            info_coordinates = info['cornerCoordinates']
            upperLeft = info_coordinates['upperLeft']
            lowerLeft = info_coordinates['lowerLeft']
            upperRight = info_coordinates['upperRight']
            lowerRight = info_coordinates['lowerRight']
            X1 = upperLeft[0]
            X2 = upperLeft[1]

            Y1 = lowerLeft[0]
            Y2 = lowerLeft[1]

            Z1 = upperRight[0]
            Z2 = upperRight[1]

            T1 = lowerRight[0]
            T2 = lowerRight[1]

            f_left[idx] = X1 
            f_right[idx] = Z1
            f_up[idx] = X2
            f_low[idx] = Y2

        Xmin = max(f_left)
        Xmax = min(f_right)
        Ymin = min(f_up)
        Ymax = max(f_low)
        cornerCoordinates = [Xmin,Ymin,Xmax,Ymax]
         

        #ROOT SAVEPATH
        if (savepath==None):
            savepath = os.path.split(self.temppath())[0]
        #name = '_cropped'
        #savepath = fm.check_folder(savepath, name)        

        #CROP IMAGE-FEATURES
        totimg = len(self)
        resolution = self._ts[0].resolution()
        for idx,img in enumerate(self):
            print('Cropping %i/%i     '%((idx+1),totimg), end='\r')
            root = img.featurepath('B01')
            root = os.path.split(root)[0] 
            name = os.path.split(root)[1]
            sp = fm.check_folder(savepath, name)
            ftdict = img.featurepath()
            temppath = self.temppath()
            for _,path in ftdict.items():
                fm.cropGeoTIFF_E(cornerCoordinates, path, sp, temppath, resolution=resolution)
                
                #detele data
                name = os.path.split( path )[1]
                name = name.split('.')[0]
                name += '.tif' 
                tpath = fm.joinpath(temppath, name) 
                os.remove(tpath)  

 
#---------------------------------------------------------------------------------------------------#
# Landsat_L2SP Tile Time Series 
class L2SPtile:
    """
    This object populates and manages the entire TS for a given tile.
    Indexing allows to return the appropriate TS
    """
    
    def __init__(self, temppath, filepaths):
        #SETUP BASIC METADATA
        self._metadataconstructor(temppath, filepaths)         

        #INITILIZE TS
        self._metadata['ts'] = LandsatL2SPts(self.temppath(), filepaths)
        self._metadata['ts'].sort()
     
    def _metadataconstructor(self, temppath, filepaths):
        self._metadata = {
                        'tile': 'None',
                        'temppath': None,
                        'ts': LandsatL2SPts(),
                        'duplicates': None
                        }
        #GET TILE
        if (len(filepaths)>0):
            fp = filepaths[0]
            filename = os.path.split(fp)[1]
            self._metadata['tile'] = _gettile(filename) 
        
        #GET TEMPPATH
        self._metadata['temppath'] = fm.check_folder(temppath, 'numpy')


    #LIST SPECIFIC METHODS
    def __len__(self):
        return len(self.gettimeseries())

    def __getitem__(self, key):
        return self.gettimeseries()[key]


    #METHODS RETURNING CLASS INFORMATION
    def temppath(self):
        return self._metadata['temppath']


    def tile(self):
        return self._metadata['tile']   
    
    def gettimeseries(self, **kwargs):        
        year = kwargs.get('year', None)
        option = kwargs.get('option', 'default')
        buffer = kwargs.get('buffer', None)
        fmt = kwargs.get('fmt', "%Y%m%d")        

        ts = self._metadata['ts']
        if year:
            ts, start, end = ts.getyear(year, option, buffer, fmt)
            return ts, start, end
        else:
            return ts


#---------------------------------------------------------------------------------------------------#
def getL2SPTileList(datapath):
    #GET ALL FILEPATHS
    filepaths = []
    for rootname, dirnames, _ in os.walk(datapath):
        for f in dirnames:
            if (('LC08_L2SP' in f) and (len(f)==40)):
                fp = fm.joinpath(rootname, f)
                filepaths.append(fp)
            if (('LE07_L2SP' in f) and (len(f)==40)):
                fp = fm.joinpath(rootname, f)
                filepaths.append(fp)  

    #SORT ALL FILEPATHS IN THE RESPECTIVE TILES
    tiledict = {}
    for fp in filepaths:
        filename = os.path.split(fp)[1]
        tile = _gettile(filename)
        if tile not in tiledict.keys():
            tiledict[tile] = []
        tiledict[tile].append(fp)

    for tile in tiledict.keys():
        print("Tile-%s has been added!" %(tile) ) 

    return tiledict

def _gettile(filename):
    # Naming convention: LXSS_LLLL_PPPRRR_YYYYMMDD_yyyymmdd_CC_TX

    info = filename.split('_')      # split filename
    tile = info[2]                  # get WRS path and row (PPPRRR)

    return tile