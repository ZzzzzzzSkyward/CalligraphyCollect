import re
from cv2 import sort
import urllib3 as urllib
from .revert_index import RevertIndex
import os
from functools import lru_cache
import json
from io import BytesIO
from PIL import Image
from zipfile import ZipFile

###############################
# 配置
jsonnames = ["bei", "taben"]
custom_json_suffix = "json"
###############################
inited = False


def entry(main_func):
    def wrapper(*args, **kwargs):
        # 在被装饰的函数执行前调用main函数
        initialize()
        # 然后执行被装饰的函数
        return main_func(*args, **kwargs)

    return wrapper


rindex = RevertIndex()
database = []


def load_json():
    d = []
    current_path = os.path.dirname(__file__)
    for jsonname in jsonnames:
        path = f"{current_path}/../data/index/{jsonname}.json.zip"
        if not os.path.exists(path):
            print(f"{path} not found")
            continue
        print(f"will load {jsonname}")
        with ZipFile(path) as f:
            data = json.loads(f.read(f"{jsonname}.json").decode("utf-8"))
            d.extend(data)
            print(f"loaded {jsonname}")
    custom_files = os.listdir(f'{current_path}/../data/index')
    sorted(custom_files)
    for file in custom_files:
        if file.endswith(custom_json_suffix):
            path = f"{current_path}/../data/index/{file}"
            with open(path, "rb") as f:
                data = json.loads(f.read().decode("utf-8"))
                if isinstance(data, list):
                    d.extend(data)
                else:
                    d.append(data)
                print(f"loaded {file}")

    return d


def save_custom_json():
    # unused
    current_path = os.path.dirname(__file__)
    custom_json_path = f"{current_path}/../data/index/custom.json.zip"
    with open(custom_json_path, "wb") as f:
        f.write(bytes(json.dumps(database, ensure_ascii=False), encoding="utf-8"))


def initialize():
    global inited
    if inited:
        return
    inited = True
    global rindex, database
    database = load_json()
    for i, item in enumerate(database):
        text = get_text(i)
        if text:
            rindex.add_doc(i, text)
    rindex.sort_index()


@lru_cache(maxsize=10)
def get_single_result(query):
    """
    query: str
    return: list[tuple(id,data,score)]
    """
    return rindex.search(query)


def get_single_result_no_cache(query):
    return rindex.search(query)


result_cache = [0, None, 0]


@entry
def get_result(query, min_match):
    h = " ".join(query) + str(min_match)
    h = hash(h)
    if h == result_cache[0]:
        return {'result': result_cache[1], 'maxhit': result_cache[2]}
    else:
        res, maxhit = find_result(query, min_match)
        result_cache[0] = h
        result_cache[1] = res
        result_cache[2] = maxhit
        return {'result': res, 'maxhit': maxhit}


@entry
def get_text_protocol(id):
    id = int(id)
    if id >= len(database):
        return "not in db"
    else:
        print("get this", id)
        return get_text(id)


def find_result(query, min_match):
    # if the min match count is set, don't perform optimization
    if min_match > 0:
        return find_result_any(query, min_match)
    freq_order = []
    print(query)
    for i in query:
        freq_order.append((rindex.freq.get(i, 0), i))
    freq_order.sort(key=lambda x: x[0])
    if len(freq_order) == 0:
        return []
    original_data = rindex.data
    res = get_single_result(freq_order[0][1])
    print(f"searching {freq_order[0][1]} got {len(res)}")
    for pair in freq_order[1:]:
        if len(res) == 0:
            break
        q = pair[1]
        rindex.data = {id: data for id, data, score in res}
        res = get_single_result_no_cache(q)
        print(f"searching {pair[1]} got {len(res)}")
    rindex.data = original_data
    if len(res) == 0:
        # fallback
        return find_result_any(query, min_match)
    return postprocess(res, query), len(query)


