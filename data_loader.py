import pandas as pd
import re
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, bhel_path: str, cpse_path: str, multi_sector_path: str = None):
        self.bhel_path = bhel_path
        self.cpse_path = cpse_path
        self.multi_sector_path = multi_sector_path

    def load_data(self) -> pd.DataFrame:
        logger.info("Loading datasets...")
        dfs = []
        
        # Load BHEL
        try:
            df_bhel = pd.read_csv(self.bhel_path)
            df_bhel = df_bhel[['CPSE', 'Material_Code', 'Material_Description']].copy()
            df_bhel['source'] = 'BHEL'
            dfs.append(df_bhel)
        except Exception as e:
            logger.error(f"Error loading BHEL dataset: {e}")

        # Load CPSE Verified
        try:
            df_cpse = pd.read_csv(self.cpse_path)
            df_cpse = df_cpse[['CPSE', 'Material_Code', 'Material_Description']].copy()
            df_cpse['source'] = 'CPSE_Verified'
            dfs.append(df_cpse)
        except Exception as e:
            logger.error(f"Error loading CPSE dataset: {e}")

        # Load Multi-Sector Distinct Dataset if present
        if self.multi_sector_path and os.path.exists(self.multi_sector_path):
            try:
                df_multi = pd.read_csv(self.multi_sector_path)
                df_multi = df_multi[['CPSE', 'Material_Code', 'Material_Description']].copy()
                df_multi['source'] = 'Multi_Sector_Public_Tenders'
                dfs.append(df_multi)
                logger.info(f"Loaded multi-sector dataset from {self.multi_sector_path}")
            except Exception as e:
                logger.error(f"Error loading Multi-Sector dataset: {e}")

        # Combine all
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=['CPSE', 'Material_Code', 'Material_Description', 'source'])
        
        # Standardize columns
        df.columns = ['cpse', 'material_code', 'material_description', 'source']
        
        # Clean descriptions
        df = self._clean_data(df)
        
        # Add internal ID
        df['internal_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        logger.info(f"Loaded {len(df)} valid materials after cleaning.")
        return df

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop missing
        df = df.dropna(subset=['material_description'])
        
        # Filter out ONGC placeholders
        df = df[~df['material_description'].str.contains('Description not exposed', case=False, na=False)]
        
        def clean_desc(desc):
            if not isinstance(desc, str):
                return ""
            # Handle pipe separated
            desc = str(desc).replace('|', ' ')
            # Lowercase
            desc = desc.lower()
            # Strip whitespace
            desc = re.sub(r'\s+', ' ', desc).strip()
            return desc
            
        df['cleaned_description'] = df['material_description'].apply(clean_desc)
        
        # Filter out empty after cleaning
        df = df[df['cleaned_description'].str.strip() != '']
        return df
