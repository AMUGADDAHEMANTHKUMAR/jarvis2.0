import win32com.client

def get_emails(count=10):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        inbox = ns.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        emails = []
        for i, msg in enumerate(messages):
            if i >= count: break
            emails.append({
                "from":    msg.SenderName,
                "subject": msg.Subject,
                "received": str(msg.ReceivedTime),
                "preview": msg.Body[:200] if msg.Body else ""
            })
        return emails
    except Exception as e:
        return [{"error": str(e)}]