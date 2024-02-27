import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
from sklearn.model_selection import learning_curve
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from joblib import dump

# Load the data
data = pd.read_csv('output.csv')  # Replace with your data file path

# Preprocess the data
# Assuming 'RSSI' and 'SNR' are the features and 'GPSDistance' is the target variable
X = data[['RSSI', 'SNR']]
y = data['GPSDistance']


# Splitting the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardizing the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train the Gradient Boosting Regressor
model = GradientBoostingRegressor(random_state=42,learning_rate=0.1,max_depth=3,min_samples_leaf=2,min_samples_split=2,n_estimators=100)
model.fit(X_train_scaled, y_train)

# Predictions
y_pred = model.predict(X_test_scaled)

# Assuming 'model' is your Gradient Boosting Regressor
dump(model, 'gradient_boosting_regressor.joblib')
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(mse)
print(mae)
# # GradientBoosting
# param_grid = {
#     'n_estimators': [100, 200, 300],
#     'learning_rate': [0.01, 0.1, 0.2],
#     'max_depth': [3, 4, 5],
#     'min_samples_split': [2, 4],
#     'min_samples_leaf': [1, 2],
# }

# grid_search = GridSearchCV(GradientBoostingRegressor(random_state=42), param_grid, cv=5, scoring='neg_mean_absolute_error', verbose=1)
# grid_search.fit(X_train_scaled, y_train)

# print(f"Best parameters: {grid_search.best_params_}")
# print(f"Best MAE: {-grid_search.best_score_}")


# param_grid_expanded = {
#     'n_neighbors': [29, 30, 31, 32, 33],  # Narrow down the range around the best found
#     'weights': ['uniform', 'distance'],
#     'metric': ['euclidean', 'manhattan']
# }

# grid_search_knn_expanded = GridSearchCV(KNeighborsRegressor(), param_grid_expanded, cv=5, scoring='neg_mean_absolute_error', verbose=1)
# grid_search_knn_expanded.fit(X_train_scaled, y_train)

# print(f"Expanded Best parameters: {grid_search_knn_expanded.best_params_}")
# print(f"Expanded Best MAE: {-grid_search_knn_expanded.best_score_}")


# optimal_knn_model = KNeighborsRegressor(n_neighbors=30, metric='manhattan', weights='uniform')
# optimal_knn_model.fit(X_train_scaled, y_train)

# # # Predictions
# # y_pred = optimal_knn_model.predict(X_test_scaled)


# # Evaluate the model


# print(f"Mean Squared Error: {mse}")
# print(f"Mean Absolute Error: {mae}")

# def plot_prediction_vs_actual_with_range(y_test, y_pred):
#     plt.figure(figsize=(10, 6))
#     plt.scatter(y_test, y_pred, alpha=0.5, label='Predictions')
#     plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2, label='Perfect Prediction')
#     # Adding lines for ±130 meters range
#     plt.plot([y_test.min(), y_test.max()], [y_test.min() + 130, y_test.max() + 130], 'g--', lw=1, label='+130m Range')
#     plt.plot([y_test.min(), y_test.max()], [y_test.min() - 130, y_test.max() - 130], 'r--', lw=1, label='-130m Range')
#     plt.title('Prediction vs. Actual GPS Distance')
#     plt.xlabel('Actual GPS Distance')
#     plt.ylabel('Predicted GPS Distance')
#     plt.legend()
#     plt.grid(True)
#     plt.show()

# # Visualization: Prediction vs. Actual Scatter Plot
# plot_prediction_vs_actual_with_range(y_test, y_pred)

# # Visualization: Residuals Plot
# residuals = y_pred - y_test
# plt.figure(figsize=(10, 6))
# plt.scatter(y_pred, residuals, alpha=0.5)
# plt.hlines(y=0, xmin=y_pred.min(), xmax=y_pred.max(), colors='k', linestyles='--')
# plt.title('Residuals vs. Predicted GPS Distance')
# plt.xlabel('Predicted GPS Distance')
# plt.ylabel('Residuals')
# plt.grid(True)
# plt.show()

# # Generate a Learning Curve
# def plot_learning_curve(estimator, title, X, y, ylim=None, cv=None, n_jobs=None, train_sizes=np.linspace(.1, 1.0, 5)):
#     plt.figure()
#     plt.title(title)
#     if ylim is not None:
#         plt.ylim(*ylim)
#     plt.xlabel("Training examples")
#     plt.ylabel("Score")
    
#     train_sizes, train_scores, test_scores = learning_curve(
#         estimator, X, y, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes)
    
#     # Calculate means and standard deviations
#     train_scores_mean = np.mean(train_scores, axis=1)
#     train_scores_std = np.std(train_scores, axis=1)
#     test_scores_mean = np.mean(test_scores, axis=1)
#     test_scores_std = np.std(test_scores, axis=1)
    
#     # Plotting the learning curve
#     plt.grid()
    
#     # Fill between for training and test scores with standard deviation
#     plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
#                      train_scores_mean + train_scores_std, alpha=0.1, color="r")
#     plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
#                      test_scores_mean + test_scores_std, alpha=0.1, color="g")
    
#     # Plot mean scores
#     plt.plot(train_sizes, train_scores_mean, 'o-', color="r", label="Training score")
#     plt.plot(train_sizes, test_scores_mean, 'o-', color="g", label="Cross-validation score")
    
#     plt.legend(loc="best")
#     return plt

# plot_learning_curve(GradientBoostingRegressor(random_state=42), "Learning Curve (Gradient Boosting Regressor)",
#                     X_train_scaled, y_train, cv=5, n_jobs=-1)
# plt.show()
