from __future__ import annotations
import os
import tempfile
import zipfile
from copy import copy
from typing import Any, Dict
from .base import Block, Param
from .registry import register


def _save_as_macro_enabled(workbook: Any, output: str, output_dir: str) -> None:
    """Save a workbook as a valid XLSM package when no VBA archive exists."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', dir=output_dir, delete=False) as temporary:
        temporary_path = temporary.name
    try:
        workbook.save(temporary_path)
        with zipfile.ZipFile(temporary_path, 'r') as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as destination:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == '[Content_Types].xml':
                    data = data.replace(
                        b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml',
                        b'application/vnd.ms-excel.sheet.macroEnabled.main+xml')
                destination.writestr(item.filename, data)
    finally:
        os.unlink(temporary_path)


@register
class OpenExcelBlock(Block):
    CATEGORY = 'Excel'
    NAME = 'Open Excel File'
    DESCRIPTION = 'Reads an Excel file into a DataFrame for processing'
    ICON = '📊'
    COLOR = '#1d9e5e'
    PARAMS = [
        Param('filepath', 'Excel File Path', 'file', required=True,
              placeholder='C:\\path\\to\\file.xlsm'),
        Param('sheet_name', 'Sheet Name', 'text', default='',
              placeholder='Sheet1 (leave empty for first sheet)'),
        Param('output_variable', 'Store data in variable', 'text', default='excel_data'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pandas as pd
        import openpyxl
        filepath = self.params['filepath']
        sheet = self.params.get('sheet_name') or 0
        var = self.params.get('output_variable') or 'excel_data'
        df = pd.read_excel(filepath, sheet_name=sheet)
        context[var] = df
        context['_excel_filepath'] = filepath
        workbook = openpyxl.load_workbook(filepath, read_only=True, keep_vba=True)
        context['_excel_sheet'] = workbook.sheetnames[sheet] if isinstance(sheet, int) else sheet
        workbook.close()
        self.output = f"Loaded {len(df)} rows × {len(df.columns)} columns"

    def get_summary(self) -> str:
        fp = self.params.get('filepath', '')
        sh = self.params.get('sheet_name', '') or 'first sheet'
        import os
        return f"{os.path.basename(fp)}  [{sh}]" if fp else "Not configured"


@register
class SelectSheetBlock(Block):
    CATEGORY = 'Excel'
    NAME = 'Select / Reload Sheet'
    DESCRIPTION = 'Re-reads a specific sheet from the already-opened Excel file'
    ICON = '📑'
    COLOR = '#1d9e5e'
    PARAMS = [
        Param('sheet_name', 'Sheet Name', 'text', required=True, placeholder='CPK'),
        Param('data_variable', 'Data variable (source)', 'text', default='excel_data'),
        Param('output_variable', 'Store result in variable', 'text', default='excel_data'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pandas as pd
        filepath = context.get('_excel_filepath')
        if not filepath:
            raise RuntimeError("No Excel file in context. Add an 'Open Excel File' block first.")
        sheet = self.params['sheet_name']
        var = self.params.get('output_variable') or 'excel_data'
        df = pd.read_excel(filepath, sheet_name=sheet)
        context[var] = df
        context['_excel_sheet'] = sheet
        self.output = f"Sheet '{sheet}': {len(df)} rows"


@register
class FilterColumnBlock(Block):
    CATEGORY = 'Excel'
    NAME = 'Filter Column'
    DESCRIPTION = 'Filters rows by string match, value list, or numeric condition; optionally sorts the result'
    ICON = '🔍'
    COLOR = '#1d9e5e'
    PARAMS = [
        Param('data_variable', 'Data variable', 'text', default='excel_data'),
        Param('sheet_name', 'Sheet name (optional — reloads sheet from file)', 'text', default='',
              placeholder='Leave empty to use current data variable'),
        Param('column', 'Column Name', 'text', required=True, placeholder='TECHNOLOGIE'),
        Param('filter_mode', 'Filter Mode', 'choice', default='match_list',
              options=['match_list', 'not_in_list', 'contains', 'starts_with', 'ends_with',
                       '==', '!=', '>', '>=', '<', '<=']),
        Param('values', 'Filter value(s) — one per line\n(numeric modes use first line only)', 'multiline',
              required=True, placeholder='C11HNL_12\nC11HNL_24'),
        Param('case_sensitive', 'Case sensitive (string modes)', 'bool', default=False),
        Param('sort_column', 'Sort by column after filtering (leave empty to skip)', 'text', default='',
              placeholder='e.g. TECHNOLOGIE or leave empty'),
        Param('sort_ascending', 'Sort ascending', 'bool', default=True),
        Param('output_variable', 'Store result in variable', 'text', default='excel_data'),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pandas as pd
        var = self.params.get('data_variable') or 'excel_data'

        # Optional: reload a specific sheet from the open file
        sheet_name = (self.params.get('sheet_name') or '').strip()
        if sheet_name:
            filepath = context.get('_excel_filepath')
            if not filepath:
                raise RuntimeError("No Excel file in context. Add an 'Open Excel File' block first.")
            df = pd.read_excel(filepath, sheet_name=sheet_name)
        else:
            df = context.get(var)
            if df is None:
                raise ValueError(f"No DataFrame in variable '{var}'. Add an Open Excel block first.")

        column = self.params['column']
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

        values_text = self.params.get('values') or ''
        values = [v.strip() for v in values_text.splitlines() if v.strip()]
        if not values:
            raise ValueError("At least one filter value is required.")

        mode = self.params.get('filter_mode') or 'match_list'
        case = bool(self.params.get('case_sensitive'))

        if mode == 'match_list':
            if case:
                mask = df[column].astype(str).isin(values)
            else:
                lower_vals = {v.lower() for v in values}
                mask = df[column].astype(str).str.lower().isin(lower_vals)
        elif mode == 'not_in_list':
            if case:
                mask = ~df[column].astype(str).isin(values)
            else:
                lower_vals = {v.lower() for v in values}
                mask = ~df[column].astype(str).str.lower().isin(lower_vals)
        elif mode == 'contains':
            pattern = '|'.join(values)
            mask = df[column].astype(str).str.contains(pattern, case=case, na=False, regex=True)
        elif mode == 'starts_with':
            pattern = '|'.join(f'^{v}' for v in values)
            mask = df[column].astype(str).str.contains(pattern, case=case, na=False, regex=True)
        elif mode == 'ends_with':
            pattern = '|'.join(f'{v}$' for v in values)
            mask = df[column].astype(str).str.contains(pattern, case=case, na=False, regex=True)
        elif mode in ('==', '!=', '>', '>=', '<', '<='):
            first = values[0]
            try:
                threshold: Any = float(first)
                col_series = df[column]
            except ValueError:
                # String comparison
                threshold = first if case else first.lower()
                col_series = df[column].astype(str) if case else df[column].astype(str).str.lower()
            ops = {
                '==': col_series == threshold,
                '!=': col_series != threshold,
                '>':  col_series > threshold,
                '>=': col_series >= threshold,
                '<':  col_series < threshold,
                '<=': col_series <= threshold,
            }
            mask = ops[mode]
        else:
            raise ValueError(f"Unknown filter mode: '{mode}'")

        filtered = df[mask]

        # Optional sort
        sort_col = (self.params.get('sort_column') or '').strip()
        if sort_col:
            if sort_col not in filtered.columns:
                raise ValueError(f"Sort column '{sort_col}' not found. Available: {list(filtered.columns)}")
            filtered = filtered.sort_values(sort_col, ascending=bool(self.params.get('sort_ascending', True)))

        out = self.params.get('output_variable') or 'excel_data'
        context[out] = filtered
        if sheet_name:
            context['_excel_sheet'] = sheet_name
        sheet_info = f", sheet '{sheet_name}'" if sheet_name else ''
        self.output = f"Filtered to {len(filtered)} rows  (col '{column}' {mode}{sheet_info})"


@register
class WriteCellBlock(Block):
    CATEGORY = 'Excel'
    NAME = 'Write to Cell'
    DESCRIPTION = 'Writes a value to a specific cell in an Excel file'
    ICON = '✏️'
    COLOR = '#1d9e5e'
    PARAMS = [
        Param('filepath', 'Excel File Path', 'file', required=True),
        Param('sheet_name', 'Sheet Name', 'text', default='Sheet1'),
        Param('cell', 'Cell (e.g. A1)', 'text', required=True, placeholder='A1'),
        Param('value', 'Value', 'text', required=True),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import openpyxl
        filepath = self.params['filepath']
        sheet_name = self.params.get('sheet_name') or 'Sheet1'
        cell = self.params['cell']
        value = self.params['value']
        wb = openpyxl.load_workbook(filepath, keep_vba=True)
        ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
        ws[cell] = value
        wb.save(filepath)
        self.output = f"Wrote '{value}' → {sheet_name}!{cell}"


@register
class SaveExcelBlock(Block):
    CATEGORY = 'Excel'
    NAME = 'Save DataFrame to Excel'
    DESCRIPTION = 'Saves a DataFrame variable to a new Excel file'
    ICON = '💾'
    COLOR = '#1d9e5e'
    PARAMS = [
        Param('data_variable', 'Data variable', 'text', default='excel_data'),
        Param('output_path', 'Output File Path', 'file_save', required=True),
        Param('sheet_name', 'Sheet Name', 'text', default='Sheet1'),
        Param('include_index', 'Include row index', 'bool', default=False),
    ]

    def execute(self, context: Dict[str, Any]) -> None:
        import pandas as pd
        import openpyxl
        var = self.params.get('data_variable') or 'excel_data'
        df = context.get(var)
        if df is None:
            raise ValueError(f"No DataFrame in variable '{var}'")
        output = self.params['output_path']
        sheet_name = self.params.get('sheet_name') or 'Sheet1'
        include_index = bool(self.params.get('include_index'))

        source = context.get('_excel_filepath')
        source_sheet = context.get('_excel_sheet')
        if source and os.path.isfile(source):
            # Keep the original package so styles, formulas, charts, and VBA survive.
            keep_vba = str(source).lower().endswith('.xlsm')
            workbook = openpyxl.load_workbook(source, keep_vba=keep_vba)
            target_sheet = sheet_name if sheet_name in workbook.sheetnames else source_sheet
            if not target_sheet or target_sheet not in workbook.sheetnames:
                target_sheet = workbook.sheetnames[0]
            worksheet = workbook[target_sheet]

            header_row = 1
            headers = [worksheet.cell(header_row, column).value for column in range(1, worksheet.max_column + 1)]
            columns = [header for header in headers if header is not None]
            if list(df.columns) != columns[:len(df.columns)]:
                workbook.close()
                raise ValueError(
                    f"Data columns do not match '{target_sheet}'. Expected {columns}, got {list(df.columns)}"
                )

            row_styles = {
                row_number: [copy(worksheet.cell(row_number, column)._style)
                             for column in range(1, len(df.columns) + 1)]
                for row_number in range(header_row + 1, worksheet.max_row + 1)
            }
            original_data_end = max(worksheet.max_row, len(df.index) + header_row)
            for row_number in range(header_row + 1, original_data_end + 1):
                for column_number in range(1, len(df.columns) + (1 if include_index else 0) + 1):
                    worksheet.cell(row_number, column_number).value = None

            for output_row, (_, row) in enumerate(df.iterrows(), start=header_row + 1):
                source_row = int(row.name) + header_row + 1 if isinstance(row.name, int) else None
                if source_row in row_styles:
                    for column_number, style in enumerate(row_styles[source_row], start=1):
                        worksheet.cell(output_row, column_number)._style = copy(style)
                values = ([row.name] if include_index else []) + list(row)
                for column_number, value in enumerate(values, start=1):
                    if pd.isna(value):
                        value = None
                    worksheet.cell(output_row, column_number).value = value

            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            if output.lower().endswith('.xlsm') and not keep_vba:
                _save_as_macro_enabled(workbook, output, os.path.dirname(os.path.abspath(output)))
            else:
                workbook.save(output)
            workbook.close()
        else:
            # No source workbook is available, so create a normal workbook.
            df.to_excel(output, sheet_name=sheet_name, index=include_index)
        self.output = f"Saved {len(df)} rows → {output}"
