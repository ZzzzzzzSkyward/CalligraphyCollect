import json
import os

def split_json(file_path, max_size_mb):
    max_size_bytes = max_size_mb * 1024 * 1024  # 将MB转换为字节
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)  # 加载整个JSON数组
        file_count = 1
        chunk = []
        chunk_size = 0

        for item in data:
            # 将JSON对象转换为字符串，以便计算其大小
            item_str = json.dumps(item,ensure_ascii=False,separators=(",",":"))
            item_size = len(item_str.encode('utf-8'))
            
            # 如果添加当前项会超过最大文件大小，则写入当前块并开始新的块
            if chunk_size + item_size > max_size_bytes:
                with open(f'{os.path.splitext(file_path)[0]}_{file_count}.json', 'w', encoding='utf-8') as chunk_file:
                    json.dump(chunk, chunk_file, ensure_ascii=False,separators=(",", ":"))
                    file_count += 1
                    chunk = []
                    chunk_size = 0
            
            # 添加当前项到当前块
            chunk.append(item)
            chunk_size += item_size
        
        # 写入最后一个块
        if chunk:
            with open(f'{os.path.splitext(file_path)[0]}_{file_count}.json', 'w', encoding='utf-8') as chunk_file:
                json.dump(chunk, chunk_file, ensure_ascii=False,separators=(",", ":"))

# 使用示例
import sys
file_path = sys.argv[1]  # 替换为你的大JSON文件路径
split_json(file_path, 60)  # 拆分成小于100MB的块