import json, os, time, re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from config import SPREADSHEET_ID, SHEET_NAME, TOKEN_PATH, COL_INDEX, get_spreadsheet_id
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def get_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f"No se encuentra el token en {TOKEN_PATH}. "
            "Ejecuta 'python campaign_runner.py --auth' primero."
        )
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token_info = json.load(f)
    creds = Credentials.from_authorized_user_info(token_info)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(json.loads(creds.to_json()), f, indent=2)
    return creds


def sheets_service():
    creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


class EmpresaCandidata:
    # Prefijos de emails role-based que se evitan (info@, admin@, etc.)
    EMAIL_BLACKLIST = {
        "info", "admin", "contact", "contacto", "hello", "hola",
        "support", "soporte", "sales", "ventas", "comercial",
        "marketing", "press", "prensa", "careers", "trabajo",
        "no-reply", "newsletter", "mail", "correo", "webmaster",
        "noc", "help", "helpdesk", "hr", "rrhh",
    }

    def __init__(self, raw_values: list[str], row_number: int):
        self.row_number = row_number
        self.row_values = raw_values

    def _get(self, key: str) -> str:
        idx = COL_INDEX.get(key)
        if idx is not None and idx < len(self.row_values):
            return (self.row_values[idx] or "").strip()
        return ""

    @property
    def nombre(self):
        return self._get("empresa")

    @property
    def provincia(self):
        return self._get("provincia")

    @property
    def web(self):
        return self._get("web")

    @property
    def email(self):
        return self._get("email")

    @property
    def telefono(self):
        return self._get("telefono")

    @property
    def categoria(self):
        return self._get("categoria")

    @property
    def estado(self):
        return self._get("estado").lower()

    @property
    def ultimo_contacto(self):
        val = self._get("ultimo_contacto")
        return self._parse_date(val)

    @property
    def proxima_accion(self):
        val = self._get("proxima_accion")
        return self._parse_date(val)

    @property
    def num_contactos(self):
        val = self._get("num_contactos")
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    @property
    def problema(self):
        return self._get("problema")

    @property
    def idea_mejora(self):
        return self._get("idea_mejora")

    @property
    def tamano(self):
        return self._get("tamano")

    @property
    def prioridad(self):
        return self._get("prioridad")

    def contexto_completo(self) -> str:
        """Devuelve toda la informacion disponible de la fila como texto para pasarselo a la IA."""
        partes = []
        raw = self.row_values
        labels = {
            0: "Nombre",
            1: "Provincia",
            2: "Categoria",
            3: "Web",
            4: "Email",
            5: "Telefono",
            6: "Rating",
            7: "Total reviews",
            8: "Reseñas clientes",
            9: "Direccion",
            10: "Coordenadas",
            11: "Google Maps URL",
            12: "Estado",
            13: "Ultimo contacto",
            14: "Proxima accion",
            16: "Problema detectado",
            17: "Idea de mejora",
            18: "Prioridad",
            19: "Notas",
            20: "Tamano",
            21: "Numero contactos",
        }
        for idx, label in labels.items():
            if idx < len(raw) and raw[idx]:
                valor = raw[idx].strip()
                # Omitir campos vacios o que no aportan
                if valor and valor.lower() not in ("", "no encontrado", "no especificado"):
                    partes.append(f"{label}: {valor}")
        return "\n".join(partes)

    def _parse_date(self, val: str):
        if not val:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
        return None

    def _extraer_emails(self) -> list[str]:
        """Devuelve lista de emails individuales desde la celda (separados por coma/punto y coma)."""
        raw = self._get("email")
        if not raw or raw.lower() in ("no encontrado", "", "sin email"):
            return []
        partes = re.split(r'[,;]', raw)
        validos = []
        for p in partes:
            p = p.strip()
            if re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", p):
                validos.append(p.lower())
        return validos

    def _es_role_based(self, email: str) -> bool:
        """True si el email es role-based (info@, admin@, etc.)."""
        local = email.split("@")[0].lower().strip()
        return local in self.EMAIL_BLACKLIST

    def mejor_email(self) -> str | None:
        """
        Selecciona el mejor email de la empresa:
        1. Excluye role-based (info@, admin@, etc.)
        2. Si solo hay role-based, usa el primero
        3. Si no hay ninguno, None
        """
        emails = self._extraer_emails()
        if not emails:
            return None
        no_role = [e for e in emails if not self._es_role_based(e)]
        if no_role:
            return no_role[0]
        return emails[0]

    def tiene_email_valido(self) -> bool:
        return self.mejor_email() is not None

    def contiene_email(self, email_buscado: str) -> bool:
        """Verifica si el email de la empresa contiene el email buscado (soporta multiples emails separados por coma)."""
        buscado = email_buscado.strip().lower()
        if not buscado:
            return False
        return buscado in self._extraer_emails()

    def necesita_touch(self, hoy: date) -> int | None:
        """Devuelve el numero de touch que necesita (1-5) o None si no necesita."""
        estado = self.estado

        if estado in ("respondido", "rebotado", "descartado"):
            return None

        touch_actual = self.num_contactos

        if touch_actual >= 5:
            return None

        if touch_actual == 0:
            # Nunca contactado
            if estado in ("", "pendiente"):
                return 1
            return None

        # Ya tiene algun touch, verificar si toca el siguiente
        ultimo = self.ultimo_contacto
        if ultimo is None:
            return None

        # El gap es el del SIGUIENTE touch (el que se va a enviar)
        from config import TOUCH_GAPS
        gap = TOUCH_GAPS.get(touch_actual + 1, 7)
        dias_desde_ultimo = (hoy - ultimo).days

        if dias_desde_ultimo >= gap:
            return touch_actual + 1

        return None


