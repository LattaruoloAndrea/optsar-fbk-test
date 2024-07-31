import sys, os, time, json
import configparser
import argparse
from datetime import timedelta
sys.path.append(".")
# from multiprocessing import freeze_support, set_start_method #some stuff for multi-processing support
from joblib import Parallel, delayed, parallel_backend

from libs.RSdatamanager import filemanager as fm
from libs.RSdatamanager.Sentinel2.S2L2A import L2Atile, getTileList
from libs.RSdatamanager.Landsat.LandsatL2SP import L2SPtile, getL2SPTileList
from libs.ToolboxModules import featurext as m1


def tile_reading_1(tileDatapath, maindir, sensor):
    if sensor == 'S2':
        tile = L2Atile(maindir, tileDatapath)
    if sensor == 'Landsat':
        tile = L2SPtile(maindir, tileDatapath)
    return tile


def tile_reading_2(tile, outpath, tilename, year, **kwargs):
    #UPDATE OPTIONS
    name = str(tilename) + '_' + year
    update = {
        'year': year,
        'savepath': fm.check_folder(outpath, name)
    }
    #MODULE 1
    options = kwargs.get('module1',{})
    options.update( update )
    m1.manager(tile, **options)


def parallel_tile_reading(tiledict, maindir, sensor, tile_keys, outpath, tilename, years, **kwargs):
    tiles = Parallel(n_jobs=-1)(delayed(tile_reading_1)(tiledict[k], maindir, sensor) for k in tile_keys)
    Parallel(n_jobs=-1)(delayed(tile_reading_2)(tile, outpath, tilename, year, **kwargs) for tile in tiles for year in years)

def main(project, datapath, options,module1):
    #PREPARE SOME TOOLBOX PARAMETERS
    sensor = options.get('sensor', None)
    tilename = options.get('tilename', None)
    years = options.get('years', None)
    maindir = options.get('maindir', None)
    outpath = options.get('outpath', None)
    deltemp = options.get('deltemp', True)

    with parallel_backend('loky'):
        if (module1):
            logging = {} 
            t_tot = time.time()  
            #READ DATASETS
            if sensor == 'S2':
                tiledict = getTileList(datapath)
            elif sensor == 'Landsat':
                tiledict = getL2SPTileList(datapath)
            else:
                raise IOError('Invalid sensor')
            keys = tiledict.keys()

            parallel_tile_reading(tiledict, maindir, sensor, keys, outpath, tilename, years, **kwargs)

            t_tot = timedelta(seconds=(time.time() - t_tot))     
            print("MOD1 TIME = ", t_tot,flush=True)      
            logging['MODULE 1'] = {'TIME': str(t_tot) }
            with open(fm.joinpath(outpath,"logging_MODULE 1.txt"),'w') as json_file:
                json.dump(logging,json_file)
