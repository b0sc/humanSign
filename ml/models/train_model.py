from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "humansign_phase1_final_dataset.csv"
)

df = pd.read_csv(DATASET_PATH)

print(df.shape)
print(df.head())

TARGET_COL = "subject"

DROP_COLUMNS = [
    "subject",
    "sessionIndex",
    "rep"
]

X = df.drop(columns=DROP_COLUMNS)
y = df[TARGET_COL]


print("X shape:", X.shape)
print("y shape:", y.shape)
print("First 5 feature names:")
print(X.columns[:5])


from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

print("Number of unique subjects:", len(label_encoder.classes_))

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

print("Train X:", X_train.shape)
print("Test X:", X_test.shape)
print("Train y:", y_train.shape)
print("Test y:", y_test.shape)



from xgboost import XGBClassifier
model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    eval_metric="mlogloss",
    random_state=42
)
model.fit(X_train, y_train)

print("Model training completed")

import joblib

ARTIFACT_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(model, ARTIFACT_DIR / "xgboost_model.pkl")
joblib.dump(label_encoder, ARTIFACT_DIR / "label_encoder.pkl")
joblib.dump(X.columns.tolist(), ARTIFACT_DIR / "feature_list.pkl")

print("Model artifacts saved successfully")








