"""Pruebas unitarias del desglose de tasas IVA/IEPS."""
from lxml import etree

from app.cfdis.parser import extraer_impuestos_comprobante, parse_cfdi


XML_IVA16 = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<cfdi:Comprobante xmlns:cfdi=\"http://www.sat.gob.mx/cfd/4\"
    xmlns:tfd=\"http://www.sat.gob.mx/TimbreFiscalDigital\"
    Version=\"4.0\" Fecha=\"2025-03-01T12:00:00\" SubTotal=\"1000\" Total=\"1160\"
    Moneda=\"MXN\" TipoDeComprobante=\"I\" MetodoPago=\"PUE\" FormaPago=\"03\"
    LugarExpedicion=\"01000\">
  <cfdi:Emisor Rfc=\"AAA010101AAA\" Nombre=\"EMISOR\" RegimenFiscal=\"601\"/>
  <cfdi:Receptor Rfc=\"SAVJ950325IP6\" Nombre=\"JUAN\" UsoCFDI=\"G03\" DomicilioFiscalReceptor=\"01000\" RegimenFiscalReceptor=\"612\"/>
  <cfdi:Conceptos>
    <cfdi:Concepto ClaveProdServ=\"01010101\" Cantidad=\"1\" ClaveUnidad=\"E48\"
      Descripcion=\"SERVICIO\" ValorUnitario=\"1000\" Importe=\"1000\" ObjetoImp=\"02\"/>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados=\"160\">
    <cfdi:Traslados>
      <cfdi:Traslado Base=\"1000\" Impuesto=\"002\" TipoFactor=\"Tasa\" TasaOCuota=\"0.160000\" Importe=\"160\"/>
    </cfdi:Traslados>
  </cfdi:Impuestos>
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital UUID=\"11111111-1111-1111-1111-111111111111\"
      FechaTimbrado=\"2025-03-01T12:00:01\" RfcProvCertif=\"SAT970701NN3\"/>
  </cfdi:Complemento>
</cfdi:Comprobante>
"""

XML_MIXTO = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<cfdi:Comprobante xmlns:cfdi=\"http://www.sat.gob.mx/cfd/4\"
    xmlns:tfd=\"http://www.sat.gob.mx/TimbreFiscalDigital\"
    Version=\"4.0\" Fecha=\"2025-03-01T12:00:00\" SubTotal=\"2000\" Total=\"2160\"
    Moneda=\"MXN\" TipoDeComprobante=\"I\">
  <cfdi:Emisor Rfc=\"BBB010101BBB\" Nombre=\"COLEGIO\"/>
  <cfdi:Receptor Rfc=\"SAVJ950325IP6\" Nombre=\"JUAN\" UsoCFDI=\"D10\"/>
  <cfdi:Conceptos>
    <cfdi:Concepto ClaveProdServ=\"86101700\" Cantidad=\"1\" ClaveUnidad=\"E48\"
      Descripcion=\"COLEGIATURA\" ValorUnitario=\"1000\" Importe=\"1000\" ObjetoImp=\"01\"/>
    <cfdi:Concepto ClaveProdServ=\"01010101\" Cantidad=\"1\" ClaveUnidad=\"E48\"
      Descripcion=\"UNIFORME\" ValorUnitario=\"1000\" Importe=\"1000\" ObjetoImp=\"02\"/>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados=\"160\">
    <cfdi:Traslados>
      <cfdi:Traslado Base=\"1000\" Impuesto=\"002\" TipoFactor=\"Exento\"/>
      <cfdi:Traslado Base=\"1000\" Impuesto=\"002\" TipoFactor=\"Tasa\" TasaOCuota=\"0.160000\" Importe=\"160\"/>
    </cfdi:Traslados>
  </cfdi:Impuestos>
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital UUID=\"22222222-2222-2222-2222-222222222222\"
      FechaTimbrado=\"2025-03-01T12:00:01\"/>
  </cfdi:Complemento>
</cfdi:Comprobante>
"""


def test_extraer_iva_16():
    root = etree.fromstring(XML_IVA16.encode())
    ns = {\"cfdi\": \"http://www.sat.gob.mx/cfd/4\"}
    taxes = extraer_impuestos_comprobante(root.find(\"cfdi:Impuestos\", ns))
    assert taxes[\"iva_trasladado\"] == 160
    assert taxes[\"iva_16\"] == 160
    assert taxes[\"base_iva_16\"] == 1000
    assert taxes[\"iva_exento\"] == 0
    assert \"0.16\" in taxes[\"iva_por_tasa\"]


def test_extraer_mixto_exento_y_16():
    root = etree.fromstring(XML_MIXTO.encode())
    ns = {\"cfdi\": \"http://www.sat.gob.mx/cfd/4\"}
    taxes = extraer_impuestos_comprobante(root.find(\"cfdi:Impuestos\", ns))
    assert taxes[\"iva_16\"] == 160
    assert taxes[\"base_iva_exento\"] == 1000


def test_parse_cfdi_roundtrip(tmp_path):
    p = tmp_path / \"a.xml\"
    p.write_text(XML_IVA16, encoding=\"utf-8\")
    data = parse_cfdi(str(p), user_rfc=\"SAVJ950325IP6\")
    assert data is not None
    assert data[\"uuid\"] == \"11111111-1111-1111-1111-111111111111\"
    assert data[\"categoria\"] == \"egreso\"
    assert data[\"iva\"] == 160
    assert data[\"iva_16\"] == 160
    assert data[\"conceptos\"][0][\"objeto_imp\"] == \"02\"
