import pandas as pd


def csv_file_identical(file1, file2):
    try:
        # Load the CSV files into DataFrames
        df1 = pd.read_csv(file1, low_memory=False)
        df2 = pd.read_csv(file2, low_memory=False)

        if df1.shape != df2.shape:
            result = False

        if df1.equals(df2):
            result =  True
        else:
            result = False

        print('Comparing: ')
        print(f"  {file1}")
        print(f"  {file2}")
        print(f"Files are {'Identical' if result else 'Different'}\n")
        return result

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


if __name__ == '__main__':

    file1a = '/Users/hans/Paint Data/Regular Probes/Single/Paint Regular Probes - Single - 30 Squares - 5 DR/Output/All Images.csv'
    file1b = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data New/Paint Regular Probes - Single - 30 Squares - 5 DR/Output/All Images.csv'
    file2 = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data New/Paint Regular Probes - Single - 30 Squares - 5 DR/Output/squares_master.csv'

    csv_file_identical(file1a, file1a)
    csv_file_identical(file1a, file1b)
    csv_file_identical(file1a, file2)

