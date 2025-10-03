# utils/graph_visualizer.py
import matplotlib.pyplot as plt
import networkx as nx

def visualize_world_graph(graph: WorldGraph, highlight_current: str = None):
    """
    Рисует граф мира для отладки.
    """
    G = graph.graph
    
    # Позиции узлов
    pos = {node: data['position'] for node, data in G.nodes(data=True)}
    
    # Цвета узлов
    node_colors = []
    for node in G.nodes():
        if node == highlight_current:
            node_colors.append('gold')
        elif G.nodes[node].get('visited'):
            node_colors.append('lightgreen')
        else:
            node_colors.append('lightgray')
    
    # Рисуем
    plt.figure(figsize=(12, 8))
    nx.draw(
        G, pos,
        node_color=node_colors,
        node_size=500,
        with_labels=True,
        labels={node: G.nodes[node]['name'][:10] for node in G.nodes()},
        font_size=8,
        arrows=True
    )
    
    plt.title("World Graph Visualization")
    plt.savefig("world_graph_debug.png", dpi=150)
    plt.close()
    
    print("✅ Граф сохранён в world_graph_debug.png")