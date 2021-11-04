# -*- coding: utf-8 -*-
"""

@author: larrea
"""

from .my_elsapy.elsclient import ElsClient
from .my_elsapy.elsdoc import AbsDoc
from .my_elsapy.elssearch import ElsSearch
import json
import logging
from tqdm import tqdm
import pandas as pd
logging.basicConfig(filename='logs.log', filemode="w", level=logging.INFO)
logger = logging.getLogger('searcher')


class Searcher(object):
    """
    Creates a searcher object using elsapy (https://github.com/ElsevierDev/elsapy)

    Attributes:
    config_path (str): path of the json file containing authentication keys
    """

    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        con_file = open(self.config_path)
        config = json.load(con_file)
        con_file.close()

        self.client = ElsClient(config["apikey"])
        self.client.inst_token = config["insttoken"]

    def get_doc(self, scopus_id=None):
        scp_doc = AbsDoc(scp_id=scopus_id)
        scp_doc.read(self.client)
        scp_doc.write()
        return scp_doc

    def get_ids(self, scopus_id=None):
        scp_doc = self.get_doc(scopus_id)
        ids = []
        for x in (
            scp_doc.data.get("item")
            .get("bibrecord")
            .get("tail")
            .get("bibliography")
            .get("reference")
        ):
            ids.append(x.get("ref-info").get("refd-itemidlist").get("itemid"))
        return ids

    def get_bib(self, scopus_id=None):
        """
        Extracts bibliographic information of the scopus_id article
        Args:
            scopus_id (int or string): 11 digits number used as identifier of the article. Is the same as the 11 last digits of EID

        Returns:
            references_listlike (dictionary): Data of articles cited stored in lists to convert easily to pandas df.
            It has the form {'x_id':(list), 'tit': (list), 'year': (list), 'source': (list)}
            references (dictionary): Data structured as a dictionary.
            It has keys and values similar to: x_id:{'x_id':(int), 'tit': (str), 'year': (int)}

        """
        scp_doc = self.get_doc(scopus_id)
        # Head data (article citation information)
        try:
            bibrecord = scp_doc.data.get("item").get("bibrecord")
            abstract = bibrecord.get("head").get("abstracts")
            title = bibrecord.get("head").get("citation-title")

            # Year has different keys deppending on the file
            try:
                year_pub = (
                bibrecord.get("head").get("source").get("publicationdate").get("year")
            )
            except:
                logger.error(f'There is no "publicationdate" key, looking for "publicationyear"')
                try:
                    year_pub = (
                        bibrecord.get("head").get("source").get("publicationyear").get("@first")
                    )
                except:
                    year_pub = "None"

            eid = scp_doc.data.get('coredata').get('eid')
            cited_by = int(scp_doc.data.get('coredata').get('citedby-count'))
            journal = bibrecord.get("head").get("source").get("sourcetitle")

            # Tail data (references from the article)
            # for references_listlike
            x_id = []
            tit = []
            year = []
            source = []
            references = {}
            try:
                for reference in bibrecord.get("tail").get("bibliography").get("reference"):

                    item_id = reference.get("ref-info").get("refd-itemidlist").get("itemid")

                    if type(item_id) == dict:
                        item_id = [item_id]
                        logger.info(f'item_id in dict form for article {item_id}')
                    _scopus_id = [
                        id_type["$"] for id_type in item_id if id_type["@idtype"] == "SGR"
                    ] # using list comprehension to avoid for loop

                    #Some references do not have years
                    try:
                        _year = reference.get("ref-info").get("ref-publicationyear").get("@first")
                    except:
                        logger.error(f'{scopus_id} has no year, "NA" used instead')
                        _year = "None"
                    _source = reference.get("ref-info").get("ref-sourcetitle")

                    # TODO: Revise is "ref-titletext" is the only key for a title
                    _title = (
                        reference.get("ref-info").get("ref-title").get("ref-titletext")
                        if reference.get("ref-info").get("ref-title") is not None
                        else "None"
                    )

                    references[_scopus_id[0]] = {
                        "scopus_id": _scopus_id[0],
                        "title": _title,
                        "year": _year,
                        "journal": _source,
                    }

                    x_id.append(_scopus_id[0])
                    tit.append(_title)
                    year.append(_year)
                    source.append(_source)

                references_listlike = {
                    "scopus_id": x_id,
                    "title": tit,
                    "year": year,
                    "source": source,
                }
            except:
                logger.info(f'The article {title} does not have references')
                references_listlike = "None"
                references = 'NA'
        except:
            return {
            "scopus_id": str(scopus_id),
            "title": 'NA',
            "abstract": 'NA',
            "journal": 'NA',
            "year": 'NA',
            "eid": 'NA',
            "cited_by": 'NA',
            # 'references_listlike': references_listlike, #is not used at the moment, confuses the user
            "references": 'NA'
        }
        return {
            "scopus_id": str(scopus_id),
            "title": title,
            "abstract": abstract,
            "journal": journal,
            "year": year_pub,
            "eid": eid,
            "cited_by": cited_by,
            # 'references_listlike': references_listlike, #is not used at the moment, confuses the user
            "references": references,
        }

    def get_search(self, query, get_all=False, database="scopus"):

        docs_srch = ElsSearch(query, database)
        docs_srch.execute(self.client, get_all=get_all)
        return docs_srch

    def search_query(self, query, get_all=False, database="scopus"):
        """
        Args:
            query (str):  string with query (website alike)
            get_all (bool): Indicates if more API calls will be made until completing all the elements of the search.
            An API call delivers 25 elements by default. Max. num of calls is 5000
            database: 'scopus' by default
        Returns:
            query_dict (dict): Has scopus_id as key and a dict of properties as value
        """
        query_dict = {}
        query_df = pd.DataFrame()
        docs_srch = self.get_search(query, get_all=get_all, database=database)
        for idx in range(docs_srch.results_df.shape[0]):

            scopus_id = docs_srch.results_df["dc:identifier"][idx][-11:]

            result_dict = {
                "scopus_id": scopus_id,
                "title": docs_srch.results_df["dc:title"][idx],
                "abstract": docs_srch.results_df["dc:description"][idx],
                "year": docs_srch.results_df["prism:coverDate"][idx].year,
                "keywords": docs_srch.results_df["authkeywords"][idx],
                "journal": docs_srch.results_df["prism:publicationName"][idx],
                "doi": docs_srch.results_df["prism:doi"][idx]
            }

            query_df = query_df.append(result_dict, ignore_index=True)
            query_dict[scopus_id] = result_dict

        return query_dict, query_df

    def build_db(self, query, get_all=False):
        """
        Uses scopus_id to make an API to request bibliography
        Args:
            query (str): List containing scopus_ids as strings
            get_all (bool): True if multiple API calls are desired until complete the full
            list of results. 25 articles per call, max 5000 calls.
        Returns:
            query_db (dict): Dictionary that has scopus_id as key and properties as value
        """
        query_dict = self.search_query(query, get_all=get_all)
        query_db = {}
        for scopus_id in tqdm(list(query_dict.keys())):
            query_db[scopus_id] = self.get_bib(scopus_id)
        return query_db
