import sys
import nltk
nltk.download(['punkt', 'wordnet'])
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

import pandas as pd
from sqlalchemy import create_engine
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split

from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV

import pickle

def load_data(database_filepath):
    '''
    Read the data from the given database
    
    Arguments: 
        database_filepath:  file path to database file
    
    Returns: 
        Messages:   dataframe containing all messages
        Categories: dataframe containing all categories
        Category names: list of all category names
    '''
    
    # load data from database
    engine = create_engine('sqlite:///' + database_filepath)
    df = pd.read_sql_table('cleaned_data', engine)
    X = df['message']
    Y = df.drop(columns = ['id', 'message', 'original', 'genre'])
    category_names = list(Y.columns)
    
    return X, Y, category_names

def tokenize(text):
    '''
    Implement text proccessing steps to the given text
    Steps: Case normalization, Lemmatization, Tokenization, 
    
    Argument:
        text:   input text
    
    Return:
        clean_tokens:   proccessed and tokenized text 
    '''
    # tokenize text
    tokens = word_tokenize(text)
    # remove stop words
    tokens = [tok for tok in tokens if tok not in stopwords.words("english")]
    # initialize lemmitizer 
    lemmatizer = WordNetLemmatizer()
    
    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens

def build_model():
    '''
    Build a mchine learning pipleline and implement gridsearch 
    to the pipeline
    
    Return:
        pipleline_cv:   machine learning pipleline having gridsearch parameters 
    '''
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', RandomForestClassifier())
    ])
    
    parameters = {
        'vect__ngram_range': ((1, 1), (1, 2)),
        'clf__n_estimators': [100, 150],
        'clf__min_samples_split': [2, 3, 4]
    }

    pipleline_cv = GridSearchCV(pipeline, param_grid=parameters, verbose=3)
    return pipleline_cv

def evaluate_model(model, X_test, Y_test, category_names):
    '''
    The funcrion predicts on the test data and return evaluation metrics
    Argument:
           X_test: faetures in test data
           Y_test: target values(categories) in test data
    Retrun:
           print evaluation metrics for each category
    '''
    
    # predict on test data
    y_pred = model.predict(X_test)
    
    # print evaluation metrics for each category
    for i, category_name in enumerate(category_names):
        print(category_name)
        print(classification_report(Y_test[category_name], y_pred[:,i]))
        
    # print all evaluation metrics as average over all categories
    accuracy = 0
    precision = 0
    recall = 0
    f1_score = 0 
    for i, category_name in enumerate(category_names):
        accuracy += accuracy_score(Y_test[category_name], y_pred[:,i])
        precision += float(classification_report(Y_test[category_name], y_pred[:,i])[-35:-31])
        recall += float(classification_report(Y_test[category_name], y_pred[:,i])[-25:-21])
        f1_score += float(classification_report(Y_test[category_name], y_pred[:,i])[-15:-11])

    accuracy = accuracy/len(category_names)
    precision = precision/len(category_names)
    recall = recall/len(category_names)
    f1_score = f1_score/len(category_names)
    print('Average of each metric over all categories:')
    print('Average accuracy:', round(accuracy, 2))
    print('Average precision:', round(precision, 2))
    print('Average recall:', round(recall, 2))
    print('Average f1_score:', round(f1_score, 2))


def save_model(model, model_filepath):
    '''
    Save model in the input file path
    
    Argument:
        model:  model to be saved in the path
        model_filepath: filepath to save the model
        
    Return:
        save the model in the given directory
    '''
    
    # Save the model as a pickle file
    pickle.dump(model, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()