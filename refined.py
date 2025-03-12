import os
import json
from py2neo import Graph, Node


class HeritageGraph:
    def __init__(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(cur_dir, 'data/heritage_1.json')
        self.g = Graph("bolt://localhost:7687", auth=("neo4j", "Your password"))  # 请替换为您的实际密码

    '''读取文件'''
    def read_nodes(self):
        heritage_sites = set()
        categories = set()
        criteria_set = set()
        dynasty_set = set()
        cultures = set()
        links_set = set()

        heritage_infos = []  # 保存遗产的详细信息

        # 关系
        rels_category = []  # 记录与Category的关系
        rels_criteria = []  # 记录与Criteria的关系
        rels_dynasty = []  # 记录与Dynasty的关系
        rels_culture = []  # 记录与Culture的关系
        rels_link = []  # 记录与Link的关系

        with open(self.data_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            for data in data_list:
                self.process_heritage_data(
                    data, heritage_sites, categories, criteria_set, dynasty_set, cultures, links_set,
                    heritage_infos, rels_category, rels_criteria, rels_dynasty, rels_culture,
                    rels_link
                )

        return (heritage_sites, categories, criteria_set, dynasty_set, cultures, links_set,
                heritage_infos, rels_category, rels_criteria, rels_dynasty, rels_culture, rels_link)

    def process_heritage_data(self, data, heritage_sites, categories, criteria_set, dynasty_set,
                              cultures, links_set, heritage_infos, rels_category, rels_criteria,
                              rels_dynasty, rels_culture, rels_link):
        heritage_dict = {}
        name = data.get('Name', '')
        heritage_dict['name'] = name
        heritage_sites.add(name)

        # 添加类别（Category）
        category = data.get('Category of property', '')
        if category:
            if isinstance(category, list):
                for cat in category:
                    categories.add(cat)
                    rels_category.append([name, cat])
            else:
                categories.add(category)
                rels_category.append([name, category])

        # 添加标准（Criteria）
        criteria = data.get('Criteria', '')
        if criteria:
            criteria_items = criteria.strip('()').split(')(')
            for criterion in criteria_items:
                criteria_set.add(criterion)
                rels_criteria.append([name, criterion])

        # 添加朝代（Dynasty）
        dynasties_in_data = data.get('Dynasty', [])
        if isinstance(dynasties_in_data, list):
            for dynasty in dynasties_in_data:
                dynasty_set.add(dynasty)
                rels_dynasty.append([name, dynasty])
        elif isinstance(dynasties_in_data, str):
            dynasty_set.add(dynasties_in_data)
            rels_dynasty.append([name, dynasties_in_data])

        # 添加文化（Culture）
        culture = data.get('Culture', [])
        if isinstance(culture, list):
            for c in culture:
                cultures.add(c)
                rels_culture.append([name, c])
        elif isinstance(culture, str):
            cultures.add(culture)
            rels_culture.append([name, culture])

        # 添加链接（Links）
        links_in_data = data.get('Links', [])
        for link in links_in_data:
            links_set.add(link)
            rels_link.append([name, link])

        heritage_dict.update({
            'danger': data.get('Danger', []),
            'construction_time': data.get('Construction time', ''),
            'integrity': data.get('Integrity', ''),
            'authenticity': data.get('Authenticity', ''),
            'protection_and_management': data.get('Protection and management requirements', ''),
            'myths_and_books': data.get('Myths and books', []),
            'accessible': data.get('Accessible', ''),
            'culture': data.get('Culture', ''),
            'links': links_in_data,
        })

        heritage_infos.append(heritage_dict)

    '''创建节点'''
    def create_node(self, label, nodes):
        for count, node_name in enumerate(nodes, start=1):
            node = Node(label, name=node_name)
            self.g.create(node)
            print(f"Created {label} node {count}: {node_name}")

    '''创建遗产地节点'''
    def create_heritage_nodes(self, heritage_infos):
        for count, heritage_dict in enumerate(heritage_infos, start=1):
            node = Node(
                "HeritageSite",
                name=heritage_dict['name'],
                danger=heritage_dict['danger'],
                construction_time=heritage_dict['construction_time'],
                integrity=heritage_dict['integrity'],
                authenticity=heritage_dict['authenticity'],
                protection_and_management=heritage_dict['protection_and_management'],
                myths_and_books=heritage_dict['myths_and_books'],
                accessible=heritage_dict['accessible'],
                culture=heritage_dict['culture'],
                links=heritage_dict['links']
            )
            self.g.create(node)
            print(f"Created HeritageSite node {count}: {heritage_dict['name']}")

    '''创建知识图谱实体节点类型schema'''
    def create_graphnodes(self):
        data = self.read_nodes()
        (heritage_sites, categories, criteria_set, dynasty_set, cultures, links_set, heritage_infos,
         rels_category, rels_criteria, rels_dynasty, rels_culture, rels_link) = data

        self.create_heritage_nodes(heritage_infos)
        self.create_node('Category', categories)
        self.create_node('Criteria', criteria_set)
        self.create_node('Dynasty', dynasty_set)
        self.create_node('Culture', cultures)
        self.create_node('Link', links_set)

    '''创建实体关系边'''
    def create_graphrels(self):
        data = self.read_nodes()
        (heritage_sites, categories, criteria_set, dynasty_set, cultures, links_set, heritage_infos,
         rels_category, rels_criteria, rels_dynasty, rels_culture, rels_link) = data

        # 创建与遗产地相关的关系
        self.create_relationship('HeritageSite', 'Category', rels_category, "HAS_CATEGORY", "Heritage Category")
        self.create_relationship('HeritageSite', 'Criteria', rels_criteria, "HAS_CRITERIA", "Heritage Criteria")
        self.create_relationship('HeritageSite', 'Dynasty', rels_dynasty, "HAS_DYNASTY", "Heritage Dynasty")
        self.create_relationship('HeritageSite', 'Culture', rels_culture, "HAS_CULTURE", "Heritage Culture")
        self.create_relationship('HeritageSite', 'Link', rels_link, "HAS_LINK", "Heritage Link")

    '''创建实体关联边'''
    def create_relationship(self, start_node_label, end_node_label, edges, rel_type, rel_name):
        # 确保所有关系边都被正确地转化为字符串
        unique_edges = {"###".join(map(str, edge)) for edge in edges}
        for count, edge in enumerate(unique_edges, start=1):
            p, q = edge.split('###')
            query = f"""
            MATCH (p:{start_node_label} {{name: $p_name}}), (q:{end_node_label} {{name: $q_name}})
            CREATE (p)-[rel:{rel_type} {{name: $rel_name}}]->(q)
            """
            parameters = {'p_name': p, 'q_name': q, 'rel_name': rel_name}
            try:
                self.g.run(query, parameters)
                print(f"Created relationship {rel_type} ({count}/{len(unique_edges)}): {p} -> {q}")
            except Exception as e:
                print(f"Failed to create relationship {rel_type} ({count}/{len(unique_edges)}): {p} -> {q}, Error: {e}")


if __name__ == '__main__':
    handler = HeritageGraph()
    handler.create_graphnodes()
    handler.create_graphrels()
