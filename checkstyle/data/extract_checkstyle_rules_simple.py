# parse_checkstyle_metadata.py
import xml.etree.ElementTree as ET
import json
import os
import glob
import re
from typing import List, Dict, Any, Optional


class CheckstyleMetadataParser:
    """解析Checkstyle元数据XML文件"""

    def __init__(self):
        self.rules = []
        self.categories = set()

    def parse_directory(self, checks_dir: str) -> List[Dict]:
        """解析目录下的所有XML文件"""

        if not os.path.exists(checks_dir):
            raise FileNotFoundError(f"目录不存在: {checks_dir}")

        xml_files = glob.glob(os.path.join(checks_dir, "**/*.xml"), recursive=True)
        print(f"找到 {len(xml_files)} 个XML文件")

        for i, xml_file in enumerate(xml_files, 1):
            if i % 20 == 0:
                print(f"处理进度: {i}/{len(xml_files)}")

            try:
                self.parse_file(xml_file)
            except Exception as e:
                print(f"解析文件 {xml_file} 失败: {e}")
                continue

        return self.get_rules()

    def parse_file(self, xml_file: str):
        """解析单个XML文件"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 根元素应该是checkstyle-metadata
        if root.tag != 'checkstyle-metadata':
            print(f"警告: {xml_file} 的根元素不是checkstyle-metadata，而是 {root.tag}")

        # 查找所有module元素
        for module in root.findall('module'):
            # 每个module中有一个check元素
            check = module.find('check')
            if check is not None:
                rule = self.parse_check_element(check, xml_file)
                if rule:
                    self.rules.append(rule)

    def parse_check_element(self, check: ET.Element, xml_file: str) -> Optional[Dict]:
        """解析check元素"""

        name = check.get('name')
        fully_qualified_name = check.get('fully-qualified-name')
        parent = check.get('parent')

        if not name:
            return None

        # 提取描述
        description = self.extract_description(check)

        # 提取选项
        options = self.extract_options(check)

        # 提取消息键
        message_keys = self.extract_message_keys(check)

        # 推断类别
        category = self.infer_category(xml_file, name, fully_qualified_name)
        self.categories.add(category)

        rule = {
            'name': name,
            'fully_qualified_name': fully_qualified_name,
            'parent': parent,
            'description': description,
            'options': options,
            'message_keys': message_keys,
            'category': category,
            'source_file': os.path.basename(xml_file)
        }

        return rule

    def extract_description(self, check: ET.Element) -> str:
        """提取和清理描述文本"""
        desc_elem = check.find('description')
        if desc_elem is None or desc_elem.text is None:
            return ""

        # 获取原始描述
        raw_desc = desc_elem.text

        # 清理HTML标签和特殊字符
        cleaned = self.clean_html(raw_desc)

        # 移除多余的空格和换行
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def clean_html(self, text: str) -> str:
        """清理HTML标签"""
        # 移除<div>, <p>等标签
        text = re.sub(r'<div[^>]*>', '', text)
        text = re.sub(r'</div>', '', text)
        text = re.sub(r'<p[^>]*>', '', text)
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<code>', '"', text)
        text = re.sub(r'</code>', '"', text)
        text = re.sub(r'<ul>', '', text)
        text = re.sub(r'</ul>', '', text)
        text = re.sub(r'<li>', '- ', text)
        text = re.sub(r'</li>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)  # 移除所有其他HTML标签

        # 解码HTML实体
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&amp;', '&').replace('&quot;', '"')
        text = text.replace('&#39;', "'").replace('&nbsp;', ' ')

        return text

    def extract_options(self, check: ET.Element) -> List[Dict]:
        """提取选项"""
        options = []

        properties = check.find('properties')
        if properties is None:
            return options

        for prop in properties.findall('property'):
            option = {
                'name': prop.get('name'),
                'type': prop.get('type'),
                'default_value': prop.get('default-value'),
                'description': ''
            }

            # 提取选项描述
            desc_elem = prop.find('description')
            if desc_elem is not None and desc_elem.text:
                option['description'] = desc_elem.text.strip()

            # 只保留有名称的选项
            if option['name']:
                options.append(option)

        return options

    def extract_message_keys(self, check: ET.Element) -> List[str]:
        """提取消息键"""
        message_keys = []

        keys_elem = check.find('message-keys')
        if keys_elem is None:
            return message_keys

        for key_elem in keys_elem.findall('message-key'):
            key = key_elem.get('key')
            if key:
                message_keys.append(key)

        return message_keys

    def infer_category(self, xml_file: str, rule_name: str, fqn: str) -> str:
        """推断规则类别"""

        # 从文件路径推断
        path_lower = xml_file.lower()

        category_map = [
            ('annotation', ['annotation']),
            ('blocks', ['blocks', 'block', 'brace']),
            ('coding', ['coding', 'todo', 'comment', 'final']),
            ('design', ['design', 'dependency', 'cyclic']),
            ('header', ['header']),
            ('imports', ['imports', 'import']),
            ('indentation', ['indentation', 'indent']),
            ('javadoc', ['javadoc']),
            ('metrics', ['metrics', 'complexity', 'npath', 'cyclomatic']),
            ('modifier', ['modifier']),
            ('naming', ['naming', 'name']),
            ('regexp', ['regexp', 'regex']),
            ('sizes', ['sizes', 'size', 'length', 'count']),
            ('whitespace', ['whitespace', 'whitespace', 'space'])
        ]

        for category, keywords in category_map:
            for keyword in keywords:
                if keyword in path_lower:
                    return category

        # 检查目录名
        dirs = xml_file.split(os.sep)
        for dir_name in dirs:
            dir_lower = dir_name.lower()
            for category, keywords in category_map:
                for keyword in keywords:
                    if keyword == dir_lower:
                        return category

        # 根据规则名推断
        rule_lower = rule_name.lower()
        if 'annotation' in rule_lower:
            return 'annotation'
        elif 'brace' in rule_lower or 'block' in rule_lower:
            return 'blocks'
        elif 'import' in rule_lower:
            return 'imports'
        elif 'javadoc' in rule_lower or 'javadoc' in rule_lower:
            return 'javadoc'
        elif 'name' in rule_lower or 'naming' in rule_lower:
            return 'naming'
        elif 'length' in rule_lower or 'size' in rule_lower:
            return 'sizes'
        elif 'whitespace' in rule_lower or 'space' in rule_lower:
            return 'whitespace'
        elif 'complexity' in rule_lower:
            return 'metrics'
        elif 'final' in rule_lower or 'modifier' in rule_lower:
            return 'modifier'

        return 'miscellaneous'

    def get_rules(self) -> List[Dict]:
        """获取所有规则（去重并排序）"""
        # 按名称去重
        unique_rules = {}
        for rule in self.rules:
            name = rule['name']
            if name not in unique_rules:
                unique_rules[name] = rule
            else:
                # 合并信息（保留更完整的信息）
                existing = unique_rules[name]
                for key in ['description', 'options', 'message_keys']:
                    if not existing[key] and rule[key]:
                        existing[key] = rule[key]

        # 转换为列表并排序
        rules_list = list(unique_rules.values())
        rules_list.sort(key=lambda x: x['name'].lower())

        return rules_list

    def generate_statistics(self, rules: List[Dict]):
        """生成统计信息"""
        print("\n" + "=" * 60)
        print("规则提取统计")
        print("=" * 60)

        print(f"总规则数: {len(rules)}")

        # 类别统计
        categories = {}
        for rule in rules:
            cat = rule['category']
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n类别分布:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat:15s}: {count:3d} 个规则")

        # 选项统计
        rules_with_options = sum(1 for rule in rules if rule['options'])
        total_options = sum(len(rule['options']) for rule in rules)

        print(f"\n选项统计:")
        print(f"  有配置选项的规则: {rules_with_options}")
        print(f"  总选项数: {total_options}")

        # 父模块统计
        parents = {}
        for rule in rules:
            parent = rule.get('parent', 'Unknown')
            parents[parent] = parents.get(parent, 0) + 1

        print(f"\n父模块分布:")
        for parent, count in sorted(parents.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {parent:40s}: {count:3d} 个规则")

        return {
            'total_rules': len(rules),
            'categories': categories,
            'rules_with_options': rules_with_options,
            'total_options': total_options,
            'parents': parents
        }


def save_rules(rules: List[Dict], output_file: str = "checkstyle_rules.json"):
    """保存规则到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

    print(f"\n已保存 {len(rules)} 个规则到 {output_file}")


