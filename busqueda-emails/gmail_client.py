import base64, os, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import FROM_EMAIL
from sheets_tracker import get_credentials


def gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def send_email(service, to_email: str, subject: str, body_text: str, thread_id: str = None) -> tuple[bool, str]:
    if not to_email or not re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", to_email):
        return False, "Email invalido"

    message = MIMEText(body_text, "plain", "utf-8")
    message["To"] = to_email
    message["From"] = FROM_EMAIL
    message["Subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    body = {"raw": raw}
    if thread_id:
        body["threadId"] = thread_id

    try:
        sent = service.users().messages().send(userId="me", body=body).execute()
        msg_id = sent.get("id", "")
        thread_id_result = sent.get("threadId", "")
        print(f"  [GMAIL] Enviado a {to_email} | msg_id={msg_id} thread={thread_id_result}")
        return True, msg_id
    except HttpError as e:
        error_text = str(e)
        print(f"  [GMAIL ERROR] {error_text}")
        return False, error_text


def create_draft(service, to_email: str, subject: str, body_text: str) -> str | None:
    """
    Crea un borrador en Gmail con firma HTML con imagen.
    """
    if not to_email or not re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", to_email):
        print(f"  [DRAFT] Email invalido: {to_email}")
        return None

    sig_html = ""
    sig_file = Path(os.path.join(os.path.dirname(__file__), "html_firma.txt"))
    if sig_file.exists():
        sig_html = sig_file.read_text(encoding="utf-8")

    import email_composer
    if body_text.endswith(email_composer.FIRMA):
        body_text = body_text[: -len(email_composer.FIRMA)].strip()

    body_html = "".join(f"<p>{line.strip()}</p>" for line in body_text.splitlines() if line.strip())

    sig_html = sig_html.replace("AQUI_TU_IMAGEN", "cid:silvigon-signature")

    full_html = body_html + sig_html
    text_plain = re.sub(r"<[^>]+>", "", full_html)

    message = MIMEMultipart("related")
    message["To"] = to_email
    message["From"] = FROM_EMAIL
    message["Subject"] = subject

    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text_plain, "plain", "utf-8"))
    alternative.attach(MIMEText(full_html, "html", "utf-8"))
    message.attach(alternative)

    img_file = Path(os.path.join(os.path.dirname(__file__), "Firma Silvigon.png"))
    if img_file.exists():
        with open(str(img_file), "rb") as f:
            img = MIMEImage(f.read())
        img.add_header("Content-ID", "<silvigon-signature>")
        img.add_header("Content-Disposition", 'inline; filename="Firma Silvigon.png"')
        img.add_header("Content-Type", 'image/png; name="Firma Silvigon.png"')
        message.attach(img)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    try:
        result = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}}
        ).execute()
        draft_id = result.get("id", "")
        print(f"  [DRAFT] Creado borrador para {to_email} | draft_id={draft_id}")
        return draft_id
    except HttpError as e:
        print(f"  [DRAFT ERROR] {e}")
        return None


def detectar_respuestas(service, max_results: int = 50) -> list[dict]:
    """
    Busca en el inbox emails recibidos (no enviados por nosotros) de los ultimos 2 dias.
    Retorna lista de dicts con info de cada respuesta.
    """
    query = f"to:{FROM_EMAIL} -from:{FROM_EMAIL} is:unread newer_than:2d"

    try:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()
    except HttpError as e:
        print(f"  [GMAIL ERROR] detectar_respuestas: {e}")
        return []

    messages = result.get("messages", [])
    if not messages:
        return []

    respuestas = []
    for msg in messages:
        try:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
            from_header = headers.get("From", "")
            subject = headers.get("Subject", "")
            date = headers.get("Date", "")
            snippet = msg_data.get("snippet", "")
            thread_id = msg_data.get("threadId", "")

            # Extraer email del From header
            match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', from_header)
            email_origen = match.group(0) if match else from_header

            respuestas.append({
                "thread_id": thread_id,
                "email_origen": email_origen,
                "from_raw": from_header,
                "subject": subject,
                "snippet": snippet,
                "date": date,
                "msg_id": msg["id"],
            })

            # Marcar como leido para no re-procesar
            try:
                service.users().messages().modify(
                    userId="me",
                    id=msg["id"],
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            except Exception:
                pass

        except Exception as e:
            print(f"  [WARN] Error procesando mensaje {msg.get('id')}: {e}")

    return respuestas


def obtener_thread_id_por_email(service, email_destino: str) -> str | None:
    """
    Busca el thread_id de la conversacion mas reciente hacia un email destino.
    Se usa para enviar follow-ups como replies en lugar de nuevos emails.
    Busca en la carpeta de enviados (SENT).
    """
    query = f"to:{email_destino}"
    try:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=1,
            labelIds=["SENT"]
        ).execute()
        messages = result.get("messages", [])
        if messages:
            msg = service.users().messages().get(
                userId="me",
                id=messages[0]["id"],
                format="minimal"
            ).execute()
            return msg.get("threadId")
    except Exception:
        pass
    return None
