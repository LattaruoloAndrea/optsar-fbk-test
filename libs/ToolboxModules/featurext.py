import time

import numpy as np

from libs.RSdatamanager import filemanager as fm

#---------------------------------------------------------------------------------------------------#
def manager(tile, **kwargs):
    #SETUP VARIABLES
    info = kwargs.get('info', True)
    year = kwargs.get('year', None)
    feature = kwargs.get('feature', 0 )
    savepath = fm.check_folder(kwargs.get('savepath', None), 'Features')

    #GET FEATURES
    yearts,_,_ = tile.gettimeseries(year=year, option='default')

    if len(yearts) != 0:
        _feature(yearts, savepath, **kwargs)
     

#---------------------------------------------------------------------------------------------------#
#COMPUTE INDEX  
def _feature(ts, path, **kwargs):

    info = kwargs.get('info',True)
    ts_length = kwargs.get("ts_legth", len(ts) )

    if info:
        print('Extracting features for each image:')
        t_start = time.time()

    #Get some information from data
    height, width = ts[0].feature('B04').shape

    ts = sorted(ts, key=lambda x: x.InvalidPixNum())[0:ts_length]
    totimg = len(ts)
    totfeature = 3
    
    #Compute Index Statistics   
    for idx,img in enumerate(ts):
        if info:        
            print('.. %i/%i      ' % ( (idx+1), totimg ), end='\r' )   
        
        feature = np.empty((height, width, totfeature))
        #Compute Index
        b1 = img.feature('BLUE', dtype=np.float32)
        b1[b1==0] = np.nan
 
        b2 = img.feature('GREEN', dtype=np.float32)
        b2[b2==0] =np.nan

        b3 = img.feature('RED', dtype=np.float32)
        b3[b3==0] = np.nan

        b4 = img.feature('NIR', dtype=np.float32)
        b4[b4==0] = np.nan

        b5 = img.feature('SWIR1', dtype=np.float32)
        b5[b5==0] = np.nan

        b6 = img.feature('SWIR2', dtype=np.float32)
        b6[b6==0] = np.nan



        feature[..., 0]=_ndi(b4,b5)
        feature[..., 1]=_ndi(b4,b3)
        feature[..., 2]=_ndi(b6,b1)

            
        #Manipulate features
        with np.errstate(invalid='ignore'):
            feature[feature>1] = 1
            feature[feature<-1] = -1
        
        #Save features
        geotransform, projection = fm.getGeoTIFFmeta( ts[0].featurepath()['B04'] )

        if img._metadata['time'] != None:
            sp = fm.joinpath(path, str(img._metadata['tile'])+'_'+str(img._metadata['date'])+'T'+str(img._metadata['time'])+'_NDI.tif')
        else:
            sp = fm.joinpath(path, str(img._metadata['tile'])+'_'+str(img._metadata['date'])+'_NDI.tif')
        fm.writeGeoTIFFD(sp, feature, geotransform, projection)
    
    if info:
        t_end = time.time()
        print('\nMODULE 1: extracting features..Took ', (t_end-t_start)/60, 'min')
    

def _ndi(b1,b2):

    denom = b1 + b2        
    nom = (b1-b2)

    denom[denom==0] = 1e-8
    index = nom/denom  

    index[index>1] = 1
    index[index<-1] = -1
    
    return index     
