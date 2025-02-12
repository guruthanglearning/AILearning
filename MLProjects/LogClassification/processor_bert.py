from sentence_transformers import SentenceTransformer
import joblib

# Load the pre-trained Sentence Transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')
# Load the saved classifier model
classifier_model = joblib.load('d:/Study/AILearning/MLProjects/LogClassification/Model/log_classifier_model.joblib')

def classify_with_BERT(log_message):
    
    # Generate embeddings for the log message
    embeddings = model.encode([log_message])

    # Classify the log message
    prediction = classifier_model.predict_proba(embeddings)[0]
    if max(prediction) < 0.5:
        return "Unknown"
    return classifier_model.predict(embeddings)[0]

if __name__ == "__main__":
    log_messages = [
        "User User123 logged in.",
        "Backup started at 2023-10-01 12:00:00.",
        "Backup completed successfully.",
        "System updated to version 1.2.3.",
        "File report.pdf uploaded successfully by user User456.",
        "Disk cleanup completed successfully.",
        "System reboot initiated by user User789.",
        "Account with ID 101 created by Admin.",
        "test"
    ]

    for log in log_messages:
        result = classify_with_BERT(log);        
        label = result[0]
        message = result
        print(f"Model: LLM Log: ", log, " => Category: ", label, " Message: ", message)