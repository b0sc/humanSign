from pathlib import Path
import pandas as pd
import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "humansign_phase1_final_dataset.csv"
)

df = pd.read_csv(DATASET_PATH)
TARGET_COL = "subject"

DROP_COLUMNS = [
    "subject",
    "sessionIndex",
    "rep"
]

X = df.drop(columns=DROP_COLUMNS)
y = df[TARGET_COL]

ARTIFACT_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"

model = joblib.load(ARTIFACT_DIR / "xgboost_model.pkl")
label_encoder = joblib.load(ARTIFACT_DIR / "label_encoder.pkl")
feature_list = joblib.load(ARTIFACT_DIR / "feature_list.pkl")


X = X[feature_list]
y_encoded = label_encoder.transform(y)


from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)


from sklearn.metrics import accuracy_score, classification_report

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))


import pandas as pd

feature_importance = pd.DataFrame({
    "feature": feature_list,
    "importance": model.feature_importances_
}).sort_values(by="importance", ascending=False)

print("\nTop 15 Most Important Features:")
print(feature_importance.head(15))


def authorship_nutrition_label(model, X_sample):
    probs = model.predict_proba(X_sample)[0]

    max_confidence = probs.max()

    organic_human = round(max_confidence * 100, 2)

    remaining = 100 - organic_human

    ai_assisted = round(remaining * 0.6, 2)
    pasted = round(remaining * 0.4, 2)

    return {
        "Organic Human Process (%)": organic_human,
        "AI-Assisted Completion (%)": ai_assisted,
        "Pasted Content (%)": pasted
    }

sample = X_test.iloc[[0]]

label = authorship_nutrition_label(model, sample)

print("\nAuthorship Nutrition Label:")
for k, v in label.items():
    print(f"{k}: {v}")