def leer_empresas(service) -> list[EmpresaCandidata]:
    """Lee todas las filas de TEST EMPRESAS BOT 2 y devuelve lista de candidatas."""
    result = service.spreadsheets().values().get(
        spreadsheetId=get_spreadsheet_id(),
        range=f"'{SHEET_NAME}'!A2:V2000"
    ).execute()

    raw = result.get("values", [])
    empresas = []
    for i, row in enumerate(raw):
        if not row or not row[0]:
            continue
        empresas.append(EmpresaCandidata(row, i + 2))  # +2 por header + 0-index

    return empresas


def local_hoy() -> date:
    from config import TIMEZONE
    return datetime.now(ZoneInfo(TIMEZONE)).date()


def roll_to_monday(day: date) -> date:
    if day.weekday() == 5:
        return day + timedelta(days=2)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def siguiente_fecha_envio(desde: date, gap_dias: int) -> date:
    """Calcula la fecha del proximo envio evitando fines de semana."""
    fecha = desde + timedelta(days=gap_dias)
    return roll_to_monday(fecha)


def actualizar_tracking(service, candidato: EmpresaCandidata, touch: int, hoy: date, asunto: str):
    """Actualiza las columnas de tracking en el Sheet."""
    from config import TOUCH_GAPS

    proximo_touch = touch + 1
    gap_siguiente = TOUCH_GAPS.get(proximo_touch, 7)
    prox_accion = siguiente_fecha_envio(hoy, gap_siguiente)

    updates = {}
    state_name = f"email_{touch}"
    updates["estado"] = state_name
    updates["ultimo_contacto"] = hoy.isoformat()
    updates["proxima_accion"] = prox_accion.isoformat()
    updates["num_contactos"] = str(touch)

    for col_key, str_value in updates.items():
        col_idx = COL_INDEX.get(col_key)
        if col_idx is None:
            continue
        col_letter = chr(65 + col_idx)  # A=0, B=1, etc.
        cell_range = f"'{SHEET_NAME}'!{col_letter}{candidato.row_number}"
        try:
            service.spreadsheets().values().update(
                spreadsheetId=get_spreadsheet_id(),
                range=cell_range,
                valueInputOption="USER_ENTERED",
                body={"values": [[str_value]]}
            ).execute()
        except Exception as e:
            print(f"  [WARN] Error actualizando {cell_range}: {e}")

    print(f"  [SHEET] Fila {candidato.row_number} actualizada: estado={state_name}, touch={touch}")


def marcar_respondido(service, nombre_empresa: str, fecha_respuesta: str):
    """Busca la empresa por nombre y marca como respondido."""
    empresas = leer_empresas(service)
    for emp in empresas:
        if emp.nombre.strip().lower() == nombre_empresa.strip().lower():
            col_estado = COL_INDEX.get("estado")
            if col_estado is not None:
                col_letter = chr(65 + col_estado)
                cell = f"'{SHEET_NAME}'!{col_letter}{emp.row_number}"
                service.spreadsheets().values().update(
                    spreadsheetId=get_spreadsheet_id(),
                    range=cell,
                    valueInputOption="USER_ENTERED",
                    body={"values": [["respondido"]]}
                ).execute()
                print(f"  [SHEET] {nombre_empresa} marcada como respondido")
            return True
    return False
