import pandas as pd


def create_diffusion_coefficient(df_tracks: pd.DataFrame) -> pd.DataFrame:
    """
    Create a DataFrame with the mean, median, standard deviation and count of the diffusion coefficient
    """

    df_dc = df_tracks.groupby('Recording Name').agg({
        'Diffusion Coefficient': ['mean', 'median', 'std', 'count']
    })

    # Rename columns and round values
    # First onvert tuple column names to strings
    df_dc.columns = ['_'.join(col) for col in df_dc.columns]

    df_dc = df_dc.round(0)

    df_dc.rename(columns={'Diffusion Coefficient_mean': 'Mean',
                          'Diffusion Coefficient_median': 'Median',
                          'Diffusion Coefficient_std': 'Std',
                          'Diffusion Coefficient_count': 'Count'}, inplace=True)
    df_dc.index_name = 'ext_recording_name'
    return df_dc