def save_simplified_rules(rules: List[Dict], output_file: str = "checkstyle_rules_simple.json"):
    """保存简化版本的规则（适合CLI工具）"""
    simplified = []

    for rule in rules:
        simple_rule = {
            'name': rule['name'],
            'description': rule['description'][:200] if rule['description'] else '',
            'category': rule['category'],
            'options': []
        }

        for option in rule['options']:
            simple_option = {
                'name': option['name'],
                'type': option['type'],
                'default': option.get('default_value'),
                'description': option['description'][:100] if option['description'] else ''
            }
            simple_rule['options'].append(simple_option)

        simplified.append(simple_rule)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(simplified, f, indent=2, ensure_ascii=False)

    print(f"已保存简化版本到 {output_file}")


def print_examples(rules: List[Dict], count: int = 10):
    """打印规则示例"""
    print(f"\n前{count}个规则示例:")
    print("-" * 80)

    for i, rule in enumerate(rules[:count]):
        desc = rule['description']
        if len(desc) > 60:
            desc = desc[:57] + "..."

        options_count = len(rule['options'])
        category = rule['category']

        print(f"{i + 1:2d}. {rule['name']:30s} | 类别: {category:12s} | 选项: {options_count:2d}")
        print(f"    描述: {desc}")

        if rule['options']:
            for opt in rule['options'][:2]:  # 最多显示2个选项
                opt_desc = opt['description']
                if len(opt_desc) > 40:
                    opt_desc = opt_desc[:37] + "..."
                print(
                    f"    选项: {opt['name']:20s} ({opt['type']:10s}) = {opt.get('default_value', 'N/A'):10s} - {opt_desc}")
        print()


