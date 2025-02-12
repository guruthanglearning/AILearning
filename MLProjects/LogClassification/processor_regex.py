import re
def classify_with_regex(log_message):
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
        print(f"Log: {log} => Category: {classify_with_regex(log)}")