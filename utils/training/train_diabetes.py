import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Load dataset
df = pd.read_csv("datasets/diabetes.csv")

# Features and Target
X = df.drop("Outcome", axis=1)
y = df["Outcome"]

# Scale data
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Deep Learning Model
model = Sequential()

model.add(Dense(16, activation="relu", input_shape=(8,)))
model.add(Dense(8, activation="relu"))
model.add(Dense(1, activation="sigmoid"))

model.compile(
    optimizer="adam",
    loss="binary_crossentropy",
    metrics=["accuracy"]
)

# Train model
model.fit(
    X_train,
    y_train,
    epochs=50,
    batch_size=16
)

# Evaluate
loss, accuracy = model.evaluate(X_test, y_test)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

# Save model
model.save("model/diabetes_model.h5")

print("\nModel Saved Successfully!")