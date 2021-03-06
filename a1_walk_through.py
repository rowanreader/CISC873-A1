# -*- coding: utf-8 -*-
"""A1_walk_through.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/173dGt3z3oS4w4VK1z0a3PQmxICg32EAT
"""

import pandas as pd
import numpy as np
from sklearn.metrics import f1_score
from pprint import pprint

from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_openml
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from xgboost.sklearn import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from skopt.space import Real, Categorical, Integer
from sklearn.linear_model import LogisticRegression

data = pd.read_csv('train.csv')
data_test = pd.read_csv('test.csv')

# prints out the dimenstions of the train data
data.shape

# detects missing values, sums, plots histogram
data.isnull().sum().hist()

# just the histogram for this column
data['match'].hist()

# if you haven't installed xgboost on your system, uncomment the line below
# !pip install xgboost
# if you haven't installed bayesian-optimization on your system, uncomment the line below
#!pip install scikit-optimize

# remove column match (this is the answer column)
x = data.drop('match', axis=1)
# separate numeric and categorical features
features_numeric = list(x.select_dtypes(include=['float64']))
features_categorical = list(x.select_dtypes(include=['object']))
# store answers separately
y = data['match']

print(features_categorical)


np.random.seed(1)

# make numerical imputer as pipeline - more streamlined
# strategy will be overwritten
transformer_numeric = Pipeline(
    steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())]
)

# make categorical imputer, replace with 'missing'
# encode to convert values to numbers
transformer_categorical = Pipeline(
    steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ]
)

# combines pipelines and apply to data
preprocessor = ColumnTransformer(
    transformers=[
        ('num', transformer_numeric, features_numeric),
        ('cat', transformer_categorical, features_categorical)
    ]
)

# does preprocessing and classification (gradient boosted decision trees)
# initializes XGBClassifier
pipeline_XGB = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('xgbClass', XGBClassifier(
            objective='binary:logistic', seed=1))
    ]
)

# uses same preprocessor, initializes logistic regression classifier
# sets iterations to 600 with tol to 0.005 (represents when it considers it converged)
pipeline_LR = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('lrClass', LogisticRegression(max_iter=600, tol=0.005))
         ]
)

# initializes random forest classifier
pipeline_RF = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('rfClass', RandomForestClassifier())
         ]
)

# initializes K nearest neighbors classifier
# - chosen instead of svm due to familiarity with svm
pipeline_KNN = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('knnClass', KNeighborsClassifier())
         ]
)

# initializes MLP with set max iterations and learning rate initialization
# due to convergence issues, initial learning rate set to higher value
pipeline_MLP = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('mlpClass', MLPClassifier(max_iter=600, learning_rate_init=0.01))
         ]
)

# dictionary of parameters

# `__` denotes attribute 
# (e.g. my_classifier__n_estimators means the `n_estimators` param for `my_classifier`
#  which is our xgb)
param_XGB = {
    'preprocessor__num__imputer__strategy': ['mean','median'],
    'xgbClass__n_estimators': [140,150,165,170,175,180],
    'xgbClass__max_depth':[10,15,20]
}

# the parameters chosen for logistic regression
param_LR = {
    'preprocessor__num__imputer__strategy': ['mean','median'],
    'lrClass__penalty': ['l2'],
    'lrClass__C':[0.1,0.5,1,1.5],
    'lrClass__solver':['sag', 'saga']
}

# the parameters chosen for random forest
param_RF = {
    'preprocessor__num__imputer__strategy': ['mean','median'],
    'rfClass__n_estimators': [100,150,190,200,220,250,270],
    'rfClass__max_depth':[8,10,15,20]
}

# parameters for k nearest neighbors
param_KNN = {
    'preprocessor__num__imputer__strategy': ['mean','median'],
    'knnClass__n_neighbors': [70,100,120,150],
    'knnClass__weights':['uniform', 'distance'],
    'knnClass__algorithm':['auto', 'ball_tree', 'kd_tree', 'brute']
}

# parameters for multi layer perceptron
param_MLP = {
    'preprocessor__num__imputer__strategy': ['mean','median'],
    'mlpClass__activation':['logistic', 'tanh', 'relu'],
    'mlpClass__solver':['sgd', 'adam'],
    'mlpClass__hidden_layer_sizes':[(100,),(150,),(100,100),(100,150)]
}

