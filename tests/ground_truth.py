"""Ground-truth barcode values for each test_docs file.

Shared between conftest.py (fixtures) and test_integration.py (parametrized tests).
Format: {"value": str, "type": str (BarcodeType.value), "symbology": str}
"""

GROUND_TRUTH: dict = {
    "(proof)(BL6)(540841).pdf": {
        "barcodes": [
            {"value": "0850031591271", "type": "EAN_13", "symbology": "EAN13"},
        ],
    },
    "(proof)(BL6)(540837).pdf": {
        "barcodes": [
            {"value": "0850031591264", "type": "EAN_13", "symbology": "EAN13"},
        ],
    },
    "EXCEL PRINTPACK-0480-01 proof.pdf": {
        "barcodes": [
            {"value": "X0032C5SUL", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "EXCEL PRINTPACK-0480-04 proof.pdf": {
        "barcodes": [
            {"value": "X002K7DQFD", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai": {
        "barcodes": [
            {"value": "X004781QUF", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg": {
        "barcodes": [
            {"value": "X004781QUF", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
}
