import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
import joblib
import os

# Step 1: Load data
df = pd.read_csv("data/processed/clean_listings.csv")
print(f"Dataset size: {len(df)} rows\n")

# Step 2: Feature Engineering
df["property_type"] = df["title"].str.split(" in ").str[0]

# Step 3: Clean up property type variations
df["property_type"] = df["property_type"].replace({
    "Rooms": "Room",
    "Place to stay": "Apartment",
    "Hotel Julian": "Hotel",
    "Home": "Apartment"
})
print("Cleaned property types:")
print(df["property_type"].value_counts())
print()

# Step 4: Encode text columns to numbers
le_region = LabelEncoder()
le_type = LabelEncoder()

df["region_encoded"] = le_region.fit_transform(df["region"])
df["type_encoded"] = le_type.fit_transform(df["property_type"])

# Step 5: Define features and target
X = df[["region_encoded", "type_encoded"]]
y = df["price"]

# Step 6: Split into train and test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Training rows: {len(X_train)}")
print(f"Testing rows : {len(X_test)}\n")

# Step 7: Train the model
model = XGBRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1
)
model.fit(X_train, y_train)
print("Model trained!")

# Step 8: Evaluate
predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)
print(f"Mean Absolute Error: ${mae:.2f}\n")

# Step 9: Save model and encoders
os.makedirs("ml/models", exist_ok=True)
joblib.dump(model, "ml/models/price_model.pkl")
joblib.dump(le_region, "ml/models/le_region.pkl")
joblib.dump(le_type, "ml/models/le_type.pkl")
print("Model saved to ml/models/")

# Step 10: Test prediction
loaded_model = joblib.load("ml/models/price_model.pkl")
loaded_le_region = joblib.load("ml/models/le_region.pkl")
loaded_le_type = joblib.load("ml/models/le_type.pkl")

test_region = "New-York"
test_type = "Apartment"

region_enc = loaded_le_region.transform([test_region])[0]
type_enc = loaded_le_type.transform([test_type])[0]

predicted = loaded_model.predict([[region_enc, type_enc]])
print(f"\nTest prediction:")
print(f"Region: {test_region} | Type: {test_type}")
print(f"Predicted price: ${predicted[0]:.2f} per night")