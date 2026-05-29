import os
from pathlib import Path
from typing import List, Dict, Any
import csv


# Asumiendo que importas tu parser desde el módulo correspondiente
# from fel_processor.core.parser import GTFelParser

class DirectoryScanner:
    """Se encarga únicamente de encontrar archivos XML."""

    @staticmethod
    def get_xml_files(directory_path: str) -> List[Path]:
        path = Path(directory_path)
        return list(path.rglob("*.xml"))


class BusinessValidator:
    """Centraliza las reglas de negocio."""

    @staticmethod
    def is_valid_for_export(invoice_data: Dict[str, Any]) -> bool:
        # Extraer el tipo de documento (FACT, NCRE, NDEB)
        tipo = invoice_data.get("documento", {}).get("tipo_documento", "")

        # Regla: Solo procesar Facturas y Notas de Crédito
        if tipo not in ["FACT", "NCRE", "FPEQ"]:
            return False

        # Aquí puedes agregar más validaciones (ej. montos en 0)
        return True


class CSVExporter:
    """Se encarga únicamente de escribir el archivo final."""

    def __init__(self, output_path: str):
        self.output_path = output_path

    def export(self, data_list: List[Dict[str, Any]]):
        if not data_list:
            return

        # Lógica de aplanado de datos y escritura en CSV
        # (Dependerá de qué columnas exactas necesitas en tu CSV de ventas/compras)
        keys = ["uuid", "fecha_emision", "tipo", "nit_proveedor", "gran_total"]

        with open(self.output_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(keys)
            for item in data_list:
                doc = item.get("documento", {})
                prov = item.get("proveedor", {})
                tot = item.get("totales", {})
                writer.writerow([
                    doc.get("uuid"),
                    doc.get("fecha_emision"),
                    doc.get("tipo_documento"),
                    prov.get("nit"),
                    tot.get("gran_total")
                ])


class InvoiceOrchestrator:
    """
    Coordina el flujo completo.
    Recibe un directorio, usa el scanner, parsea, valida y exporta.
    """

    def __init__(self, exporter: CSVExporter, validator: BusinessValidator):
        self.exporter = exporter
        self.validator = validator

    def process_directory(self, directory_path: str):
        xml_files = DirectoryScanner.get_xml_files(directory_path)
        valid_invoices = []

        for xml_file in xml_files:
            try:
                # 1. Parsear (Responsabilidad del Parser)
                parser = GTFelParser(xml_file)
                invoice_data = parser.procesar_factura()

                # 2. Validar (Responsabilidad del Validator)
                if self.validator.is_valid_for_export(invoice_data):
                    valid_invoices.append(invoice_data)

            except Exception as e:
                print(f"Error procesando {xml_file.name}: {e}")

        # 3. Exportar (Responsabilidad del Exporter)
        self.exporter.export(valid_invoices)
        return len(valid_invoices)


# --- EJEMPLO DE USO ---
if __name__ == "__main__":
    exporter = CSVExporter("reporte_compras.csv")
    validator = BusinessValidator()

    # Inyección de dependencias al orquestador
    processor = InvoiceOrchestrator(exporter, validator)
    procesadas = processor.process_directory("/ruta/a/tu/carpeta/xmls")
    print(f"Se procesaron y exportaron {procesadas} documentos válidos.")