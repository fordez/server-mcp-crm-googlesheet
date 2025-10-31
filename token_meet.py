#!/usr/bin/env python3
"""
Script para obtener token de Google Calendar/Meet manualmente.
Guarda el token en la misma estructura que usa tu servidor.
"""

import os
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Mismo scopes que tu CalendarService
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/meetings.space.created",
]


def get_token(environment="production"):
    """
    Obtiene el token de Google usando OAuth2 flow.

    Args:
        environment: "development" o "production"
    """
    # Determinar rutas según entorno
    if environment.lower() == "development":
        token_path = "secrets/token-dev.json"
        credentials_path = "secrets/credentials-dev.json"
    else:
        token_path = "secrets/token-prod.json"
        credentials_path = "secrets/credentials-prod.json"

    print(f"\n🔐 Obteniendo token para: {environment.upper()}")
    print(f"📁 Token se guardará en: {token_path}")
    print(f"📄 Usando credenciales de: {credentials_path}\n")

    # Verificar que existe el archivo de credenciales
    if not os.path.exists(credentials_path):
        print(
            f"❌ ERROR: No se encontró el archivo de credenciales: {credentials_path}"
        )
        print("\n💡 Debes descargar las credenciales OAuth2 de Google Cloud Console:")
        print("   1. Ve a https://console.cloud.google.com/apis/credentials")
        print("   2. Crea credenciales OAuth 2.0 (tipo 'Desktop app')")
        print(f"   3. Descarga el JSON y guárdalo como: {credentials_path}\n")
        return

    creds = None

    # Verificar si ya existe un token válido
    if os.path.exists(token_path):
        print("⚠️  Ya existe un token en esa ruta.")
        respuesta = input("¿Deseas renovarlo? (s/n): ").strip().lower()
        if respuesta != "s":
            print("❌ Operación cancelada.")
            return

        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"⚠️  Token existente inválido: {e}")

    # Si no hay credenciales válidas, iniciar flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refrescando token expirado...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️  No se pudo refrescar: {e}")
                creds = None

        if not creds:
            print("🌐 Iniciando flujo OAuth2...")
            print("🔓 Se abrirá tu navegador para autorizar el acceso...\n")

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Usa el servidor local en puerto 8080
            creds = flow.run_local_server(port=8080)

    # Crear directorio secrets si no existe
    os.makedirs("secrets", exist_ok=True)

    # Guardar el token
    with open(token_path, "w") as token:
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        json.dump(token_data, token, indent=2)

    print(f"\n✅ Token guardado exitosamente en: {token_path}")
    print("🎉 Ahora tu servidor puede usar este token automáticamente.\n")


def main():
    """Menú principal para elegir entorno."""
    print("=" * 60)
    print("🔑 GENERADOR DE TOKEN GOOGLE CALENDAR/MEET")
    print("=" * 60)
    print("\nSelecciona el entorno:")
    print("  1. Development (token-dev.json)")
    print("  2. Production (token-prod.json)")
    print("  3. Salir")

    opcion = input("\nOpción [1/2/3]: ").strip()

    if opcion == "1":
        get_token("development")
    elif opcion == "2":
        get_token("production")
    elif opcion == "3":
        print("👋 Saliendo...")
    else:
        print("❌ Opción inválida")


if __name__ == "__main__":
    main()
