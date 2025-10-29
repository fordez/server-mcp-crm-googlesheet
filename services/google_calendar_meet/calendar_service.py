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

CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "meet-credentials.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.json")
TIMEZONE = os.getenv(
    "TIMEZONE", "America/Argentina/Buenos_Aires"
)  # 🔹 Zona horaria del .env

# ⚠️ Scopes fijos para Calendar/Meet
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/meetings.space.created",
]


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
            # Hay solapamiento
            return {
                "success": False,
                "error": "Horario no disponible, ya existe un evento en ese rango",
                "busy_slots": busy_slots,
            }

        # Crear evento solo si está libre
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

        # 🔹 Imprimir en consola
        logger.info(f"✅ Evento creado | ID: {event_id} | Link: {calendar_link}")

        return {
            "success": True,
            "event_id": event_id,  # ID real para buscar/modificar el evento
            "meet_link": meet_link,  # Link de Meet
            "calendar_link": calendar_link,  # Link de Calendar
            "summary": event["summary"],
        }

    # -------------------------------------------------
    @staticmethod
    def check_availability():
        """Retorna los espacios libres entre 8 a.m. y 5 p.m. de los próximos 3 días hábiles con disponibilidad."""
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

        # Buscar 3 días hábiles con huecos disponibles
        while dias_encontrados < 3 and offset < 14:
            date = now.date() + timedelta(days=offset)

            # Saltar sábados (5) y domingos (6)
            if date.weekday() >= 5:
                offset += 1
                continue

            start_day, end_day, label = day_range(offset)
            start = max(now, start_day) if offset == 0 else start_day

            if start >= end_day:
                offset += 1
                continue

            # Consultar eventos ocupados
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

            # Formatear resultado
            slots_fmt = [
                {
                    "inicio": s.strftime("%I:%M %p"),
                    "fin": e.strftime("%I:%M %p"),
                    "inicio_iso": s.isoformat(),
                    "fin_iso": e.isoformat(),
                }
                for s, e in free_slots
                if (e - s).total_seconds() >= 900  # mínimo 15 minutos
            ]

            if slots_fmt:
                disponibilidad.append({"dia": label, "espacios_libres": slots_fmt})
                dias_encontrados += 1

            offset += 1

        return disponibilidad

    @staticmethod
    def get_event_details(event_id: str):
        """
        Obtiene los detalles de un evento dado su event_id.
        Retorna información como resumen, inicio, fin, asistentes y link.
        """
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
