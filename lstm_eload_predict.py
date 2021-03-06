import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.contrib import learn
from sklearn.metrics import mean_squared_error
from lstm import generate_data, lstm_model, load_csvdata, load_csvdata_xy, sin_cos
import dateutil.parser
import datetime
import matplotlib.dates as mdates
import os
import shutil 

# When you change network parameters, Do rm -rf ops_logs/*
LOG_DIR = './ops_logs/lstm_eload_predict'
TIMESTEPS = 30
#RNN_LAYERS = [{'num_units': 5}]
#DENSE_LAYERS = [10, 10]
RNN_LAYERS = [{'num_units': 30}]
DENSE_LAYERS = [30]
TRAINING_STEPS = 500000 #3200000
BATCH_SIZE = 56
PRINT_STEPS = 365
NORMALFACTOR = 1000.0

def mean_absolute_percentage_error(y_true, y_pred):
  if len(y_true.shape) > 1:
    y_true = np.squeeze(y_true)
  if len(y_pred.shape) > 1:
    y_pred = np.squeeze(y_pred)
  return (np.average(abs( (y_true - y_pred) / y_true ) )*100)

def maximum_absolute_error(y_true, y_pred):
  if len(y_true) > 1: #if len(y_true.shape)
    y_true = np.squeeze(y_true)
  if len(y_pred) > 1: #if len(y_pred.shape)
    y_pred = np.squeeze(y_pred)
  return (np.max(abs( y_true - y_pred)))


def load_eload_frame(filename):
    data_raw = pd.read_csv(filename)
    data_raw = data_raw.astype(float)

    # normalize
    data_raw['yesterday_consumed'] = data_raw['yesterday_consumed'] / NORMALFACTOR
    data_raw['today_consume'] = data_raw['today_consume'] / NORMALFACTOR

    #df_X = pd.DataFrame(data_raw, columns=['weekday', 'special', 'avgtemp108', 'yesterday_consumed'])
    df_X = pd.DataFrame(data_raw, columns=['yesterday_consumed',  'special', 'weekday', 'avgtemp108'])
    #df_X = pd.DataFrame(data_raw, columns=['yesterday_consumed', 'special', 'dayofyear'])
    #df_X = pd.DataFrame(data_raw, columns=['yesterday_consumed', 'special'])
    #df_X = pd.DataFrame(data_raw, columns=['yesterday_consumed'])
    df_y = pd.DataFrame(data_raw, columns=['today_consume'])

    return df_X, df_y

try:
	shutil.rmtree(LOG_DIR)
except OSError:
	pass

data_eload_X, data_eload_y = load_eload_frame("data/eload-2005-2014.csv")
X, y = load_csvdata_xy(data_eload_X, data_eload_y, TIMESTEPS, val_size=0.01, test_size=0.10)
#print X
#X, y = generate_data(sin_cos, np.linspace(0, 100, 10000, dtype=np.float32), TIMESTEPS, seperate=False)


regressor = learn.Estimator(model_fn=lstm_model(TIMESTEPS, RNN_LAYERS, DENSE_LAYERS),
                           model_dir=LOG_DIR)

# create a lstm instance and validation monitor
validation_monitor = learn.monitors.ValidationMonitor(X['val'], y['val'],
                                                     every_n_steps=PRINT_STEPS,
                                                     early_stopping_rounds=1000000)
regressor.fit(X['train'], y['train'],
              monitors=[validation_monitor],
              batch_size=BATCH_SIZE,
              steps=TRAINING_STEPS)

predicted = regressor.predict(X['test'])

#not used in this example but used for seeing deviations
rmse = np.sqrt(((predicted - y['test']) ** 2).mean(axis=0))

score = mean_squared_error(predicted, y['test'])
print ("MSE: %f" % score)
mape = mean_absolute_percentage_error(y['test'], predicted)
print ("MAPE: %f" % mape)
mae = maximum_absolute_error(y['test'], predicted)
print ("MAE: %f" % (mae*NORMALFACTOR))

plot_predicted, = plt.plot(predicted, label='predicted')
plot_test, = plt.plot(y['test'], label='test')
plt.legend(handles=[plot_predicted, plot_test])
plt.show()

