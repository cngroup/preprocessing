primary modules
----------------------------------------------------
indexing.py : build lucene index for raw text data to support query
tweet_transform.py : transforms the raw twitter data into matrix form
email_transform.py : transforms the raw email data into matrix form
clustering.py : load the matrices and generates smoothing clusters
output.py : transforms the analysis results into json used in the visualization


utility models 
----------------------------------------------------
ttp.py : for twitter json parsing
utils.py :  for constructing the output json file for visualization