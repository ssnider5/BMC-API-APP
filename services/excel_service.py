import pandas as pd
from openpyxl import load_workbook
import numpy as np

class ExcelService:
    def __init__(self):
        self.current_data = None
        self.current_headers = None
        self.current_file = None
    
    def read_excel(self, file_path, sheet_name=0):
        """
        Reads an Excel file and returns headers and data.
        """
        self.current_file = file_path
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Clean up data
            df = self._clean_dataframe(df)
            
            # Store for later use
            self.current_data = df
            self.current_headers = df.columns.tolist()
            
            # Convert to format suitable for treeview (list of tuples)
            data_rows = [tuple(row) for row in df.values]
            
            return self.current_headers, data_rows
        
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            raise
    
    def _clean_dataframe(self, df):
        """
        Standardizes the dataframe: handles empty rows, NaNs, and duplicate columns.
        """
        # Drop completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Ensure column names are strings
        df.columns = [f"Column {i}" if pd.isna(col) else str(col) for i, col in enumerate(df.columns)]
        
        # Handle duplicate column names
        counts = {}
        new_columns = []
        for col in df.columns:
            if col in counts:
                counts[col] += 1
                new_columns.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 0
                new_columns.append(col)
        df.columns = new_columns
        
        # Replace NaN with empty strings
        df = df.fillna('')
        
        return df
    
    def get_json_data(self):
        """
        Returns the current data as a list of dictionaries.
        Sanitizes numpy types to standard Python types for JSON compatibility.
        """
        if self.current_data is None:
            return []
        
        # Convert DataFrame to list of dicts
        records = self.current_data.to_dict('records')
        
        # Ensure all values are JSON-serializable
        for record in records:          
            for key, value in record.items():
                if isinstance(value, np.integer):
                    record[key] = int(value)
                elif isinstance(value, np.floating):
                    record[key] = float(value)
                elif isinstance(value, np.ndarray):
                    record[key] = value.tolist()
        
        return records
    
    def extract_names(self, json_list):
        """
        Helper to get a list of 'name' fields from the data (used for verification lists).
        """
        names = []
        for json_obj in json_list:
            name = json_obj.get('name')
            if name:
                names.append(name)
        return names