def main():
    # 设置checks目录路径
    checks_dir = "checkstyle/src/main/resources/com/puppycrawl/tools/checkstyle/meta/checks"

    if not os.path.exists(checks_dir):
        print(f"错误: 目录不存在: {checks_dir}")
        print("请确保在checkstyle项目根目录下运行此脚本")
        return

    print("开始解析Checkstyle元数据文件...")
    print(f"目录: {checks_dir}")
    print("=" * 60)

    # 创建解析器
    parser = CheckstyleMetadataParser()

    # 解析目录
    rules = parser.parse_directory(checks_dir)

    if not rules:
        print("未解析到任何规则")
        return

    # 生成统计
    stats = parser.generate_statistics(rules)

    # 打印示例
    print_examples(rules, 10)

    # 保存完整规则
    save_rules(rules, "checkstyle_rules_complete.json")

    # 保存简化版本
    save_simplified_rules(rules, "checkstyle_rules_simple.json")

    # 生成按类别分割的文件
    save_rules_by_category(rules)

    print("\n" + "=" * 60)
    print("解析完成!")
    print("=" * 60)


def save_rules_by_category(rules: List[Dict]):
    """按类别保存规则"""
    os.makedirs("checkstyle_rules_by_category", exist_ok=True)

    # 按类别分组
    categories = {}
    for rule in rules:
        cat = rule['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rule)

    # 保存每个类别的规则
    for cat, rule_list in categories.items():
        # 清理类别名用于文件名
        safe_cat = re.sub(r'[^a-zA-Z0-9]', '_', cat)
        output_file = f"checkstyle_rules_by_category/{safe_cat}.json"

        # 排序
        rule_list.sort(key=lambda x: x['name'].lower())

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rule_list, f, indent=2, ensure_ascii=False)

        print(f"  已保存类别 '{cat}' 的 {len(rule_list)} 个规则到 {output_file}")


if __name__ == "__main__":
    main()