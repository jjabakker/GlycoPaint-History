import pandas as pd

def create_diffusion_coefficient(df_tracks: pd.DataFrame) -> pd.DataFrame:

    df_dc = df_tracks.groupby('RECORDING NAME').agg({
        'DIFFUSION_COEFFICIENT': ['mean', 'median', 'std', 'count']
    })

    # Rename columns and round values
    # First onvert tuple column names to strings
    df_dc.columns = ['_'.join(col) for col in df_dc.columns]

    df_dc = df_dc.round(0)

    df_dc.rename(columns={'DIFFUSION_COEFFICIENT_mean': 'Mean',
                          'DIFFUSION_COEFFICIENT_median': 'Median',
                          'DIFFUSION_COEFFICIENT_std': 'Std',
                          'DIFFUSION_COEFFICIENT_count': 'Count'}, inplace=True)
    df_dc.index_name = 'ext_recording_name'
    return df_dc