def find_result_any(query, min_match):
    results = {}
    hits = {}
    for q in query:
        res = get_single_result(q)
        for id, data, score in res:
            if id not in results:
                results[id] = [data]
                hits[id] = [1, score]
            else:
                results[id].append(data)
                hits[id][0] += 1
                hits[id][1] += score
        print(f"fb searching {q} got {len(results)}")
    # find the max hit
    maxhit = 0
    for id, hit in hits.items():
        if hit[0] > maxhit:
            maxhit = hit[0]
    # select items with max hit
    if min_match > 0:
        maxhit = min(min_match, maxhit)
    res = []
    for id, hit in hits.items():
        if hit[0] == maxhit:
            data = results[id]
            score = hit[1]
            res.append([id, data, score])

    return postprocess(res, query), maxhit


select_keys = ["name", "owner"]


def postprocess(res, query):
    result = []
    for id, data, score in res:
        d = {}
        raw = database[id]
        for k in select_keys:
            v = raw.get(k, None)
            if v:
                d[k] = v
        d["sw"] = get_text(id)
        result.append(
            {"id": id, "data": d, "score": score,
                "char": get_image_query(id, query)}
        )
    result.sort(key=lambda x: x["score"], reverse=True)
    return result


@entry
def get_image(id, char):
    img_urls = []
    d = database[id]
    if not d:
        print(f"no such entry {id}")
        return img_urls
    detail = d.get("detail")
    if not detail:
        print(f"no detail for {id}")
        return img_urls
    detail = detail[0]
    for img_id, d in enumerate(detail):
        char_map = d.get("char")
        if not char_map:
            continue
        url = d.get("url")
        name = d.get("name")
        text = d.get("text")
        iimg_id = d.get("id")
        fulltext = "".join([char.get("char", "#") for char in char_map])
        index = 0
        l = len(fulltext)
        while index >= 0 and index < l:
            index = fulltext.find(char, index)
            if index >= 0:
                img_urls.append(
                    f"api/get_char_image?id={id}&index={index}&img_id={img_id}"
                )
                index += 1

    return img_urls


header_template = {
    "Host": "ldbk.bnu.edu.cn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
    "Accept-Language": "zh-CN,zh-TW;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Sec-GPC": "1",
    "Referer": "https://ldbk.bnu.edu.cn/",
    "Connection": "keep-alive",
    "Cookie": "JSESSIONID=1A4AB3238954E5BAB7A3F46B38BFF919",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=5, i",
}


def generate_header(url):
    return header_template


reverse_hash = {}


def fetch_full_image(url_or_hash):
    raw_url = reverse_hash.get(url_or_hash, url_or_hash)
    print("fetching ", url_or_hash, "->", raw_url)
    try:
        if "http" in raw_url:
            image = fetch_from_server(raw_url)
        else:
            image = Image.open(raw_url)
        return image
    except Exception as e:
        print(e)
        return None


@lru_cache(maxsize=128)
def req(url):
    content = urllib.request(
        "GET", url, headers=generate_header(url), redirect=True, timeout=5
    )
    content = content.data
    return content


def fetch_from_server(raw_url):
    content = req(raw_url)
    image = Image.open(BytesIO(content))
    return image


def generate_clip_url(url):
    h = hash(url)
    h_str = str(h)
    if h < 0:
        h_str = "0" + h_str[1:]
    reverse_hash[h_str] = url
    return f"api/clip_image/{h_str}.png"


def clip_single_char(url, pos):
    x, y, x1, y1 = pos
    w = x1 - x
    h = y1 - y
    image_url = generate_clip_url(url)
    return f"{image_url}?x={x}&y={y}&w={w}&h={h}"


@entry
def get_clipped_image(url, x, y, w, h):
    image = fetch_full_image(url)
    buffered = BytesIO()
    if not image:
        return None
    try:
        cropped = image.crop((x, y, x + w, y + h))
        cropped.save(buffered, format="PNG")
        cropped.close()
    except Exception as e:
        print("cannot crop image", url, x, y, w, h, image.width, image.height)
        raise e
        return None
    buffered.seek(0)
    return buffered


