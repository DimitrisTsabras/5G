import numpy as np
import pandas as pd
import keras
from keras import layers, Input
from keras.models import load_model
import tensorflow as tf
# Visualisation:
from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# Define the number of time steps
TIME_STEPS = 100

# Change file root as required!
file_train_root = "train.txt"
file_test_root = "test.txt"

# make the dataframes
df_train = pd.read_csv(file_train_root, sep=',')
df_test = pd.read_csv(file_test_root, sep=',')

'''
# DEBUG: shape of the data
print(df_train.shape)
print(df_test.shape)
'''

# training sequences for use in the model.
def create_sequences(values, time_steps=TIME_STEPS):
    output = []
    for i in range(len(values) - time_steps + 1):
        output.append(values[i: (i + time_steps)])
    return np.stack(output)

# make the sequences
x_train = create_sequences(df_train.values)
x_test = create_sequences(df_test.values)

'''
# DEBUG: shape of the data
#due to the window approach the data is reduced
print("Training input shape: ", x_train.shape)
print("Test input shape: ", x_test.shape)
'''

'''
# ========== Model ==========
model = keras.Sequential(
    [
        layers.Input(shape=(x_train.shape[1], x_train.shape[2])),
        layers.Conv1D(
            filters=32,
            kernel_size=7,
            padding="same",
            strides=1,  # Adjusted the strides to be 1
            activation="relu",
        ),
        layers.Dropout(rate=0.2),
        layers.Conv1D(
            filters=16,
            kernel_size=7,
            padding="same",
            strides=1,  # Adjusted the strides to be 1
            activation="relu",
        ),
        layers.Conv1DTranspose(
            filters=16,
            kernel_size=7,
            padding="same",
            strides=1,  # Adjusted the strides to be 1
            activation="relu",
        ),
        layers.Dropout(rate=0.2),
        layers.Conv1DTranspose(
            filters=32,
            kernel_size=7,
            padding="same",
            strides=1,  # Adjusted the strides to be 1
            activation="relu",
        ),
        layers.Conv1DTranspose(filters=38, kernel_size=7, padding="same"),
    ]
)

model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
model.summary()
history = model.fit(
    x_train,
    x_train,
    epochs=40,
    batch_size=64,
    validation_split=0.1,
    callbacks=[
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, mode="min")
    ],
)

# ========== Plots ==========

# Plotting the Training Loss:
plt.plot(history.history['loss'], label='Training Loss')

# Plotting the Validation Loss:
plt.plot(history.history['val_loss'], label='Validation Loss')

plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')

plt.legend()
plt.show()
'''

# Load the model
model = load_model("anomaly_complete_v0_3.keras")

# ========== Predictions ==========

# Predict and MAE loss for the training data
train_predictions = model.predict(x_train)
train_mae_loss = np.mean(np.abs(train_predictions - x_train), axis=1)
# Predict and MAE loss for the test data
test_predictions = model.predict(x_test)
test_mae_loss = np.mean(np.abs(test_predictions - x_test), axis=1)

# Plot the MAE loss for the training data
plt.hist(train_mae_loss, bins=50)
plt.title('MAE Loss - TRAIN')
plt.xlabel('Train MAE Loss')
plt.ylabel('No of samples')

plt.show()

# ========== Anomaly Detection ==========

# Set the threshold
threshold = np.percentile(train_mae_loss, 89.5) + 0.085

# Detect anomalies in the test data (boolean multi-dimensional)
anomalies = test_mae_loss > threshold
# (boolean one-dimensional)
anomalous_samples = np.any(anomalies, axis=1)

# Load the test_labels.txt file
test_labels = np.loadtxt('test_labels.txt')

# Trim the first TIME_STEPS-1 elements from test_labels
test_labels_trimmed = test_labels[TIME_STEPS:]

