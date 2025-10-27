import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz
from datetime import datetime, timedelta, time


# --- CONFIGURACIÓN GLOBAL ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "credentials.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token_calendar.json")

# 🔧 Ahora leemos los scopes desde el .env dinámicamente
SCOPES = os.getenv("SCOPES", "").split(",")


# --- FUNCIÓN 1: AUTENTICACIÓN ---
def get_credentials():
    """
    Inicia sesión con OAuth2 y guarda el token localmente.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as token_file:
                creds_data = json.load(token_file)
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        except Exception:
            logging.warning("Token inválido o corrupto. Se generará uno nuevo.")

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        logging.info("🔐 Token guardado correctamente.")

    return creds


# --- FUNCIÓN 2: CREAR EVENTO CON MEET ---
def create_meet_event(summary, start_time, end_time, attendees=None, description=None):
    """
    Crea un evento en Google Calendar con enlace de Google Meet.
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    if isinstance(start_time, datetime):
        start_time = start_time.isoformat()
    if isinstance(end_time, datetime):
        end_time = end_time.isoformat()

    event = {
        "summary": summary,
        "description": description
        or "Evento con enlace de Meet creado automáticamente.",
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

    meet_link = event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
    logging.info(f"✅ Evento creado: {event.get('htmlLink')}")
    logging.info(f"🔗 Enlace Meet: {meet_link}")

    return {
        "event_id": event["id"],
        "meet_link": meet_link,
        "calendar_link": event["htmlLink"],
    }


# --- FUNCIÓN 4: OBTENER DETALLES DE UN EVENTO ---
def get_event_details(event_id):
    """
    Recupera detalles completos del evento, incluido el enlace Meet.
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    meet_link = event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
    details = {
        "summary": event.get("summary"),
        "description": event.get("description"),
        "start": event["start"]["dateTime"],
        "end": event["end"]["dateTime"],
        "meet_link": meet_link,
        "htmlLink": event.get("htmlLink"),
        "attendees": [a["email"] for a in event.get("attendees", [])],
    }

    logging.info(f"📄 Detalles del evento: {json.dumps(details, indent=2)}")
    return details


def check_availability():
    """
    Devuelve e imprime los espacios libres entre 8:00am y 5:00pm
    para hoy y mañana (hora Colombia). No incluye horas ya pasadas.
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    tz = pytz.timezone("America/Bogota")
    now = datetime.now(tz)

    def day_range(offset):
        date = now.date() + timedelta(days=offset)
        start_day = datetime.combine(date, time(8, 0)).replace(tzinfo=tz)
        end_day = datetime.combine(date, time(17, 0)).replace(tzinfo=tz)
        return start_day, end_day, date.strftime("%A %d/%m/%Y")

    disponibilidad = []

    for offset in [0, 1]:  # 0 = hoy, 1 = mañana
        start_day, end_day, label = day_range(offset)

        # Si es hoy, no considerar horas anteriores a 'now'
        if offset == 0 and now > start_day:
            start = now
        else:
            start = start_day
        end = end_day

        # Si el inicio ya pasó del rango, no hay slots
        if start >= end:
            disponibilidad.append(
                {"dia": label, "fecha": start.date().isoformat(), "espacios_libres": []}
            )
            print(f"\n📅 {label} (8:00 AM - 5:00 PM)")
            print("🔴 Rango ya pasado o sin tiempo disponible.")
            continue

        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": "primary"}],
        }

        result = service.freebusy().query(body=body).execute()
        busy_slots = result["calendars"]["primary"].get("busy", [])

        # Construir huecos libres entre start..end usando busy_slots ordenados
        free_slots = []
        current_time = start

        # busy_slots vienen ordenados por la API, pero por seguridad los ordenamos
        # además convertimos a datetimes tz-aware y descartamos entradas sin dateTime
        busy_intervals = []
        for slot in busy_slots:
            s_raw = slot.get("start")
            e_raw = slot.get("end")
            try:
                s_dt = datetime.fromisoformat(s_raw).astimezone(tz)
                e_dt = datetime.fromisoformat(e_raw).astimezone(tz)
            except Exception:
                # si no podemos parsear (p.e. all-day), saltamos
                continue
            # ignorar eventos que terminan antes del inicio del rango
            if e_dt <= start:
                continue
            # cortar eventos que comienzan después del fin
            if s_dt >= end:
                continue
            # recortar a los límites del rango
            s_dt = max(s_dt, start)
            e_dt = min(e_dt, end)
            busy_intervals.append((s_dt, e_dt))

        # merge intervals en caso de solapamientos (defensivo)
        busy_intervals.sort(key=lambda x: x[0])
        merged = []
        for s, e in busy_intervals:
            if not merged:
                merged.append((s, e))
            else:
                last_s, last_e = merged[-1]
                if s <= last_e:
                    merged[-1] = (last_s, max(last_e, e))
                else:
                    merged.append((s, e))

        for s_busy, e_busy in merged:
            if current_time < s_busy:
                free_slots.append((current_time, s_busy))
            current_time = max(current_time, e_busy)

        # después del último evento
        if current_time < end:
            free_slots.append((current_time, end))

        # Formatear la salida
        slots_formatted = [
            {
                "inicio_iso": s.isoformat(),
                "fin_iso": e.isoformat(),
                "inicio_hora": s.strftime("%I:%M %p"),
                "fin_hora": e.strftime("%I:%M %p"),
            }
            for s, e in free_slots
        ]

        disponibilidad.append(
            {
                "dia": label,
                "fecha": start_day.date().isoformat(),
                "espacios_libres": slots_formatted,
            }
        )

        # Imprimir resumen legible
        print(f"\n📅 {label} (8:00 AM - 5:00 PM)")
        if not slots_formatted:
            print("🔴 No hay espacios libres en este rango.")
        else:
            print("🟢 Espacios libres:")
            for slot in slots_formatted:
                print(f"   ⏰ {slot['inicio_hora']} - {slot['fin_hora']}")

    return disponibilidad
