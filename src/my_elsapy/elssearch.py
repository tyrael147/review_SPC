"""The search module of elsapy.
    Additional resources:
    * https://github.com/ElsevierDev/elsapy
    * https://dev.elsevier.com
    * https://api.elsevier.com"""

from . import log_util
from urllib.parse import quote_plus as url_encode
import pandas as pd, json
from .utils import recast_df
from tqdm import tqdm
logger = log_util.get_logger(__name__)
# class bcolors:
#     HEADER = '\033[95m'
#     OKBLUE = '\033[94m'
#     OKCYAN = '\033[96m'
#     OKGREEN = '\033[92m'
#     WARNING = '\033[93m'
#     FAIL = '\033[91m'
#     ENDC = '\033[0m'
#     BOLD = '\033[1m'
#     UNDERLINE = '\033[4m'


class ElsSearch():
    """Represents a search to one of the search indexes accessible
         through api.elsevier.com. Returns True if successful; else, False."""

    # static / class variables
    _base_url = u'https://api.elsevier.com/content/search/'
    _cursored_indexes = [
        'scopus',
    ]

    def __init__(self, query, index):
        """Initializes a search object with a query and target index."""
        self.query = query
        self.index = index
        self._cursor_supported = (index in self._cursored_indexes)
        self._uri = self._base_url + self.index + '?query=' + url_encode(
                self.query) +'&'+'view=COMPLETE'#+'&'+'cursor=*'
        self.results_df = pd.DataFrame()

    # properties
    @property
    def query(self):
        """Gets the search query"""
        return self._query

    @query.setter
    def query(self, query):
        """Sets the search query"""
        self._query = query

    @property
    def index(self):
        """Gets the label of the index targeted by the search"""
        return self._index

    @index.setter
    def index(self, index):
        """Sets the label of the index targeted by the search"""
        self._index = index

    @property
    def results(self):
        """Gets the results for the search"""
        return self._results

    @property
    def tot_num_res(self):
        """Gets the total number of results that exist in the index for
            this query. This number might be larger than can be retrieved
            and stored in a single ElsSearch object (i.e. 5,000)."""
        return self._tot_num_res

    @property
    def num_res(self):
        """Gets the number of results for this query that are stored in the 
            search object. This number might be smaller than the number of 
            results that exist in the index for the query."""
        return len(self.results)

    @property
    def uri(self):
        """Gets the request uri for the search"""
        return self._uri

    def _upper_limit_reached(self):
        """Determines if the upper limit for retrieving results from of the
            search index is reached. Returns True if so, else False. Upper 
            limit is 5,000 for indexes that don't support cursor-based 
            pagination."""
        if self._cursor_supported:
            return False
        else:
            return self.num_res >= 5000

    
    def execute(self, els_client = None, get_all = False):
        """Executes the search. If get_all = False (default), this retrieves
            the default number of results specified for the API. If
            get_all = True, multiple API calls will be made to iteratively get 
            all results for the search, up to a maximum of 5,000."""

        #first response
        api_response = els_client.exec_request(self._uri)
        self._tot_num_res = int(api_response['search-results']['opensearch:totalResults'])
        self._results = api_response['search-results']['entry']

        if self._tot_num_res > 5000 and get_all is True:
            # adds as a cursor parameter to allow +5000 results
            self._uri = self._uri +'&'+'cursor=*'
            print('\033[92m'+'Using cursor for this search')
            # resends a query to obtain new links
            api_response = els_client.exec_request(self._uri)
            self._tot_num_res = int(api_response['search-results']['opensearch:totalResults'])
            self._results = api_response['search-results']['entry']

        if get_all is True:
            # progress bar
            pb = tqdm(total=self.tot_num_res, colour='green')
            while (self.num_res < self.tot_num_res) and not self._upper_limit_reached():
                for e in api_response['search-results']['link']:
                    if e['@ref'] == 'next':
                        next_url = e['@href']
                api_response = els_client.exec_request(next_url)
                self._results += api_response['search-results']['entry']
                pb.update(len(api_response['search-results']['entry']))
            else:
                logger.info(f'Search is finished')
                pb.update(len(api_response['search-results']['entry']))
        with open('dump.json', 'w') as f:
            f.write(json.dumps(self._results))
        self.results_df = recast_df(pd.DataFrame(self._results))

    def hasAllResults(self):
        """Returns true if the search object has retrieved all results for the
            query from the index (i.e. num_res equals tot_num_res)."""
        return (self.num_res is self.tot_num_res)
