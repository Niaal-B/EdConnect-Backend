import joblib

model = joblib.load('career_model.joblib')
le = joblib.load('label_encoder.joblib')

def career_prediction(user_input: list[str]):
    """Predicts career based on skill input"""
    skills = user_input
    pred = model.predict(skills)
    print("Predicted Career:", le.inverse_transform(pred)[0])


if __name__ == "__main__":
    career_prediction(["Customer Relationship Management, Communication, Leadership"])
