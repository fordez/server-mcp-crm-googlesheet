# test_catalog.py
from services.google_sheet.catalog_service import CatalogService

print("🧪 Test get_all_services:")
print(CatalogService.get_all_services())

print("\n🧪 Test get_service_by_name:")
print(CatalogService.get_service_by_name("Página Web"))
