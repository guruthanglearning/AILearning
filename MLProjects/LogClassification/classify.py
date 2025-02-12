import re
import pandas as pd
from processor_regex import classify_with_regex
from processor_llm import classify_with_LLM
from processor_bert import classify_with_BERT

def classify_with_regex(source, log_message):
    regex_patterns = {
        r"User User\d+ logged (in|out).": "User Action",
        r"Backup (started|ended) at .*": "System Notification",
        r"Backup completed successfully.": "System Notification",
        r"System updated to version .*": "System Notification",
        r"File .* uploaded successfully by user .*": "System Notification",
        r"Disk cleanup completed successfully.": "System Notification",
        r"System reboot initiated by user .*": "System Notification",
        r"Account with ID .* created by .*": "User Action"
    }
    for pattern, category in regex_patterns.items():
        if re.match(pattern, log_message, re.IGNORECASE):
            return category
    return  None

def classify_csv(inputfile):
    df = pd.read_csv(inputfile + '/Logs.csv')
    df['Lable'] = classify(list(zip(df['sources'], df['log_message'])))
    df.to_csv(inputfile  + '/Result.csv', index=False)
   

def classify(logs):
    labels = []
    for source, logmessage in logs:
        label = classify_logs(source, logmessage)
        labels.append (label)
    return labels

def classify_logs(source, logmessage):
    if source == "LegacyCRM":
          label = classify_with_LLM(logmessage)
    else:
        label = classify_with_regex(source, logmessage)
        if label is None:
            label = classify_with_BERT(logmessage)                     
    return label

if __name__ == "__main__":   
   classify_csv('D:\Study\AILearning\MLProjects\LogClassification\Datasets')
   """  log_messages = [
        ("ModernCRM", "IP 192.168.133.114 blocked due to potential attack"),
        ("BillingSystem", "User User2345 logged in."),
        ("AnalyticsEngine", "File data_6957.csv uploaded successfully by user User265."),
        ("AnalyticsEngine", "Backup completed successfully."),
        ("ModernHR", "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1 RCODE  200 len: 1583 time: 0.1878400"),
        ("ModernHR", "Admin access escalation detected for user 9429"),
        ("LegacyCRM", "Case escalation for ticket ID 7324 failed because the assigned support agent is no longer active."),
        ("LegacyCRM", "Invoice generation process aborted for order ID 8910 due to invalid tax calculation module."),
        ("LegacyCRM", "The 'BulkEmailSender' feature is no longer supported. Use 'EmailCampaignManager' for improved functionality."),
        ("LegacyCRM", " The 'ReportGenerator' module will be retired in version 4.0. Please migrate to the 'AdvancedAnalyticsSuite' by Dec 2025"),
        ("ModernHR", " testing 123")
    ]

    for source, log_message in log_messages:
        print(f"Source :{source} Log: {log_message} => Category: {classify_logs(source, log_message)}")
         """