# Simple test to see if ML agent predicts correctly
import joblib

model = joblib.load("ml_agent.pkl")
test_input = [[0] * 42]
print("Example prediction:", model.predict(test_input)) # should output a number
