import os

from lxml import etree

JQUERY = 'https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

_ROOT = os.path.abspath(os.path.dirname(__file__))


def clean_name(name):
    """
    Clean a name for the node, edge...
    :param name:
    :return:
    """
    return name.strip()


def clean_id(identifier):
    """
    Remove special characters from the string
    :param identifier:
    :return:
    """
    chars_to_remove = [' ', '[', ']', ':', '-', ',', '.', '(', ')', '#', '/', '|', '{', '}', '&', '~']
    for c in chars_to_remove:
        identifier = identifier.replace(c, '')
    return identifier


class GraphRepresentation(object):
    """
    A simple structure to represent the link between the node of the graph. It's used during the postprocessing of the svg
    to add these links in order to highlight the nodes and edge on hover.
    """

    def __init__(self, graph_dict=None):
        if graph_dict is None:
            graph_dict = {}
        self.graph_dict = graph_dict

    def add_node(self, node_name):
        if node_name not in self.graph_dict:
            self.graph_dict[node_name] = []

    def add_link(self, node1, node2):
        self.add_node(node1)
        edges = self.graph_dict[node1]
        edges.append(node2)
        self.graph_dict[node1] = edges


def _get_data_absolute_path(path):
    """
    Return the data absolute path
    :param path:
    :return:
    """
    return os.path.join(_ROOT, 'data', path)


def _read_data(filename):
    """
    Read the script and return is as string
    :param filename:
    :return:
    """
    javascript_path = _get_data_absolute_path(filename)

    with open(javascript_path) as javascript:
        return javascript.read()


class PostProcessor(object):
    """
    Post process the svg by adding some javascript and css
    """

    def __init__(self, svg_path, graph_representation):
        self.svg_path = svg_path
        self.graph_representation = graph_representation
        self.tree = etree.parse(svg_path)
        self.root = self.tree.getroot()

        self.root.set('id', 'svg')

    def insert_script_tag(self, index, attrib):
        element_script_tag = etree.Element('script', attrib=attrib)

        self.root.insert(index, element_script_tag)

    def insert_cdata(self, index, tag, attrib, cdata_text):
        element = etree.Element(tag, attrib=attrib)
        element.text = etree.CDATA(cdata_text)

        self.root.insert(index, element)

    def post_process(self):
        # insert jquery
        self.insert_script_tag(0, attrib={'type': 'text/javascript', 'href': JQUERY})

        highlight_script = _read_data("highlight-hover.js")

        self.insert_cdata(1, 'script', attrib={'type': 'text/javascript'}, cdata_text=highlight_script)

        css = _read_data("graph.css")

        self.insert_cdata(2, 'style', attrib={'type': 'text/css'}, cdata_text=css)

        self._insert_graph_representation()

    def write(self):
        self.tree.write(self.svg_path, xml_declaration=True, encoding="UTF-8")

    def _insert_graph_representation(self):
        for node, node_links in self.graph_representation.graph_dict.items():
            # Find the group g with the specified id
            element = self.tree.xpath("./ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})[0]

            root_subelement = etree.Element('links')

            for link in node_links:
                root_subelement.append(etree.Element('link', attrib={'target': link}))

            element.append(root_subelement)
