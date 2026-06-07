import json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from config import SHEET_NAME, TOKEN_PATH, COL_INDEX, get_spreadsheet_id


def get_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f"No se encuentra el token en {TOKEN_PATH}. "
            "Copialo desde busqueda-emails/google_token_sheets.json"
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


class Empresa:
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
    def categoria(self):
        return self._get("categoria")

    @property
    def web(self):
        return self._get("web")

    @property
    def problema(self):
        return self._get("problema")

    @property
    def idea_mejora(self):
        return self._get("idea_mejora")

    @property
    def tamano(self):
        return self._get("tamano")

    def tiene_enriquecimiento(self) -> bool:
        return bool(self.problema) and bool(self.idea_mejora) and bool(self.tamano)

    def __repr__(self):
        return f"<Empresa row={self.row_number}: {self.nombre}>"


def leer_empresas(service) -> list[Empresa]:
    """Lee todas las filas del sheet y devuelve lista de empresas."""
    result = service.spreadsheets().values().get(
        spreadsheetId=get_spreadsheet_id(),
        range=f"'{SHEET_NAME}'!A2:V2000"
    ).execute()

    raw = result.get("values", [])
    empresas = []
    for i, row in enumerate(raw):
        if not row or not row[0]:
            continue
        empresas.append(Empresa(row, i + 2))
    return empresas


def leer_pendientes(service) -> list[Empresa]:
    """Devuelve solo empresas que NO tengan Q, R y U rellenos."""
    return [e for e in leer_empresas(service) if not e.tiene_enriquecimiento()]


def escribir_resultados(service, empresa: Empresa, problema: str, mejora: str, tamano: str, notas: str = ""):
    """Escribe problema (Q), mejora (R), tamano (U) y notas (T) en el sheet en un solo batch."""
    sid = get_spreadsheet_id()
    data = []
    fields = [
        ("problema", problema[:150]),
        ("idea_mejora", mejora[:150]),
        ("tamano", tamano[:100]),
    ]
    if notas:
        fields.append(("notas", notas[:500]))

    for col_key, str_value in fields:
        col_idx = COL_INDEX.get(col_key)
        if col_idx is None:
            continue
        col_letter = chr(65 + col_idx)
        cell_range = f"'{SHEET_NAME}'!{col_letter}{empresa.row_number}"
        data.append({"range": cell_range, "values": [[str_value]]})

    if not data:
        return

    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sid,
            body={"valueInputOption": "RAW", "data": data}
        ).execute()
    except Exception as e:
        print(f"  [WARN] Error en batchUpdate: {e}")
