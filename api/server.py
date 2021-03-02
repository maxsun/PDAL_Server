from flask import Flask, render_template, send_file, jsonify, request
from flask_cors import CORS, cross_origin
import process as P
import os, json
import shutil
from PIL import Image

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def index():
    return 'API is live'


@app.route('/api/input_list')
@cross_origin()
def get_input_list():
    files = []
    for file in os.listdir('data'):
        print(file)
        if '.hsx' in file.lower() or '.laz' in file.lower():
            files.append(file)
    return jsonify(files)


@app.route('/api/info/<filename>')
@cross_origin()
def get_info(filename):
    return jsonify(P.output_metadata[filename])


@app.route('/api/meta')
@cross_origin()
def get_meta():
    return jsonify(P.output_metadata)


@app.route('/api/pipe', methods=['GET', 'POST'])
@cross_origin()
def start_pipeline():
    content = request.json
    spec = content['spec']
    out_fname = None
    if 'output_filename' in content:
        out_fname = content['output_filename']

    P.run_pipeline(content['input_filename'], spec, out_fname)

    return jsonify(content)


@app.route('/api/image/<filename>')
@cross_origin()
def get_image(filename):
    return send_file('output_images/'+ filename, mimetype='image/png')


@app.route('/api/thumbnail/<filename>')
@cross_origin()
def get_thumbnail(filename):
    image = Image.open('output_images/' + filename)
    image.thumbnail((50,50))
    image.save(f'output_images/thumbnail_{filename}')
    return send_file(f'output_images/thumbnail_{filename}', mimetype='image/png')


@app.route('/api/upload', methods=['POST'])
@cross_origin()
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    lower_fname = file.filename.lower()

    if file and P.verify_file(lower_fname):
        filename = file.filename

        P.output_metadata[filename] = {}
        P.save_metadata()

        file.save(os.path.join('./data/', filename))
        return 'success'


@app.route('/api/clear_cache')
@cross_origin()
def clear_cache():
    if os.path.exists('output_images'):
        shutil.rmtree('output_images')

    if os.path.exists('meta.json'):
        os.remove('meta.json')

    os.makedirs('output_images')
    P.output_metadata = {}
    return jsonify({})



app.run(host='0.0.0.0', port=8080, debug=True)