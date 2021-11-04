import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
import numpy as np
import seaborn as sn
import bibtexparser


df_ctx = pd.read_csv('data/Corpus Explorer.csv')
df_0 = pd.read_csv('data/query_df_0.csv').drop(["Unnamed: 0"], axis=1)
df_1 = pd.read_csv('data/query_df_1.csv').drop(["Unnamed: 0"], axis=1)
df_2 = pd.read_csv('data/query_df_2.csv').drop(["Unnamed: 0"], axis=1)
df_3 = pd.read_csv('data/query_df_3.csv').drop(["Unnamed: 0"], axis=1)
df_4 = pd.read_csv('data/selected_articles.csv')

with open('data/mybib.bib') as bibtex_file:
    bibtex_str = bibtex_file.read()

selected = bibtexparser.loads(bibtex_str)
# db = pd.DataFrame(selected.entries)
# db.to_excel("data/fileS1.xlsx")
#

idxs = []
for idx, i in enumerate(selected.entries):
    corrected = i["title"].replace("{\&}", "&")
    corrected = corrected.replace("\n", " ")
    corrected = corrected[1:-1]
    # print(corrected[1:-1])
    # print("---")
    if df_4[df_4["title"].str.contains(corrected)].shape[0]!=0:
        print(corrected)
        idxs.append(idx)

l0 = [4, 18, 25, 33, 53, 59, 65, 68, 69, 70, 72, 86, 87, 88, 98, 102]
l1 = [18, 23, 24, 25, 26, 38, 59, 69, 71, 83, 118]
l2 = [7, 10, 15, 16, 17, 18, 25, 35, 41, 55, 56, 59, 69, 96, 108, 114]
lt = [18, 24, 25, 35, 59, 69, 87]