"""
Visualization for knowledge graph

Creates interactive HTML visualizations using vis.js
"""

from pathlib import Path

from gamedatagen.core.knowledge_graph import KnowledgeGraph


def visualize_knowledge_graph(kg: KnowledgeGraph, output_path: Path) -> Path:
    """
    Create interactive knowledge graph visualization

    Args:
        kg: Knowledge graph to visualize
        output_path: Output HTML file path

    Returns:
        Path to generated HTML file
    """
    # Build nodes and edges
    nodes = {}
    edges = []

    for triplet in kg.triplets:
        # Add subject node
        subject_key = f"{triplet.subject.type}:{triplet.subject.id}"
        if subject_key not in nodes:
            nodes[subject_key] = {
                "id": subject_key,
                "label": triplet.subject.id,
                "group": triplet.subject.type,
                "title": f"{triplet.subject.type}: {triplet.subject.id}",
            }

        # Add object node
        object_key = f"{triplet.object.type}:{triplet.object.id}"
        if object_key not in nodes:
            nodes[object_key] = {
                "id": object_key,
                "label": triplet.object.id,
                "group": triplet.object.type,
                "title": f"{triplet.object.type}: {triplet.object.id}",
            }

        # Add edge
        edge = {
            "from": subject_key,
            "to": object_key,
            "label": triplet.predicate,
            "arrows": "to",
            "title": triplet.predicate,
        }

        # Add metadata to edge title if present
        if triplet.metadata:
            metadata_str = ", ".join(
                f"{k}: {v}"
                for k, v in triplet.metadata.model_dump().items()
                if v is not None and k != "custom"
            )
            if metadata_str:
                edge["title"] = f"{triplet.predicate} ({metadata_str})"

        edges.append(edge)

    # Generate HTML with vis.js
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GameDataGen - Knowledge Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        #header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        #stats {{
            background: #34495e;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-around;
        }}
        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid lightgray;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🎮 GameDataGen Knowledge Graph</h1>
        <p>Interactive visualization of entity relationships</p>
    </div>

    <div id="stats">
        <div class="stat">
            <div class="stat-value">{len(nodes)}</div>
            <div class="stat-label">ENTITIES</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(edges)}</div>
            <div class="stat-label">RELATIONSHIPS</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(set(n['group'] for n in nodes.values()))}</div>
            <div class="stat-label">ENTITY TYPES</div>
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({list(nodes.values())});

        var edges = new vis.DataSet({edges});

        var container = document.getElementById("mynetwork");
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            nodes: {{
                shape: 'dot',
                size: 16,
                font: {{
                    size: 12,
                    color: '#000000'
                }},
                borderWidth: 2,
                shadow: true
            }},
            edges: {{
                width: 1,
                shadow: true,
                smooth: {{
                    type: 'continuous'
                }},
                font: {{
                    size: 10,
                    align: 'middle'
                }}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                navigationButtons: true,
                keyboard: true
            }},
            groups: {{
                Quest: {{ color: {{ background: '#3498db', border: '#2980b9' }} }},
                NPC: {{ color: {{ background: '#2ecc71', border: '#27ae60' }} }},
                Item: {{ color: {{ background: '#f39c12', border: '#e67e22' }} }},
                Enemy: {{ color: {{ background: '#e74c3c', border: '#c0392b' }} }},
                Zone: {{ color: {{ background: '#9b59b6', border: '#8e44ad' }} }},
                Event: {{ color: {{ background: '#1abc9c', border: '#16a085' }} }}
            }}
        }};

        var network = new vis.Network(container, data, options);

        network.on("click", function(params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var node = nodes.get(nodeId);
                console.log("Clicked node:", node);
            }}
        }});
    </script>
</body>
</html>
"""

    output_path.write_text(html)
    return output_path
