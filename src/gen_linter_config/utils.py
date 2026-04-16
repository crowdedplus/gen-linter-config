"""通用工具函数"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any

def load_config(file_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif file_path.endswith('.xml'):
        tree = ET.parse(file_path)
        root = tree.getroot()
        # 将XML转换为字典的逻辑
        return xml_to_dict(root)
    else:
        raise ValueError("不支持的配置文件格式")

def save_config(config: Dict[str, Any], file_path: str):
    """保存配置文件"""
    if file_path.endswith('.json'):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError("不支持的配置文件格式")

def xml_to_dict(element):
    """XML转换为字典"""
    # 实现XML到字典的转换逻辑
    pass