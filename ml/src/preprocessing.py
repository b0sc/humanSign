"""Data preprocessing for keystroke datasets."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional


def load_dsn_2009(filepath: Path) -> pd.DataFrame:
    """
    Load DSN-2009 dataset (Killourhy & Maxion CMU benchmark).
    
    Expected columns: subject, session, rep, H.*, DD.*, UD.*
    where:
    - H.key = hold time (dwell time)
    - DD.key1.key2 = down-down time
    - UD.key1.key2 = up-down time (flight time)
    """
    df = pd.read_csv(filepath)
    
    # Melt timing features into long format
    records = []
    
    for _, row in df.iterrows():
        subject = row['subject']
        session = row.get('sessionIndex', 1)
        rep = row.get('rep', 1)
        
        # Extract hold times (H.*)
        h_cols = [c for c in df.columns if c.startswith('H.')]
        dd_cols = [c for c in df.columns if c.startswith('DD.')]
        ud_cols = [c for c in df.columns if c.startswith('UD.')]
        
        record = {
            'subject': subject,
            'session': session,
            'rep': rep,
            'is_human': True,  # All real human data
        }
        
        # Add dwell times
        for col in h_cols:
            key = col[2:]  # Remove "H." prefix
            record[f'dwell_{key}'] = row[col]
        
        # Add down-down times
        for col in dd_cols:
            keys = col[3:]  # Remove "DD." prefix
            record[f'dd_{keys}'] = row[col]
        
        # Add up-down times (flight)
        for col in ud_cols:
            keys = col[3:]  # Remove "UD." prefix
            record[f'flight_{keys}'] = row[col]
        
        records.append(record)
    
    return pd.DataFrame(records)


def load_aalto_desktop(filepath: Path) -> pd.DataFrame:
    """
    Load Aalto Desktop dataset.
    
    Large-scale browser-based typing data.
    """
    # Aalto dataset typically has keypress, keyrelease timestamps
    df = pd.read_csv(filepath)
    
    # Group by participant and sentence
    grouped = df.groupby(['PARTICIPANT_ID', 'TEST_SECTION_ID'])
    
    records = []
    for (participant, section), group in grouped:
        group = group.sort_values('PRESS_TIME')
        
        # Calculate dwell and flight times
        dwell_times = (group['RELEASE_TIME'] - group['PRESS_TIME']).values
        
        press_times = group['PRESS_TIME'].values
        release_times = group['RELEASE_TIME'].values
        flight_times = press_times[1:] - release_times[:-1]
        
        # Filter outliers
        dwell_times = dwell_times[(dwell_times > 0) & (dwell_times < 2000)]
        flight_times = flight_times[(flight_times > -500) & (flight_times < 5000)]
        
        if len(dwell_times) < 10:
            continue
        
        record = {
            'subject': participant,
            'session': section,
            'is_human': True,
            'total_keystrokes': len(group),
            'avg_dwell_time': np.mean(dwell_times),
            'std_dwell_time': np.std(dwell_times),
            'avg_flight_time': np.mean(flight_times) if len(flight_times) > 0 else 0,
            'std_flight_time': np.std(flight_times) if len(flight_times) > 0 else 0,
        }
        records.append(record)
    
    return pd.DataFrame(records)


def clean_timing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean timing data by removing outliers and invalid values.
    """
    # Remove negative values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if 'dwell' in col.lower() or 'flight' in col.lower() or 'dd' in col.lower():
            df[col] = df[col].clip(lower=0)
    
    # Cap extreme values
    for col in numeric_cols:
        if 'dwell' in col.lower():
            df[col] = df[col].clip(upper=2000)  # Max 2 seconds
        elif 'flight' in col.lower() or 'dd' in col.lower():
            df[col] = df[col].clip(upper=5000)  # Max 5 seconds
    
    # Remove rows with too many NaNs
    df = df.dropna(thresh=len(df.columns) * 0.5)
    
    return df


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/validation/test sets.
    
    Ensures subjects don't appear in multiple sets.
    """
    subjects = df['subject'].unique()
    np.random.seed(random_state)
    np.random.shuffle(subjects)
    
    n_subjects = len(subjects)
    n_test = int(n_subjects * test_size)
    n_val = int(n_subjects * val_size)
    
    test_subjects = subjects[:n_test]
    val_subjects = subjects[n_test:n_test + n_val]
    train_subjects = subjects[n_test + n_val:]
    
    train_df = df[df['subject'].isin(train_subjects)].copy()
    val_df = df[df['subject'].isin(val_subjects)].copy()
    test_df = df[df['subject'].isin(test_subjects)].copy()
    
    return train_df, val_df, test_df


def create_synthetic_bot_data(
    human_df: pd.DataFrame,
    n_samples: int,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Create synthetic bot data by perturbing human timing patterns.
    
    Bots typically have:
    - More uniform timing distributions
    - Less variance in dwell/flight times
    - Missing natural pause patterns
    """
    np.random.seed(random_state)
    
    timing_cols = [c for c in human_df.columns 
                   if 'dwell' in c.lower() or 'flight' in c.lower() or 'dd' in c.lower()]
    
    records = []
    for i in range(n_samples):
        # Sample a random human record as base
        base = human_df.sample(1).iloc[0]
        
        record = {
            'subject': f'bot_{i}',
            'session': 1,
            'is_human': False,
        }
        
        for col in timing_cols:
            if pd.notna(base[col]):
                # Bots have more uniform timing (reduce variance)
                mean_val = base[col]
                # Add small uniform noise instead of natural variation
                noise = np.random.uniform(-10, 10)
                record[col] = max(0, mean_val * 0.9 + noise)
        
        records.append(record)
    
    return pd.DataFrame(records)


if __name__ == '__main__':
    # Example usage
    print("Preprocessing module loaded successfully")
