#!/usr/bin/env python


import networkx as nx


def readGraph(file="data/graph_subset.txt"):
    
    
    G=nx.complete_graph(736)
    
    datafile = open(file,"r")
    lines = (line.rstrip('\r\n') for line in datafile)
    n=0
    for line in lines:
        arr=line.split(' ')
        white=arr[1]
        black=arr[0]
        
        G.add_edge(white, black)
            
    return G


if __name__ == '__main__':
    import networkx as nx


    G=readGraph()

    ngames=G.number_of_edges()
    nplayers=G.number_of_nodes()

    #print("Loaded %d chess games between %d players\n"\
    #               % (ngames,nplayers))

    score = nx.adamic_adar_index(G,[(646,2)])
    for a,b,c in score:
        print(str(a) + "," + str(b) + "," + str(c))
     
    #score = nx.adamic_adar_index(G)
    #for a,b,c in score:
    #    if (c>0):
    #        print(str(a) + "," + str(b) + "," + str(c))
        
    
