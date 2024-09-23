import os
import numpy as np
from libs.RSdatamanager import filemanager as fm
from libs.RSdatamanager.satimage import SATimg

class Landsatimg(SATimg):
    
    def __init__(self, features=None, temppath=None):
        #INITIALIZE BASIC METADATA
        super().__init__()
        self._metadata['resolution'] = 30

        #CHECK IF FEATUREPATHS HAVE BEEN PASSED
        if features:
            self._populate(features, temppath)
 
    def _populate(self, features, temppath=None):
        
                #STORE PATHS
        self._storepaths(features)
        
        #GET METADATA FROM FN
        self._getmetadata()
        

        #GET TEMPPATH
        self._gettemppath(temppath)

        if self.flag():
            self._savemetadata()
        else:
            self._loadmetadata()
    
    
    #-----------------------------------------------------------------------------------------------#
    def _getmetadata(self):
        #SMALL REDUNDANT CHECK
        fd = self.featurepath()
        if (len( fd )>0):
            key = next(iter(fd))
            fp = fd[key]
            self._getinfo(fp) 
    
    def _storepaths(self, features):
        for key,path in features.items():
            fn = os.path.split(path)[1]
            info = fn.split('.')[0]
            info = info.split('_')
            self._metadata['landsatsensor'] = info[0]
            ftname = self.translate(key)
            self._metadata['featurepath'][ftname] = path

    
    def _getinfo(self, filepath):
        #GET FILENAME OF A FEATURE         
        fn = os.path.split(filepath)[1]
        
        #PRAPARE LIST OF USEFULL INFORMATION
        info = fn.split('.')[0]
        info = info.split('_')

        #GET BASIC METADATA (Naming convention: LXSS_LLLL_PPPRRR_YYYYMMDD_yyyymmdd_CC_TX)
        self._metadata['tile'] = info[2]
        self._metadata['date'] = info[3]

    
    
    def _gettemppath(self, temppath):
        if (temppath==None):
            features = self.featurepath()
            key = next( iter( features) )
            path = features[key]
            fp = os.path.split(path)[1]
        else:
            fp = fm.joinpath( temppath, self.name() )  
        self._metadata['temppath'] = fm.check_folder(fp)
    

    #-----------------------------------------------------------------------------------------------#
    def _getmask(self):
        """Landsat 8 Quality Assessment:
        https://prd-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/atoms/files/LSDS-1619_Landsat8-C2-L2-ScienceProductGuide-v2.pdf 
        
        MASK-Legend:
        -1:Defective
        -2:NAN
        -3:Clouds
        -4:CloudShadows
        -5:Snow
        """

        img_qa = self.feature('QA_PIXEL', dtype=np.uint16, store=False)

        img_qa_values = np.unique(img_qa)                                   # QA values
        binary_qa_values = []                                               # QA values binary translation
        mask_qa_values = np.zeros(len(img_qa_values), dtype=np.uint8)       # QA corresponding mask values

        for i in range(len(img_qa_values)):
            b = np.binary_repr(img_qa_values[i], width=16)
            binary_qa_values.append(b)
            
            #SNOW
            if b[-6] == '1':
                mask_qa_values[i] = 5
            
            #CLOUD SHADOWS
            if b[-5] == '1' or (b[-11] == '1' and b[-12] == '1'):
                mask_qa_values[i] = 4
            
            #CLOUDS: medium-prob and high-prob cloud and cirrus
            if (b[-3] == '1' or b[-4] == '1' or (b[-9] == '0' and b[-10] == '1') or 
                (b[-9] == '1' and b[-10] == '1') or (b[-15] == '1' and b[-16] == '1')):
                mask_qa_values[i] = 3

            #FILL (NAN)
            if b[-1] == '1':
                mask_qa_values[i] = 2

        #MASK
        height, width = img_qa.shape
        mask = np.zeros( (height,width), dtype=np.uint8 )

        for i in range(len(img_qa_values)):
            layer = (img_qa == img_qa_values[i])
            mask[layer] = mask_qa_values[i]

        self._metadata['invalidpixnum'] = np.count_nonzero(mask)
        self._metadata['nanpixnum'] = np.count_nonzero(mask==2)
        self._metadata['cloudypixnum'] = np.count_nonzero((mask==3) | (mask==4))
        self._metadata['totpixnum'] = height*width

        #SAVE MASK
        fp = fm.joinpath(self.temppath(), 'MASK.npy')
        np.save(fp, mask)

    def InvalidPixNum(self):
        return self._metadata['invalidpixnum']

    def NANPixNum(self):
        return self._metadata['nanpixnum']
    
    def CloudyPixNum(self):
        return self._metadata['cloudypixnum']

    def TotalPixNum(self):
        return self._metadata['totpixnum']
    
  
    #-----------------------------------------------------------------------------------------------#
    #USEFULL TOOLS
    def name(self):
        name = self._metadata['tile'] + '_' + self._metadata['date']
        return name
  
       
    def translate(self, string):

        landsatsensor = self._metadata['landsatsensor']

        if landsatsensor == 'LC08':
            #SETUP Landsat8 DICTIONARY
            dictionary = {}
            dictionary['B01'] = ['B1','b1','B01','b01','Coastal Aerosol','Aerosol','aerosol']
            dictionary['B02'] = ['B2','b2','B02','b02','BLUE','blue']
            dictionary['B03'] = ['B3','b3','B03','b03','GREEN','green']
            dictionary['B04'] = ['B4','b4','B04','b04','RED','red']
            dictionary['B05'] = ['B5','b5','B05','b05','NIR','nir']
            dictionary['B06'] = ['B6','b6','B06','b06','SWIR1','swir1']
            dictionary['B07'] = ['B7','b7','B07','b07','SWIR2','swir2']
            dictionary['B08'] = ['B8','b8','B08','b08','Panchromatic', 'panchromatic']
            dictionary['B09'] = ['B9','b9','B09','b09','Cirrus','cirrus']
            dictionary['B10'] = ['B10','b10','TIRS1']
            dictionary['NDVI'] = ['NDVI','ndvi']
            dictionary['RGB'] = ['RGB','rgb']
            dictionary['MASK'] = ['MASK','mask','Mask']
            dictionary['QA_PIXEL'] = ['QA_PIXEL']
        else:
            #SETUP Landsat7 DICTIONARY
            dictionary = {}
            dictionary['B01'] = ['B1','b1','B01','b01','BLUE','blue']
            dictionary['B02'] = ['B2','b2','B02','b02','GREEN','green']
            dictionary['B03'] = ['B3','b3','B03','b03','RED','red']
            dictionary['B04'] = ['B4','b4','B04','b04','NIR','nir']
            dictionary['B05'] = ['B5','b5','B05','b05','SWIR1','swir1']
            dictionary['B06'] = ['B6','b6','B06','b06','THERMAL','thermal']
            dictionary['B07'] = ['B7','b7','B07','b07','SWIR2','swir2']
            dictionary['B08'] = ['B8','b8','B08','b08','Panchromatic', 'panchromatic']
            dictionary['B09'] = ['B9','b9','B09','b09','Cirrus','cirrus']
            dictionary['B10'] = ['B10','b10','TIRS1']
            dictionary['NDVI'] = ['NDVI','ndvi']
            dictionary['RGB'] = ['RGB','rgb']
            dictionary['MASK'] = ['MASK','mask','Mask']
            dictionary['QA_PIXEL'] = ['QA_PIXEL']

        #SLOW-SEARCH
        for key in list(dictionary.keys()):
            for s in dictionary[key]:
                if s==string:
                    return key
        
        print('SatImage has no band named "',string,'"!')
        return None

    def feature(self, string, **kwargs):
        dtype = kwargs.get('dtype', None)
        name = self.translate(string)
        store = kwargs.get('store', True)

        #MASK-FEATURE IS SPECIAL CASE
        if name=='MASK':
            if self.temppath():
                fp = fm.joinpath(self.temppath(),'MASK.npy')                
                if (os.path.isfile(fp)==False):
                    self._getmask()
                if dtype:
                    matr =  np.load(fp).astype(dtype) #astype raises error if dtype is invalid
                else:
                    matr = np.load(fp)
            else:
                raise IOError('Invalid "temppath": path was not correctly initialized!')
        
        else:
            matr = super().feature(name, dtype=dtype, store=store)

        return matr   
