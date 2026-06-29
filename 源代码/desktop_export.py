from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


def export_to_excel(title: str, headers: list[str], rows: list[list], path: str) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def workbook_bytes(title: str, headers: list[str], rows: list[list]) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream
