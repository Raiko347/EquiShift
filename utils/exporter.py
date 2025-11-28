# -*- coding: utf-8 -*-
"""
utils/exporter.py

Enthält die Logik zum Exportieren von Daten als XLSX und PDF.
"""
import pandas as pd
from collections import defaultdict
from datetime import datetime
import os
import re
import io

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# GUI Imports für Fehlermeldungen
from PyQt5.QtWidgets import QMessageBox

# PyPDF Imports (für Anhänge)
try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    PdfWriter = None

class Exporter:
    """Eine Klasse, die nur statische Methoden für den Export bereitstellt."""

    @staticmethod
    def create_member_template(file_path):
        columns = ["first_name", "last_name", "display_name", "birth_date", "street", "postal_code", "city", "email", "phone1", "phone2", "status", "entry_date", "notes"]
        df = pd.DataFrame(columns=columns)
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Mitglieder-Vorlage", index=False)
                worksheet = writer.sheets["Mitglieder-Vorlage"]
                worksheet['A2'] = "Max"; worksheet['B2'] = "Mustermann"; worksheet['C2'] = "Max M."; worksheet['D2'] = "TT.MM.JJJJ"; worksheet['K2'] = "Aktiv"; worksheet['L2'] = "TT.MM.JJJJ"
                for i, col in enumerate(columns): worksheet.column_dimensions[chr(65 + i)].width = len(col) + 5
            return True
        except Exception as e:
            print(f"Fehler: {e}")
            return False

    @staticmethod
    def export_members_to_xlsx(data, duty_type_names, file_path):
        if not data: return False
        df = pd.DataFrame(data)
        static_cols_map = {"first_name": "Vorname", "last_name": "Nachname", "display_name": "Anzeigename", "birth_date": "Geburtsdatum", "street": "Straße", "postal_code": "PLZ", "city": "Ort", "email": "E-Mail", "phone1": "Telefon 1", "phone2": "Telefon 2", "status": "Status", "entry_date": "Eintrittsdatum", "exit_date": "Austrittsdatum", "notes": "Notizen"}
        sorted_duty_cols = sorted(duty_type_names)
        final_cols_order = list(static_cols_map.keys()) + sorted_duty_cols
        df = df[final_cols_order]
        df.columns = list(static_cols_map.values()) + sorted_duty_cols
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Mitgliederliste", index=False)
                worksheet = writer.sheets["Mitgliederliste"]
                for i, col_name in enumerate(df.columns):
                    max_len = max(df[col_name].astype(str).map(len).max(), len(col_name))
                    worksheet.column_dimensions[chr(65 + i)].width = max_len + 2
            return True
        except Exception as e:
            print(f"Fehler: {e}")
            return False

    @staticmethod
    def export_hours_summary_to_xlsx(data, file_path, time_period):
        if not data: return False
        df = pd.DataFrame(data)
        df.columns = ["Name", "Geleistete Stunden", "Anzahl Dienste"]
        df['Geleistete Stunden'] = df['Geleistete Stunden'].round(2)
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                sheet_name = f"Stundenübersicht {time_period}"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value)) for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
            return True
        except Exception as e:
            print(f"Fehler: {e}")
            return False

    @staticmethod
    def export_to_xlsx(data, event_name, file_path):
        if not data: return False
        data_list = [dict(row) for row in data]
        df = pd.DataFrame(data_list)
        df['shift_date_formatted'] = pd.to_datetime(df['shift_date']).dt.strftime('%d.%m.%Y')
        df['schicht'] = df['shift_date_formatted'] + ' ' + df['start_time'] + ' - ' + df['end_time']
        df = df[['aufgabe', 'schicht', 'helfer', 'telefon']]
        df.columns = ["Aufgabe", "Schicht", "Helfer", "Telefon"]
        df['Helfer'] = df['Helfer'].fillna('--- Unbesetzt ---')
        df['Telefon'] = df['Telefon'].fillna('')
        try:
            safe_sheet_name = re.sub(r'[\\/*?:\[\]]', '', event_name)[:31]
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
                worksheet = writer.sheets[safe_sheet_name]
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value)) for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
            return True
        except Exception as e:
            print(f"Fehler: {e}")
            return False

    @staticmethod
    def export_to_pdf_matrix(data, event_name, file_path, settings, tasks_to_show=None, attachments=None):
        """
        Exportiert den Dienstplan als PDF und fügt optionale Anhänge (PDFs) hinzu.
        """
        if not data: return False

        # 1. Daten aufbereiten
        if tasks_to_show: tasks = tasks_to_show
        else: tasks = sorted(list(set(row['aufgabe'] for row in data)))
        shifts = sorted(list(set((row['shift_date'], row['start_time'], row['end_time']) for row in data)))
        
        assignments = defaultdict(list)
        for row in data:
            if row['helfer']:
                key = (row['aufgabe'], row['shift_date'], row['start_time'], row['end_time'])
                assignments[key].append(row['helfer'])

        # 2. Tabelle bauen
        dates = defaultdict(list)
        time_header = ["Aufgabe"]
        for i, (date, start, end) in enumerate(shifts):
            formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
            dates[formatted_date].append(i + 1)
            time_header.append(f"{start} - {end}")
        
        date_header = [""] * len(time_header)
        for date_str, cols in dates.items(): date_header[cols[0]] = date_str
        table_data = [date_header, time_header]

        for task_name in tasks:
            row_data = [task_name]
            for shift_date, start_time, end_time in shifts:
                key = (task_name, shift_date, start_time, end_time)
                helpers = assignments.get(key, [])
                p_style = ParagraphStyle(name='Cell', parent=getSampleStyleSheet()['Normal'], alignment=TA_CENTER)
                cell_content = Paragraph("<br/>".join(sorted(helpers)), p_style)
                row_data.append(cell_content)
            table_data.append(row_data)

        # 3. PDF erstellen (in Buffer)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5*inch, bottomMargin=1.5*inch)
        story = []
        
        table = Table(table_data, repeatRows=2)
        style_commands = [
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 2), (0, -1), 'LEFT'),
            ('LEFTPADDING', (0, 2), (0, -1), 6),
        ]
        for r, task_name in enumerate(tasks, start=2):
            for c, shift_key in enumerate(shifts, start=1):
                key = (task_name, shift_key[0], shift_key[1], shift_key[2])
                if not assignments.get(key):
                    style_commands.append(('BACKGROUND', (c, r), (c, r), colors.lightgrey))
        for date_str, cols in dates.items():
            start_col, end_col = cols[0], cols[-1]
            if len(cols) > 1: style_commands.append(('SPAN', (start_col, 0), (end_col, 0)))
            style_commands.append(('ALIGN', (start_col, 0), (end_col, 0), 'CENTER'))
            style_commands.append(('BACKGROUND', (start_col, 0), (end_col, 0), colors.darkgrey))
            style_commands.append(('TEXTCOLOR', (start_col, 0), (end_col, 0), colors.whitesmoke))
            style_commands.append(('FONTNAME', (start_col, 0), (end_col, 0), 'Helvetica-Bold'))
        table.setStyle(TableStyle(style_commands))
        story.append(table)

        club_name = settings.get_pdf_club_name()
        logo_path = settings.get_pdf_logo_path()
        footer_text = settings.get_pdf_footer_text()

        def _header_footer(canvas, doc):
            canvas.saveState()
            styles = getSampleStyleSheet()
            header_rect_height = 0.8 * inch
            header_y = doc.pagesize[1] - doc.topMargin + 0.2*inch
            canvas.setFillColor(colors.lightgrey)
            canvas.rect(doc.leftMargin, header_y, doc.width, header_rect_height, fill=1, stroke=0)
            p = Paragraph(f"Dienstplan {club_name}<br/>Veranstaltung: {event_name}", styles['h1'])
            p.wrapOn(canvas, doc.width - 2*inch, doc.height)
            p.drawOn(canvas, doc.leftMargin + 0.2*inch, header_y + 0.1*inch)
            if not os.path.isabs(logo_path): logo_path_abs = os.path.join(os.path.abspath("."), logo_path)
            else: logo_path_abs = logo_path
            if os.path.exists(logo_path_abs):
                try:
                    img = Image(logo_path_abs, width=0.7*inch, height=0.7*inch)
                    img.drawOn(canvas, doc.leftMargin + doc.width - 1*inch, header_y + 0.05*inch)
                except: pass
            footer_y = doc.bottomMargin - 1.2*inch
            p_left = Paragraph(footer_text, styles['Normal'])
            p_left.wrapOn(canvas, doc.width * 0.7, doc.height)
            p_left.drawOn(canvas, doc.leftMargin, footer_y)
            right_style = ParagraphStyle(name='Right', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=8)
            p_right = Paragraph("EquiShift © 2025<br/>by Raiko347", right_style)
            p_right.wrapOn(canvas, doc.width * 0.25, doc.height)
            p_right.drawOn(canvas, doc.leftMargin + doc.width * 0.75, footer_y)
            canvas.restoreState()

        try:
            doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
        except Exception as e:
            print(f"Fehler beim Erstellen des Basis-PDFs: {e}")
            return False

        # 4. Merging mit Anhängen (pypdf)
        
        # CHECK 1: Ist pypdf installiert?
        if PdfWriter is None:
            QMessageBox.warning(None, "Fehlende Komponente", "Die Bibliothek 'pypdf' ist nicht installiert.\nAnhänge können nicht hinzugefügt werden.\n\nBitte 'pip install pypdf' ausführen.")
            try:
                with open(file_path, "wb") as f:
                    f.write(buffer.getvalue())
                return True
            except Exception as e:
                print(f"Fehler beim Speichern (ohne Anhänge): {e}")
                return False

        try:
            merger = PdfWriter()
            
            # Dienstplan hinzufügen
            buffer.seek(0)
            merger.append(buffer)
            
            # Anhänge hinzufügen
            if attachments:
                for att_path in attachments:
                    if os.path.exists(att_path):
                        try:
                            merger.append(att_path)
                        except Exception as e:
                            QMessageBox.warning(None, "Fehler bei Anhang", f"Konnte Anhang nicht hinzufügen:\n{att_path}\n\nFehler: {e}")
                    else:
                         QMessageBox.warning(None, "Anhang fehlt", f"Die Datei wurde nicht gefunden:\n{att_path}")
            
            merger.write(file_path)
            merger.close()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Export Fehler", f"Kritischer Fehler beim PDF-Export:\n{e}")
            return False

    @staticmethod
    def export_post_event_sheets(data, event_name, file_path, settings):
        if not data: return False
        doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), topMargin=1.5*inch, bottomMargin=1.5*inch)
        story = []
        styles = getSampleStyleSheet()
        tasks = defaultdict(list)
        for row in data: tasks[row['task_name']].append(row)
        first_task = True
        for task_name, rows in sorted(tasks.items()):
            if not first_task: story.append(PageBreak())
            first_task = False
            title = Paragraph(f"Nachbereitung für: {task_name}", styles['h2'])
            story.append(title)
            story.append(Spacer(1, 0.2 * inch))
            table_data = [["Schicht", "Geplanter Helfer", "Erledigt\n[ ]", "Vertreter\n[ ]", "Entschuldigt\n[ ]", "Gschwänzt\n[ ]", "Name des Vertreters"]]
            style_commands = [('GRID', (0, 0), (-1, -1), 1, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('ALIGN', (1, 1), (1, -1), 'LEFT'), ('FONTSIZE', (0, 0), (-1, -1), 8)]
            last_shift_key = None; start_span_row = 1
            sorted_rows = sorted(rows, key=lambda r: (r['shift_date'], r['start_time']))
            for i, row in enumerate(sorted_rows):
                current_shift_key = f"{row['shift_date']}{row['start_time']}"
                shift_text = f"{datetime.strptime(row['shift_date'], '%Y-%m-%d').strftime('%d.%m.%Y')}\n{row['start_time']} - {row['end_time']}"
                if last_shift_key and last_shift_key != current_shift_key:
                    if i - (start_span_row - 1) > 1: style_commands.append(('SPAN', (0, start_span_row), (0, i)))
                    start_span_row = i + 1
                if i == 0: start_span_row = 1
                table_data.append([shift_text, row['helper_name'], "", "", "", "", ""])
                last_shift_key = current_shift_key
            if len(sorted_rows) - (start_span_row - 1) > 1: style_commands.append(('SPAN', (0, start_span_row), (0, len(sorted_rows))))
            table = Table(table_data, colWidths=[1.5*inch, 2*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch, 2.5*inch], repeatRows=1)
            table.setStyle(TableStyle(style_commands))
            story.append(table)

        club_name = settings.get_pdf_club_name()
        logo_path = settings.get_pdf_logo_path()
        footer_text = settings.get_pdf_footer_text()

        def _header_footer(canvas, doc):
            canvas.saveState()
            styles = getSampleStyleSheet()
            header_rect_height = 0.8 * inch
            header_y = doc.pagesize[1] - doc.topMargin + 0.2*inch
            canvas.setFillColor(colors.lightgrey)
            canvas.rect(doc.leftMargin, header_y, doc.width, header_rect_height, fill=1, stroke=0)
            p = Paragraph(f"Dienstplan {club_name}<br/>Veranstaltung: {event_name}", styles['h1'])
            p.wrapOn(canvas, doc.width - 2*inch, doc.height)
            p.drawOn(canvas, doc.leftMargin + 0.2*inch, header_y + 0.1*inch)
            if not os.path.isabs(logo_path): logo_path_abs = os.path.join(os.path.abspath("."), logo_path)
            else: logo_path_abs = logo_path
            if os.path.exists(logo_path_abs):
                try:
                    img = Image(logo_path_abs, width=0.7*inch, height=0.7*inch)
                    img.drawOn(canvas, doc.leftMargin + doc.width - 1*inch, header_y + 0.05*inch)
                except: pass
            footer_y = doc.bottomMargin - 1.2*inch
            p_left = Paragraph(footer_text, styles['Normal'])
            p_left.wrapOn(canvas, doc.width * 0.7, doc.height)
            p_left.drawOn(canvas, doc.leftMargin, footer_y)
            right_style = ParagraphStyle(name='Right', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=8)
            p_right = Paragraph("EquiShift © 2025<br/>by Raiko347", right_style)
            p_right.wrapOn(canvas, doc.width * 0.25, doc.height)
            p_right.drawOn(canvas, doc.leftMargin + doc.width * 0.75, footer_y)
            canvas.restoreState()
        
        try:
            doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
            return True
        except Exception as e:
            print(f"Fehler beim Nachbereitungs-Export: {e}")
            return False