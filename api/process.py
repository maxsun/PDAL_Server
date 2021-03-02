import pdal
import os, json
import rasterio
import cmocean
from rasterio.plot import show
import matplotlib.pyplot as plt

plt.rcParams['savefig.dpi'] = 500

output_metadata = {}


def verify_file(fname):
    valid_exts = ['.hsx', '.laz', '.las', '.tif']
    return any([fname.lower().endswith(ext) for ext in valid_exts])


def init_metadata():
    global output_metadata
    if os.path.isfile('meta.json'):
        output_metadata = json.loads(open('meta.json').read())
    else:
        for file in os.listdir('data'):
            if verify_file(file):
                output_metadata[file] = {}


def save_metadata():
    open('meta.json', 'w').write(json.dumps(output_metadata))


def mbinfo(filename):
    return json.loads(os.popen(f'mbinfo -Idata/{filename} -X1').read())


def run_pipeline(input_filename, pipeline_spec, output_filename=None):

    if output_filename is None:
        output_filename = f'out{len(output_metadata)}.png'

    json_spec = '''
    {
        "pipeline":%s
    }
    ''' % (json.dumps(pipeline_spec))


    pipeline = pdal.Pipeline(json_spec)
    count = pipeline.execute()
    arrays = pipeline.arrays
    data = arrays[0]
    metadata = pipeline.metadata
    log = pipeline.log

    print('Read', count, 'points with', len(data.dtype), 'dimensions')
    print('Dimension names are', data.dtype.names)

    # Calculate the bounding box
    minx = None
    miny = None
    maxx = None
    maxy = None

    if '.laz' in input_filename.lower() or '.las' in input_filename.lower():
        pipe_metadata = json.loads(pipeline.metadata)['metadata']
        minx = pipe_metadata['readers.las']['minx']
        miny = pipe_metadata['readers.las']['miny']
        maxx = pipe_metadata['readers.las']['maxx']
        maxy = pipe_metadata['readers.las']['maxy']
    elif '.hsx' in input_filename.lower():
        i = mbinfo(input_filename)
        minx = float(i['limits']['minimum_longitude'])
        miny = float(i['limits']['minimum_latitude'])
        maxx = float(i['limits']['maximum_longitude'])
        maxy = float(i['limits']['maximum_latitude'])


    fig = plt.figure(frameon=False)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')

    DTM = rasterio.open("temp.tif", driver="GTiff")
    show(DTM, ax=ax, cmap=cmocean.cm.deep);
    if not os.path.exists('output_images'):
        os.makedirs('output_images')
    plt.savefig(f'output_images/{output_filename}')


    if input_filename not in output_metadata:
        output_metadata[input_filename] = {}

    output_metadata[input_filename][output_filename] = {
        'filename': output_filename,
        'spec': pipeline_spec,
        'bbox': [[minx, miny], [maxx, maxy]]
    }

    save_metadata()

    return output_filename


init_metadata()
