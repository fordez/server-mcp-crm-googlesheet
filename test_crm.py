#!/usr/bin/env python3
"""
Script de prueba completo para verificar:
 - Creación de cliente
 - Verificación de existencia
 - Actualización de correo y notas
"""

from services.google_sheet.crm_service import CRMService
import json
import time

print("=" * 60)
print("🧪 PRUEBA COMPLETA DEL CRM")
print("=" * 60)

# --------------------------------------------------------
# 🔹 1. Datos iniciales del cliente
# --------------------------------------------------------
test_data = {
    "name": "Juan Pérez",
    "channel": "WhatsApp",
    "phone": "3001234567",
    "email": "juan@ejemplo.com",
    "note": "Cliente interesado en servicios",
    "user": "@juanperez",
    "client_type": "Lead",
    "status": "Nuevo",
}

print("\n📋 Datos iniciales:")
print(json.dumps(test_data, indent=2, ensure_ascii=False))

print("\n🔄 Llamando a CRMService.create_client()...")

try:
    # --------------------------------------------------------
    # 🔹 Crear cliente
    # --------------------------------------------------------
    result = CRMService.create_client(
        name=test_data["name"],
        channel=test_data["channel"],
        phone=test_data["phone"],
        email=test_data["email"],
        note=test_data["note"],
        user=test_data["user"],
        client_type=test_data["client_type"],
        status=test_data["status"],
    )

    print("\n✅ RESPUESTA DE CREACIÓN:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("success"):
        client_id = result.get("client_id")
        print(f"\n🎉 ¡Cliente creado exitosamente con ID: {client_id}!")

        # --------------------------------------------------------
        # 🔹 2. Verificar cliente recién creado
        # --------------------------------------------------------
        print("\n🔍 Verificando que el cliente existe...")
        verify_result = CRMService.verify_client(client_id=client_id)

        if verify_result.get("exists"):
            print("✅ Cliente encontrado en la hoja de cálculo:")
            print(json.dumps(verify_result, indent=2, ensure_ascii=False))
        else:
            print("❌ ERROR: Cliente NO encontrado después de crearlo")
            exit(1)

        # --------------------------------------------------------
        # 🔹 3. Actualizar datos del cliente
        # --------------------------------------------------------
        print("\n🛠️ Actualizando correo y notas del cliente...")

        updated_data = {
            "Email": "nuevo_correo@empresa.com",
            "Note": "Actualización: cliente confirmó interés y reunión agendada.",
            "Status": "Interesado",
        }

        update_result = CRMService.update_client_dynamic(
            client_id=client_id, fields=updated_data
        )

        print("\n✅ RESPUESTA DE ACTUALIZACIÓN:")
        print(json.dumps(update_result, indent=2, ensure_ascii=False))

        if update_result.get("success"):
            print("\n🔁 Releyendo datos del cliente para confirmar cambios...")
            time.sleep(1)
            verify_after = CRMService.verify_client(client_id=client_id)
            print(json.dumps(verify_after, indent=2, ensure_ascii=False))
        else:
            print("❌ ERROR: No se pudo actualizar el cliente")

    else:
        print(f"\n❌ ERROR: {result.get('error')}")

except Exception as e:
    print(f"\n💥 EXCEPCIÓN: {str(e)}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