@entry
def get_clipped_char_image(id, img_id, index):
    if id >= len(database):
        return None
    data = database[id]
    if not data:
        return None
    detail = data.get("detail", [])
    if len(detail) > 0 and type(detail[0]) is list:
        detail = detail[0]
    if not detail:
        return None
    if len(detail) <= img_id:
        print(f"No such image with id {id}-{img_id}")
        return None
    detail = detail[img_id]
    char_map = detail.get("char")
    if not char_map:
        return None
    url = detail.get("url")
    if not url:
        return None
    if type(url) is list:
        url = url[0]
    try:
        x, y, x1, y1 = char_map[index]["pos"]
        w = x1 - x
        h = y1 - y
        assert w > 0 and h > 0
    except Exception as e:
        print(e)
        print(char_map[index])
        return None
    return get_clipped_image(url, x, y, w, h)


def get_text(id):
    data = database[id]
    text = data.get("sw2", None)
    if not text:
        text = data.get("sw", None)
    if not text:
        return None
    return text


@entry
def get_image_query(id, query):
    if id >= len(database):
        return None
    text = get_text(id) or ""
    found_phrases = []
    for q in query:
        normal = rindex.is_string_chinese(q)
        if normal:
            if q in text:
                found_phrases.append(q)
        else:
            result = re.findall(q, text, flags=re.MULTILINE)
            found_phrases.extend(result)

    # print("found phrases:", found_phrases)
    chars_map = {}
    result = []
    for phrase in found_phrases:
        for c in phrase:
            if c not in chars_map:
                chars_map[c] = True
                r = get_image(id, c)
                if r:
                    result.append({"char": c, "urls": r})
    return result


@entry
def get_entry():
    res = []
    for i, d in enumerate(database):
        entry = {}
        entry["id"] = i
        entry["name"] = d.get("name", "")
        entry["owner"] = d.get("owner", "")
        entry["wenti"] = d.get("wentiText", "")
        res.append(entry)
    return res


@entry
def get_full_image(id):
    if id >= len(database):
        return
    data = database[id]
    details = data.get('detail', [])[0]
    if not details:
        return
    urls = []
    for i, d in enumerate(details):
        if d.get('url'):
            urls.append(f"api/full_image?id={id}&img_id={i}")
    return urls


@entry
def get_noclip_image(id, img_id):
    if id >= len(database):
        return None
    data = database[id]
    details = data.get('detail', [])[0]
    if not details:
        print("no detail", id)
        return None
    if img_id >= len(details):
        print("no img_id", id, img_id)
        return None
    detail = details[img_id]
    url = detail.get("url")
    if not url:
        print("no url", id, img_id)
        return None
    if type(url) is list:
        url = url[0]
    image = fetch_full_image(url)
    if not image:
        print("no image", id, img_id)
        return None
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image.close()
    buffered.seek(0)
    return buffered


class apis:
    @staticmethod
    def get_image(*args, **kwargs):
        return get_image(*args, **kwargs)

    @staticmethod
    def get_text(*args, **kwargs):
        return get_text(*args, **kwargs)

    @staticmethod
    def get_entry(*args, **kwargs):
        return get_entry(*args, **kwargs)

    @staticmethod
    def get_full_image(*args, **kwargs):
        return get_full_image(*args, **kwargs)

    @staticmethod
    def get_noclip_image(*args, **kwargs):
        return get_noclip_image(*args, **kwargs)

    @staticmethod
    def get_image_query(*args, **kwargs):
        return get_image_query(*args, **kwargs)

    @staticmethod
    def get_clipped_char_image(*args, **kwargs):
        return get_clipped_char_image(*args, **kwargs)

    @staticmethod
    def get_clipped_image(*args, **kwargs):
        return get_clipped_image(*args, **kwargs)

    @staticmethod
    def get_text_protocol(*args, **kwargs):
        return get_text_protocol(*args, **kwargs)

    @staticmethod
    def get_result(*args, **kwargs):
        return get_result(*args, **kwargs)
