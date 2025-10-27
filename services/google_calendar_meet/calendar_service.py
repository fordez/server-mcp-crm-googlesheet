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

CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "credentials.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token_server.json")
SCOPES = os.getenv("SCOPES", "").split(",")


class CalendarService:
    _service = None

    @staticmethod
    def get_credentials():
        """Carga las credenciales internas del servidor sin flujo OAuth."""
        if not os.path.exists(TOKEN_FILE):
            raise FileNotFoundError(
                f"❌ No existe el token interno: {TOKEN_FILE}. Genera uno manualmente."
            )
        with open(TOKEN_FILE, "r") as token_file:
            creds_data = json.load(token_file)
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        return creds

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
        """Crea un evento con enlace de Meet usando token interno."""
        service = CalendarService.get_service()

        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()

        event = {
            "summary": summary,
            "description": description or "Evento creado automáticamente con Meet.",
            "start": {"dateTime": start_time, "timeZone": "America/Bogota"},
            "end": {"dateTime": end_time, "timeZone": "America/Bogota"},
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

        meet_link = (
            event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
        )
        logger.info(f"✅ Evento creado: {event.get('htmlLink')}")

        return {
            "event_id": event["id"],
            "meet_link": meet_link,
            "calendar_link": event["htmlLink"],
            "summary": event["summary"],
        }

    # -------------------------------------------------
    @staticmethod
    def get_event_details(event_id):
        """Obtiene detalles completos de un evento."""
        service = CalendarService.get_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()

        meet_link = (
            event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
        )
        return {
            "summary": event.get("summary"),
            "description": event.get("description"),
            "start": event["start"]["dateTime"],
            "end": event["end"]["dateTime"],
            "meet_link": meet_link,
            "htmlLink": event.get("htmlLink"),
            "attendees": [a["email"] for a in event.get("attendees", [])],
        }

    # -------------------------------------------------
    @staticmethod
    def check_availability():
        """Retorna los espacios libres entre 8am y 5pm de los próximos 3 días hábiles disponibles."""
        service = CalendarService.get_service()
        tz = pytz.timezone("America/Bogota")
        now = datetime.now(tz)

        def day_range(offset):
            date = now.date() + timedelta(days=offset)
            start_day = datetime.combine(date, time(8, 0)).replace(tzinfo=tz)
            end_day = datetime.combine(date, time(17, 0)).replace(tzinfo=tz)
            return start_day, end_day, date.strftime("%A %d/%m/%Y")

        disponibilidad = []
        offset = 0
        dias_encontrados = 0

        # Buscar 3 días hábiles con huecos, empezando desde hoy
        while dias_encontrados < 3 and offset < 14:
            start_day, end_day, label = day_range(offset)
            start = max(now, start_day) if offset == 0 else start_day

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
                if s < e
            ]

            if slots_fmt:
                disponibilidad.append({"dia": label, "espacios_libres": slots_fmt})
                dias_encontrados += 1

            offset += 1

        return disponibilidad
