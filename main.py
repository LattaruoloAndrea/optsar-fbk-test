import sys, os, time, json
import configparser
import argparse
from datetime import timedelta

# from multiprocessing import freeze_support, set_start_method #some stuff for multi-processing support
from joblib import Parallel, delayed, parallel_backend

main_path = os.path.dirname(os.path.abspath(__file__)) # Retrieve toolbox path
package_path = os.path.join(main_path,'libs') # Generate package path
sys.path.insert(0,package_path) # Insert package path into $PYTHONPATH

from libs.RSdatamanager import filemanager as fm
from libs.RSdatamanager.Sentinel2.S2L2A import L2Atile, getTileList
from libs.RSdatamanager.Landsat.LandsatL2SP import L2SPtile, getL2SPTileList
from libs.ToolboxModules import featurext as m1


#---------------------------------------------------------------------------------------------------#

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


def main(datapath, **kwargs):
    #PREPARE SOME TOOLBOX PARAMETERS
    sensor = kwargs['options'].get('sensor', None)
    tilename = kwargs['options'].get('tilename', None)
    years = kwargs['options'].get('years', None)
    maindir = kwargs['options'].get('maindir', None)
    outpath = kwargs['options'].get('outpath', None)
    deltemp = kwargs['options'].get('deltemp', True)

    module1 = kwargs['module1'].get('run', False)

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


#---------------------------------------------------------------------------------------------------#
if (__name__ == '__main__'):
    #MULTIPROCESSING INITIALIZATION
    # freeze_support() #needed for windows
    # set_start_method('spawn') # because the VSCode debugger (ptvsd) is not fork-safe

    #READ COMMAND ARGUMENTS
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', required=True, metavar='config.ini')
    parser.add_argument('-m1', '--module1', action='store_true', help="run module 1")



    args = parser.parse_args()

    configfile = os.path.abspath(args.config)
    module1 = args.module1



    #READ INITIALIZATION FILE AND SETUP OPTIONS
    config = configparser.ConfigParser()
    config.read(configfile)

    datapath = fm.formatPath(config['Paths']['data_path'])

    options = {
        'sensor': config['Data']['sensor'],
        'tilename': config['Data']['tilename'],
        'years': config['Data']['years'].split(','),
        'maindir': fm.formatPath(config['Paths']['main_dir']),
        'outpath': fm.check_folder(config['Paths']['output_path']),
        'info': False,
        'deltemp': False
    }
    
    m1options = {}
    m1options.update(options)
    m1options['run'] = module1

  
    #CALL MAIN FUNCTION
    main(	datapath = datapath,
            options = options,
			module1 = m1options,
		)