'''
# DEBUG: shape of the data
# due to the window approach the data is reduced
# test_labels should be trimmed 
print("Shape of test_labels: ", test_labels.shape)
print("Shape of test_labels_trimmed: ", test_labels_trimmed.shape)
print("Shape of anomalous_samples: ", anomalous_samples.shape)
'''

#check
assert test_labels_trimmed.shape == anomalous_samples.shape

# Compare
common_values = np.logical_and(anomalous_samples, test_labels_trimmed)

# Calculate the sum for each one
anomalies_detected = np.sum(anomalous_samples)
actual_anomalies = np.sum(test_labels_trimmed)
correctly_detected_anomalies = np.sum(common_values)

print("Number of anomalies detected: ", anomalies_detected)
print("Actual number of anomalies: ", actual_anomalies)
print("Number of correctly detected anomalies: ", correctly_detected_anomalies)

# Plot a bar graph with these three values
labels = ['Anomalies Detected', 'Actual Anomalies', 'Correctly Detected Anomalies']
values = [anomalies_detected, actual_anomalies, correctly_detected_anomalies]

plt.bar(labels, values)
plt.title('Anomaly Detection Results')
plt.xlabel('Categories')
plt.ylabel('Number of Anomalies')
plt.show()

# ========== Confusion Matrix ==========

# Calculate the confusion matrix
cm = confusion_matrix(test_labels_trimmed, anomalous_samples)

# Display the confusion matrix
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Anomaly"])
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()

# ========== METRICS ==========

# Calculate the precision, recall, and F1 score
precision = correctly_detected_anomalies / anomalies_detected
recall = correctly_detected_anomalies / actual_anomalies
f1_score = 2 * precision * recall / (precision + recall)

print("Precision: ", precision)
print("Recall: ", recall)
print("F1 Score: ", f1_score)

# ========== VISUALISATION ==========

#-------------
# Plot the anomalies through time:

# Create an array for all samples
all_samples = np.arange(len(anomalous_samples))

# Create arrays for actual anomalies, detected anomalies, and correctly detected anomalies
actual_anomalies_indices = np.where(test_labels_trimmed == 1)[0]
detected_anomalies_indices = np.where(anomalous_samples == True)[0]
correctly_detected_anomalies_indices = np.where(common_values == True)[0]

# Create a scatter plot
plt.figure(figsize=(10,6))

# Plot all samples
plt.scatter(all_samples, [0]*len(all_samples), color='blue', s=10, label='All Samples')

# Plot actual anomalies
plt.scatter(actual_anomalies_indices, [1]*len(actual_anomalies_indices), color='red', s=10, label='Actual Anomalies')

# Plot detected anomalies
plt.scatter(detected_anomalies_indices, [2]*len(detected_anomalies_indices), color='purple', s=10, label='Anomalies Detected')

# Plot correctly detected anomalies
plt.scatter(correctly_detected_anomalies_indices, [3]*len(correctly_detected_anomalies_indices), color='green', s=10, label='Correctly Detected Anomalies')

# Label the axes
plt.xlabel('Sample Index')
plt.yticks([0, 1, 2, 3], ['All Samples', 'Actual Anomalies', 'Anomalies Detected', 'Correctly Detected Anomalies'])
plt.ylabel('Category')

# Add a legend
plt.legend()

# Show the plot
plt.show()

#--------------
# plot the predicted var1
# Select the first variable from the actual and predicted training data
actual_data = x_train[:, :, 0]
predicted_data = train_predictions[:, :, 0]

# Flatten the actual_data and predicted_data arrays
actual_data_flat = actual_data.flatten()
predicted_data_flat = predicted_data.flatten()

# Plot the actual data
plt.figure(figsize=(12,6))
plt.plot(actual_data_flat, 'b', label='Actual')

# Plot the predicted data
plt.plot(predicted_data_flat, 'r', label='Predicted')

# Label the axes
plt.xlabel('Time Step')
plt.ylabel('Value')

# Add a legend
plt.legend()

# Show the plot
plt.show()