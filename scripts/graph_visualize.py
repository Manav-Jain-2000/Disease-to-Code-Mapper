import networkx as nx
import matplotlib.pyplot as plt
class ICDcodeNode:
    def __init__(self, icd_code, description, children, parent):
        self.icd_code = icd_code
        self.description = description
        self.children  =  children
        self.parent = parent

    def get_children(self):
        return self.children
    
    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def get_parent(self):
        return self.parent
    
    def set_parent(self,parent):
        self.parent = parent

    def __repr__(self):
        return f'{self.icd_code} - {self.description} -  Children: {[x.icd_code for x in self.children]}'

def build_networkx_graph(root_node):
    """Convert ICDcodeNode tree to NetworkX graph"""
    graph = nx.Graph()

    def add_nodes_edges(node):
        # Add node with its ICD code and description as attributes
        graph.add_node(node.icd_code, description=node.description)

        # Add edges for each child
        for child in node.get_children():
            graph.add_edge(node.icd_code, child.icd_code)
            add_nodes_edges(child)

    add_nodes_edges(root_node)
    return graph

def visualize_large_graph(graph):
    """Visualize NetworkX graph with matplotlib"""
    pos = nx.spring_layout(graph, k=0.1, iterations=100) #spacing between nodes

    plt.figure(figsize=(8.5, 8.5))

    # Draw edges
    nx.draw_networkx_edges(graph, pos, alpha=0.5, width=0.5, edge_color='#888')

    # Draw nodes
    node_sizes = []
    for node in graph.nodes():
        # Size inversely proportional to ICD code length (longer codes are lower in the hierarchy)
        code_length = len(node)
        if '-' in node: #(code is a section/chapter)
            code_length = 1
        node_sizes.append(1 / (code_length + 1) * 2000)  # Scale factor

    nx.draw_networkx_nodes(
        graph, pos, 
        node_size=node_sizes,
        node_color=[len(graph.edges(n)) for n in graph.nodes()],
        cmap=plt.cm.plasma, alpha=0.5
    )

    # Add labels to nodes (ICD codes)
    labels = {node: node for node in graph.nodes()}
    nx.draw_networkx_labels(graph, pos, labels, font_size=8)

    plt.title('ICD Code Hierarchy Visualization', fontsize=16)
    plt.axis('off') 
    plt.tight_layout()
    plt.show()




# Convert to NetworkX graph and visualize