"""
# exhaustive search over parameters, uses the pipeline made above
grid_search = GridSearchCV(
    full_pipline, param_grid, cv=5, verbose=3, n_jobs=2, 
    scoring='roc_auc') # computes area under curve from prediction scores

grid_search.fit(x, y)

# print out best average score found in search and the parameters for it

print('best score {}'.format(grid_search.best_score_))
print('best score {}'.format(grid_search.best_params_))

# prepare submission:
submission = pd.DataFrame()
submission['id'] = data_test['id']
submission['match'] = grid_search.predict_proba(data_test)[:,1]
submission.to_csv('RandomSearch.csv', index=False)
"""

# make array of pipelines and parameters to iterate through
pipelines = [pipeline_XGB, pipeline_LR, pipeline_RF, pipeline_KNN, pipeline_MLP]
params = [param_XGB, param_LR, param_RF, param_KNN, param_MLP]
names = ['XGB', 'LR', 'RF', 'KNN', 'MLP']

# iterate through pipelines and parameters
# use random search - produces better results than Bayesian, likely due to getting stuck in local optimums
for i in range(5):
    # uses same parameters and model
    random_search = RandomizedSearchCV(
        pipelines[i], params[i], cv=5, verbose=3, n_jobs=2,
        scoring='roc_auc')

    random_search.fit(x, y)
    print('best score {}'.format(random_search.best_score_))
    print('best score {}'.format(random_search.best_params_))

    # prepare submission:
    submission = pd.DataFrame()
    submission['id'] = data_test['id']
    submission['match'] = random_search.predict_proba(data_test)[:,1]
    submission.to_csv('RandomSearch' + names[i] + '.csv', index=False)


"""
from skopt import BayesSearchCV
from skopt.space import Real, Categorical, Integer
from sklearn.svm import SVC

# bayesian search parameters for xgboost
# must be in ranged form
param_bayes = {
    'preprocessor__num__imputer__strategy': Categorical(['most_frequent','mean','median']),
    'my_classifier__n_estimators': Integer(10, 210, 'log-uniform'),
    'my_classifier__max_depth':Integer(5, 30, 'log-uniform')
}

# chooses values based on optimized approach
# essentially random but skewed towards high performing ones
bayes_search = BayesSearchCV(
    full_pipline, param_bayes, cv=5, verbose=3, n_jobs=2,
    scoring='roc_auc',
    n_iter=3,
    random_state=0,
    refit=True,

)

bayes_search.fit(x, y)

# print out best score and its parameters
print('best score {}'.format(bayes_search.best_score_))
print('best score {}'.format(bayes_search.best_params_))

"""

"""
# make another pipeline, same preprocessor but using an SVM instead of decision trees
SVC_pipline = Pipeline(
    steps=[
        ('preprocessor', preprocessor),
        ('my_svc', SVC(class_weight='balanced', probability=True))
    ]
)
# SVC has a class_weight attribute for unbalanced data


# samples a fixed number of parameters (not exhaustive like GridSearchCV) from distribution
# Sets svm parameters: C-regularization, kernal-type of kernal, degree-for polynomial kernal, gamma-influence
# define ranges for bayes search
bayes_search = BayesSearchCV(
    SVC_pipline,
    {
        'my_svc__C': Real(1e-6, 1e+6, prior='log-uniform'),
        'my_svc__gamma': Real(1e-6, 1e+1, prior='log-uniform'),
        'my_svc__degree': Integer(1,8),
        'my_svc__kernel': Categorical(['poly', 'rbf']),
    },
    n_iter=3,
    random_state=0,
    verbose=3,
    refit=True,
)

bayes_search.fit(x, y)

# print out best score and its parameters
print('best score {}'.format(bayes_search.best_score_))
print('best score {}'.format(bayes_search.best_params_))

# lists which parameters were chosen
print('all the cv scores')
# pretty printing
pprint(bayes_search.cv_results_)



# prepare submission:
submission = pd.DataFrame()
submission['id'] = data_test['id']
submission['match'] = bayes_search.predict_proba(data_test)[:,1]
submission.to_csv('BayesSearch.csv', index=False)

"""
