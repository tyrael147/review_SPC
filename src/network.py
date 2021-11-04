import networkx as nx
from .searcher import Searcher
import copy
import logging
import pandas as pd
from tqdm import tqdm
logger = logging.getLogger(__name__+'network')

class Network_bib(object):
    def __init__(self, query_list, n_layers=1):
        self.n_layers = n_layers
        self.query_list = query_list.copy()
        self.graph = nx.DiGraph()
        self.articles_db = {}
        self._create_graph(self.query_list, self.n_layers)  # updates self.graph and self.db

    def _create_graph(self, query_list, n_layers):
        """
        Args:
            query_list (list): list of scopus_ids as strings
            n_layers (int): number of layers to explore (references of references)
        """
        sr = Searcher("src/config.json")  # initialize the searcher

        articles_list = copy.deepcopy(query_list)
        missing_articles = []
        for layer in tqdm(range(n_layers + 1)):
            if layer == 0:
                missing_articles = articles_list
            else:
                for scopus_id in tqdm(missing_articles):
                    self.articles_db[scopus_id] = sr.get_bib(scopus_id)

                    self.graph.add_node(
                        scopus_id,
                        title=self.articles_db[scopus_id].get("title"),
                        year=self.articles_db[scopus_id].get("year"),
                        journal=self.articles_db[scopus_id].get("journal"),
                    )

                    # If it does not have references then skip this part
                    if self.articles_db[scopus_id]["references"] != 'NA':
                        for scopus_id_ref, properties in self.articles_db[scopus_id][
                            "references"
                        ].items():

                            self.graph.add_node(
                                scopus_id_ref,
                                title=properties.get("title"),
                                year=properties.get("year"),
                                journal=properties.get("journal"),
                            )

                            self.graph.add_edges_from([(scopus_id, scopus_id_ref)])
                    else:
                            logger.info(
                                f'The article {self.articles_db[scopus_id].get("title")} does not have references')

                articles_in_graph = list(self.graph.nodes)
                articles_in_db = list(self.articles_db.keys())
                missing_articles = [article for article in articles_in_graph if article not in articles_in_db]


           # n_layer = upper_layer    # the n+1 layer (suppliers) become consumers for next iteration

        return self.graph


    ## TODO: This function is an unnecessary loop, integrate it with the _create_graph loop
    @property
    def db(self):
        df = pd.DataFrame(columns=['scopus_id','title','abstract','journal','year','cited_by','eid'])
        for scopus_id, properties in self.articles_db.items():
            data_dict = {
                'scopus_id':properties['scopus_id'],
                'title':properties['title'],
                'abstract': properties['abstract'],
                'journal': properties['journal'],
                'year': properties['year'],
                'cited_by': properties['cited_by'],
                'eid': properties['eid']
            }
            df = df.append(data_dict, ignore_index=True)

        return df
