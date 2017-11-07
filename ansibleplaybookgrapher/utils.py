import os
import xml.etree.ElementTree as etree

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

    def __str__(self):
        print(self.graph_dict)


# cdata support https://gist.github.com/zlalanne/5711847
def CDATA(text=None):
    element = etree.Element('![CDATA[')
    element.text = text
    return element


etree._original_serialize_xml = etree._serialize_xml


def _serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == '![CDATA[':
        write("<%s%s]]>" % (elem.tag, elem.text))
        return
    return etree._original_serialize_xml(
        write, elem, qnames, namespaces, short_empty_elements, **kwargs)


etree._serialize_xml = etree._serialize['xml'] = _serialize_xml


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


def insert_javascript_elements(svg_root):
    """
    Insert the required elements needed to run javascript
    :param svg_root:
    :return:
    """
    # jquery tag
    jquery_element = etree.Element("script", attrib={'type': 'text/javascript', 'xlink:href': JQUERY})

    # insert jquery script tag
    svg_root.insert(0, jquery_element)

    # TODO: remove snap if not needed
    snap = _read_data('snap.svg-min.js')
    snap_element = etree.Element('script', attrib={'type': 'text/javascript'})
    snap_element.append(CDATA("\n" + snap))
    svg_root.insert(1, snap_element)

    javascript = _read_data("highlight-hover.js")

    javascript_element = etree.Element('script', attrib={'type': 'text/javascript'})
    javascript_element.append(CDATA("\n" + javascript))

    svg_root.insert(2, javascript_element)


def insert_css_element(svg_root, css_filename):
    """
    Insert css style
    :param css_filename:
    :param svg_root:
    :return:
    """
    style_element = etree.Element("style", attrib={'type': 'text/css'})

    style = _read_data(css_filename)
    style_element.append(CDATA("\n" + style))

    svg_root.insert(2, style_element)


def insert_graph_representation(tree, graph_representation):
    """
    Insert the graph representation in the svg
    :param tree:
    :param graph_representation:
    :return:
    """
    for node, node_edges in graph_representation.graph_dict.items():
        element = tree.find("./ns:g/*[@id='%s']" % node, namespaces={'ns': SVG_NAMESPACE})

        root_subelement = etree.Element('links')

        for e in node_edges:
            root_subelement.append(etree.Element('link', attrib={'target': e}))

        element.append(root_subelement)


def post_process_svg(svg_filename, graph_representation):
    """
    Post process the svg as xml to add the javascript files
    :param graph_representation:
    :param svg_filename:
    :return:
    """
    etree.register_namespace("", SVG_NAMESPACE)
    tree = etree.parse(svg_filename)
    svg_root = tree.getroot()

    svg_root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")  # xlink namespace

    # add an id to the root
    svg_root.set("id", "svg")

    insert_javascript_elements(svg_root)
    insert_css_element(svg_root, "graph.css")

    insert_graph_representation(tree, graph_representation)

    tree.write(svg_filename, xml_declaration=True, encoding="UTF-8")
