from graph.state import VideoAudit
from graph.nodes import audit_content_node , Video_indexer_node
from langgraph.graph import StateGraph , END


def create_graph():
    '''
    creates the workflow of the agent from start to finish. The order of how it will be executed.
    '''
    workflow = StateGraph(VideoAudit)

    #defining the nodes
    workflow.add_node("audit_content_node" , audit_content_node)
    workflow.add_node("Video_indexer_node" , Video_indexer_node)

    #building the edges
    workflow.set_entry_point(Video_indexer_node)
    workflow.add_edge(Video_indexer_node , audit_content_node)
    workflow.add_edge(audit_content_node ,END)

    #compiling the graph
    graph = workflow.compile()
    return graph

graph = create_graph()