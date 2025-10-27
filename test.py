from datetime import datetime, timedelta
from services.google_calendar_meet.services import (
    get_credentials,
    create_meet_event,
    check_availability,
    get_event_details,
)
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def ejemplo_autenticacion():
    """
    🔐 Ejemplo 1: Solo autenticar (una vez)
    """
    creds = get_credentials()
    logging.info("✅ Autenticación completada correctamente.")
    print(f"Token válido hasta: {creds.expiry}")


def ejemplo_crear_evento():
    """
    🗓️ Ejemplo 2: Crear evento con enlace de Google Meet
    """
    start = datetime.now() + timedelta(minutes=10)
    end = start + timedelta(minutes=30)

    evento = create_meet_event(
        summary="Demo de Google Meet con Python",
        start_time=start,
        end_time=end,
        attendees=["ejemplo@gmail.com"],  # cambia por un correo válido
        description="Reunión creada automáticamente desde main.py",
    )

    print("\n=== EVENTO CREADO ===")
    print(f"🆔 ID: {evento['event_id']}")
    print(f"🔗 Enlace Meet: {evento['meet_link']}")
    print(f"📅 Enlace Calendar: {evento['calendar_link']}")


def ejemplo_ver_disponibilidad():
    """
    🕓 Ejemplo 3: Verificar disponibilidad del calendario
    """
    start = datetime.now() + timedelta(hours=1)
    end = start + timedelta(minutes=30)

    libre = check_availability()
    if libre:
        print("🟢 Estás disponible en ese rango.")
    else:
        print("🔴 Ya tienes eventos agendados en ese rango.")


def ejemplo_obtener_detalles():
    """
    📄 Ejemplo 4: Consultar detalles completos del evento
    """
    event_id = input("👉 Ingresa el ID del evento que deseas consultar: ").strip()
    detalles = get_event_details(event_id)

    print("\n=== DETALLES DEL EVENTO ===")
    for key, value in detalles.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    print("""
    === MENÚ DE EJEMPLOS ===
    1️⃣ Autenticación OAuth
    2️⃣ Crear evento con Meet
    3️⃣ Ver disponibilidad
    4️⃣ Obtener detalles del evento
    """)
    opcion = input("Selecciona una opción (1-4): ")

    if opcion == "1":
        ejemplo_autenticacion()
    elif opcion == "2":
        ejemplo_crear_evento()
    elif opcion == "3":
        ejemplo_ver_disponibilidad()
    elif opcion == "4":
        ejemplo_obtener_detalles()
    else:
        print("❌ Opción no válida.")
