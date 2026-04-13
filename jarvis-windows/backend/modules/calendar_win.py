import win32com.client
from datetime import datetime, timedelta

def get_events(days_ahead=7):
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
        cal = ns.GetDefaultFolder(9)
        items = cal.Items
        items.Sort("[Start]")
        items.IncludeRecurrences = True

        start = datetime.now()
        end   = start + timedelta(days=days_ahead)
        items = items.Restrict(
            f"[Start] >= '{start.strftime('%m/%d/%Y')}' AND [Start] <= '{end.strftime('%m/%d/%Y')}'"
        )

        events = []
        for item in items:
            events.append({
                "subject": item.Subject,
                "start":   str(item.Start),
                "end":     str(item.End),
                "location": item.Location or ""
            })
        return events
    except Exception as e:
        return [{"error": str(e)}]