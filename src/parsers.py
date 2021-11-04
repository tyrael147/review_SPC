# -*- coding: utf-8 -*-
"""
This module provides useful functions to parse a csv generated from scopus to 
avoid bugs from pd.read_csv
@author: larrea
"""
import pandas as pd
import csv



class parser_csv(object):
    """
    This class creates a parser using CSV package. This avoids some issues with the pandas.read_csv parser and sniffer.

    Attributes:
    f_path (str): file path
    db (list): list of lists containing the parsed rows from the f_path
    """

    def __init__(self, f_path, encoding="utf-8-sig"):
        self.f_path = f_path

        csv.field_size_limit(100000000)

        lista = []
        self.db = lista

        with open(f_path, encoding=encoding) as f:
            reader = csv.reader(f)
            for row in reader:
                self.db.append(row)

    def header(self):
        """
        returns a dict containing variable name and column index
        """

        header_dict = {value: index for (index, value) in enumerate(self.db[0])}
        return header_dict

    def scopus_id(self, row=None):
        """
        Selects the 11 last characters from the EID variable (scopus ID)
        returns a string
        """
        return self.db[row][self.header().get('EID')][-11:]

    def title(self, row=None):
        """
        returns a tittle string
        """

        return self.db[row][self.header().get('Title')]

    def source(self, row=None):
        """
        returns a source string
        """

        return self.db[row][self.header().get('Source title')]

    def abstract(self, row=None):
        """
        returns an abstract string
        """
        return self.db[row][self.header().get('Abstract')]

    def to_pandas(self):
        """
        returns a pandas.DataFrame object
        """
        return pd.DataFrame(self.db[1:], columns=self.db[0])
