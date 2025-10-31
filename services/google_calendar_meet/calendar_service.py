# services/google_calendar_meet/calendar_service.py
import os
import json
import logging
import pytz
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

load_dotenv()
logger = logging.getLogger(__name__)

TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

# ⚠️ Scopes fijos para Calendar/Meet
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/meetings.space.created",
]


class CalendarService:
    _service = None

    # -------------------------------------------------
    @staticmethod
    def get_token_path() -> str:
        """Detecta entorno y retorna la ruta correcta del token."""
        env = os.getenv("ENVIRONMENT", "production").lower()
        if env == "development":
            path = os.getenv("TOKEN_FILE_DEV", "secrets/token-dev.json")
        else:
            path = os.getenv("TOKEN_FILE_PROD", "secrets/token-prod.json")

        logger.info(f"🧩 Entorno detectado: {env} → usando token: {path}")
        return path

    # -------------------------------------------------
    @staticmethod
    def get_credentials():
        """Carga las credenciales internas del servidor sin flujo OAuth."""
        token_path = CalendarService.get_token_path()

        if not os.path.exists(token_path):
            raise FileNotFoundError(f"❌ No existe el token interno: {token_path}")

        # Leer archivo y validar contenido
        with open(token_path, "r") as token_file:
            content = token_file.read().strip()
            if not content:
                raise ValueError(f"⚠️ El token {token_path} está vacío o corrupto.")
            try:
                creds_data = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(
                    f"⚠️ El token {token_path} tiene formato JSON inválido."
                )

        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        return creds

    # -------------------------------------------------
    @staticmethod
    def get_service():
        """Singleton del servicio de Calendar autenticado internamente."""
        if CalendarService._service is None:
            creds = CalendarService.get_credentials()
            CalendarService._service = build("calendar", "v3", credentials=creds)
        return CalendarService._service

    # -------------------------------------------------
    @staticmethod
    def create_meet_event(
        summary, start_time, end_time, attendees=None, description=None
    ):
        """Crea un evento con enlace de Meet usando token interno y valida disponibilidad."""
        service = CalendarService.get_service()
        tz = pytz.timezone(TIMEZONE)

        # Convertir a datetime con tz si no lo están
        if isinstance(start_time, datetime):
            start_time = start_time.astimezone(tz)
        else:
            start_time = datetime.fromisoformat(start_time).astimezone(tz)

        if isinstance(end_time, datetime):
            end_time = end_time.astimezone(tz)
        else:
            end_time = datetime.fromisoformat(end_time).astimezone(tz)

        # 🔹 Validar disponibilidad
        result = (
            service.freebusy()
            .query(
                body={
                    "timeMin": start_time.isoformat(),
                    "timeMax": end_time.isoformat(),
                    "items": [{"id": "primary"}],
                }
            )
            .execute()
        )
        busy_slots = result["calendars"]["primary"].get("busy", [])
        if busy_slots:
            return {
                "success": False,
                "error": "Horario no disponible, ya existe un evento en ese rango",
                "busy_slots": busy_slots,
            }

        # Crear evento
        event = {
            "summary": summary,
            "description": description or "Evento creado automáticamente con Meet.",
            "start": {"dateTime": start_time.isoformat(), "timeZone": TIMEZONE},
            "end": {"dateTime": end_time.isoformat(), "timeZone": TIMEZONE},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{os.urandom(4).hex()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "attendees": [{"email": e} for e in (attendees or [])],
        }

        event = (
            service.events()
            .insert(calendarId="primary", body=event, conferenceDataVersion=1)
            .execute()
        )

        event_id = event["id"]
        meet_link = (
            event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
        )
        calendar_link = event.get("htmlLink")

        logger.info(f"✅ Evento creado | ID: {event_id} | Link: {calendar_link}")

        return {
            "success": True,
            "event_id": event_id,
            "meet_link": meet_link,
            "calendar_link": calendar_link,
            "summary": event["summary"],
        }

    # -------------------------------------------------
    @staticmethod
    def check_availability():
        """Retorna los espacios libres entre 8 a.m. y 5 p.m. de los próximos 3 días hábiles."""
        service = CalendarService.get_service()
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)

        def day_range(offset):
            date = now.date() + timedelta(days=offset)
            start_day = datetime.combine(date, time(8, 0)).replace(tzinfo=tz)
            end_day = datetime.combine(date, time(17, 0)).replace(tzinfo=tz)
            label = date.strftime("%A %d/%m/%Y")
            return start_day, end_day, label

        disponibilidad = []
        offset = 0
        dias_encontrados = 0

        while dias_encontrados < 3 and offset < 14:
            date = now.date() + timedelta(days=offset)

            if date.weekday() >= 5:  # Saltar sábados y domingos
                offset += 1
                continue

            start_day, end_day, label = day_range(offset)
            start = max(now, start_day) if offset == 0 else start_day

            if start >= end_day:
                offset += 1
                continue

            result = (
                service.freebusy()
                .query(
                    body={
                        "timeMin": start.isoformat(),
                        "timeMax": end_day.isoformat(),
                        "items": [{"id": "primary"}],
                    }
                )
                .execute()
            )

            busy_slots = result["calendars"]["primary"].get("busy", [])
            free_slots = []
            current_time = start

            for slot in busy_slots:
                s = datetime.fromisoformat(slot["start"]).astimezone(tz)
                e = datetime.fromisoformat(slot["end"]).astimezone(tz)
                if e <= start or s >= end_day:
                    continue
                if current_time < s:
                    free_slots.append((current_time, s))
                current_time = max(current_time, e)

            if current_time < end_day:
                free_slots.append((current_time, end_day))

            slots_fmt = [
                {
                    "inicio": s.strftime("%I:%M %p"),
                    "fin": e.strftime("%I:%M %p"),
                    "inicio_iso": s.isoformat(),
                    "fin_iso": e.isoformat(),
                }
                for s, e in free_slots
                if (e - s).total_seconds() >= 900
            ]

            if slots_fmt:
                disponibilidad.append({"dia": label, "espacios_libres": slots_fmt})
                dias_encontrados += 1

            offset += 1

        return disponibilidad

    # -------------------------------------------------
    @staticmethod
    def get_event_details(event_id: str):
        """Obtiene los detalles de un evento dado su event_id."""
        service = CalendarService.get_service()
        try:
            event = (
                service.events().get(calendarId="primary", eventId=event_id).execute()
            )
            tz = pytz.timezone(TIMEZONE)

            start = datetime.fromisoformat(event["start"].get("dateTime")).astimezone(
                tz
            )
            end = datetime.fromisoformat(event["end"].get("dateTime")).astimezone(tz)
            attendees = [a.get("email") for a in event.get("attendees", [])]
            meet_link = (
                event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
            )

            return {
                "event_id": event["id"],
                "summary": event["summary"],
                "description": event.get("description"),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "attendees": attendees,
                "calendar_link": event.get("htmlLink"),
                "meet_link": meet_link,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
