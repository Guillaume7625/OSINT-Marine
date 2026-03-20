import queue
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pythoncom
import win32com.client

from .util_text import clean_body, truncate


@dataclass
class EmailItem:
    entry_id: str
    subject: str
    sender_email: str
    sender_name: str
    received_time: str
    body_excerpt: str
    to_cc: str
    attachments: List[str]


class OutlookWorker:
    def __init__(self) -> None:
        self._queue: "queue.Queue" = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        pythoncom.CoInitialize()
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        try:
            while True:
                task = self._queue.get()
                if task is None:
                    break
                func, args, kwargs, event, container = task
                try:
                    container["result"] = func(outlook, *args, **kwargs)
                except Exception as exc:
                    container["error"] = exc
                finally:
                    event.set()
        finally:
            pythoncom.CoUninitialize()

    def submit(self, func, *args, **kwargs):
        event = threading.Event()
        container: Dict[str, Any] = {"result": None, "error": None}
        self._queue.put((func, args, kwargs, event, container))
        event.wait()
        if container["error"]:
            raise container["error"]
        return container["result"]


class OutlookClient:
    def __init__(self) -> None:
        self.worker = OutlookWorker()

    def _get_inbox(self, outlook):
        return outlook.GetDefaultFolder(6)

    def _get_or_create_folder(self, inbox, name: str):
        for folder in inbox.Folders:
            if folder.Name == name:
                return folder
        return inbox.Folders.Add(name)

    def _get_sender_email(self, item) -> str:
        sender_email = getattr(item, "SenderEmailAddress", "") or ""
        if sender_email and "@" in sender_email:
            return sender_email
        try:
            return item.PropertyAccessor.GetProperty("http://schemas.microsoft.com/mapi/proptag/0x39FE001E")
        except Exception:
            return sender_email

    def _fetch_messages(self, outlook, limit: int, days_window: int) -> List[EmailItem]:
        inbox = self._get_inbox(outlook)
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        restricted = items.Restrict("[Unread] = True")
        cutoff = datetime.now() - timedelta(days=days_window)

        results: List[EmailItem] = []
        for item in restricted:
            try:
                received = item.ReceivedTime
                if hasattr(received, "replace"):
                    received_dt = received
                else:
                    received_dt = datetime.fromtimestamp(int(received))
                if received_dt < cutoff:
                    break
                sender_email = self._get_sender_email(item)
                sender_name = getattr(item, "SenderName", "") or ""
                subject = getattr(item, "Subject", "") or ""
                body = getattr(item, "Body", "") or ""
                to_cc = ""
                try:
                    to_cc = f"{getattr(item, 'To', '')} {getattr(item, 'CC', '')}".strip()
                except Exception:
                    to_cc = ""
                attachments = []
                try:
                    for att in item.Attachments:
                        attachments.append(att.FileName)
                except Exception:
                    attachments = []
                body_excerpt = truncate(clean_body(body), 1000)
                results.append(
                    EmailItem(
                        entry_id=item.EntryID,
                        subject=subject,
                        sender_email=sender_email,
                        sender_name=sender_name,
                        received_time=received_dt.isoformat(),
                        body_excerpt=body_excerpt,
                        to_cc=to_cc,
                        attachments=attachments,
                    )
                )
                if len(results) >= limit:
                    break
            except Exception:
                continue
        return results

    def fetch_messages(self, limit: int, days_window: int) -> List[EmailItem]:
        return self.worker.submit(self._fetch_messages, limit, days_window)

    def _move_message(self, outlook, entry_id: str, target_folder: str) -> bool:
        inbox = self._get_inbox(outlook)
        dest = self._get_or_create_folder(inbox, target_folder)
        item = outlook.GetItemFromID(entry_id)
        item.Move(dest)
        return True

    def move_message(self, entry_id: str, target_folder: str) -> bool:
        return self.worker.submit(self._move_message, entry_id, target_folder)

    def _create_summary_draft(self, outlook, subject: str, body: str, folder_name: Optional[str]) -> bool:
        mail = outlook.Application.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        if folder_name:
            inbox = self._get_inbox(outlook)
            dest = self._get_or_create_folder(inbox, folder_name)
            mail.Save()
            mail.Move(dest)
        else:
            mail.Save()
        return True

    def create_summary_draft(self, subject: str, body: str, folder_name: Optional[str] = None) -> bool:
        return self.worker.submit(self._create_summary_draft, subject, body, folder_name)
