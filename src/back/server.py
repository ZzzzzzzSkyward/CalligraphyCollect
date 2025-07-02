from os import error
from flask_caching import Cache
from flask_cors import CORS
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template, g
from flask_compress import Compress
from script.utils import apis
import traceback
import re
app = Flask(__name__)
#####################
port = 5012  # 端口号
app.json.ensure_ascii = False  # type: ignore
app.config['COMPRESS_REGISTER'] = False
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 30*60  # 缓存时间（秒）
network_timeout = 60  # 最长网络响应等待时间（秒）
###########################
CORS(app)
compress = Compress(app)
cache = Cache(app)


@app.before_request
def set_timeout():
    g.flask_timeout = network_timeout

# 文件服务器
##############################


@app.route('/')
@app.route('/index')
def serve_index():
    return send_from_directory('dist', 'index.html')
# 默认静态文件目录


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('dist', filename)
############################


# 查询接口路由


def process_query(query, min_match):
    r = apis.get_result(query, min_match)
    result = {
        "result": r['result'],
        "maxhit": r['maxhit'],
    }
    return result

# 查询参数验证函数


def validate_query(query):
    """
    验证查询字符串的合法性

    Args:
        query (str): 输入的查询字符串

    Returns:
        bool: 是否合法
    """
    # 空值检查
    if not query:
        return False

    # 长度限制（例如：1-100字符）
    if len(query) < 1 or len(query) > 100:
        return False

    # 空格拆分
    subquery = query.split(' ')
    valid_subquery = []
    for i in subquery:
        try:
            i = i.strip()
            if len(i) > 0 and re.compile(i):
                valid_subquery.append(i)
        except:
            pass
    return subquery


def error400(msg):
    return jsonify({
        "error": msg,
    }), 400


@app.route('/api/query', methods=['GET'])
@compress.compressed()
def api_query():
    query = request.args.get('q', '')
    min_match = request.args.get('min_match', -1)

    subquery = validate_query(query)
    if not subquery:
        return error400("invalid param: q")
    try:
        min_match = int(min_match)
    except:
        return error400("invalid param: min_match")
    # 处理查询
    try:
        result = process_query(subquery, min_match)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


@app.route('/api/getimage', methods=['GET'])
def api_getimage():
    id = request.args.get('id', '')
    char = request.args.get('char', '')
    valid = len(char) > 0
    try:
        id = int(id)
    except:
        valid = False
    if not valid:
        return jsonify({
            "error": "Invalid query",
        }), 400

    try:
        result = apis.get_image(id, char)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


@app.route('/api/getimages', methods=['GET'])
def api_getimages():
    id = request.args.get('id', '')
    query = request.args.get('query', '')
    subquery = validate_query(query)
    valid = not not subquery
    try:
        id = int(id)
    except:
        valid = False
    if not valid:
        return error400("invalid param")

    try:
        result = apis.get_image_query(id, query)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


@app.route('/api/clip_image', methods=['GET'])
@cache.cached(timeout=3000, query_string=True)
def api_clip_image():
    url = request.args.get('url', '')
    x = request.args.get('x', '')
    y = request.args.get('y', '')
    w = request.args.get('w', '')
    h = request.args.get('h', '')

    valid = url and x and y and w and h
    try:
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
    except:
        valid = False
    if not valid:
        return error400("invalid param")

    try:
        result = apis.get_clipped_image(url, x, y, w, h)
        assert result is not None, "cannot clip image"
        return send_file(result, mimetype="image/png")

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


@app.route('/api/get_text', methods=['GET'])
@cache.cached(timeout=3000, query_string=True)
def api_get_text():
    id = request.args.get('id', 0)
    print("get_text", id)
    t = apis.get_text_protocol(id)
    if t:
        return t
    else:
        return "error"


@app.route('/api/getentry', methods=['GET'])
@compress.compressed()
def api_get_entry():
    try:
        result = apis.get_entry()
        assert result is not None, "cannot get entry"
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


@app.route('/api/get_char_image', methods=['GET'])
@cache.cached(timeout=3000, query_string=True)
def api_get_char_image():
    id = request.args.get('id', '')
    index = request.args.get('index', '')
    img_id = request.args.get('img_id', '')
    valid = True
    try:
        id = int(id)
        index = int(index)
        img_id = int(img_id)
        valid = index >= 0 and id >= 0 and img_id >= 0
    except:
        valid = False
    if not valid:
        return error400("invalid param")

    try:
        result = apis.get_clipped_char_image(id, img_id, index)
        assert result is not None, "cannot clip image"
        return send_file(result, mimetype="image/png")

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500

# 大图


@app.route('/api/get_single_image_urls', methods=['GET'])
@cache.cached(timeout=3000, query_string=True)
def api_get_single_image_urls():
    id = request.args.get('id', '')
    valid = True
    try:
        id = int(id)
        valid = id >= 0
    except:
        valid = False
    if not valid:
        return error400("invalid param")

    try:
        result = apis.get_full_image(id)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500
# 大图


@app.route('/api/full_image', methods=['GET'])
@cache.cached(timeout=3000, query_string=True)
def api_get_full_image():
    id = request.args.get('id', '')
    img_id = request.args.get('img_id', '')
    valid = True
    try:
        id = int(id)
        img_id = int(img_id)
        valid = id >= 0 and img_id >= 0
    except:
        valid = False
    if not valid:
        return error400("invalid param")

    try:
        result = apis.get_noclip_image(id, img_id)
        assert result is not None, "cannot get full sized image"
        return send_file(result, 'image/png')

    except Exception as e:
        return jsonify({
            "error": traceback.format_exc(),
        }), 500


# 主入口
if __name__ == '__main__':
    # 启动服务器，不开启调试模式
    app.run(debug=False, host='0.0.0.0', port=port)
