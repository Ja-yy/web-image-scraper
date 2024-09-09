
import os

def ensure_directory_exists(directory: str) -> None:
    '''
    Ensures that a directory exists, creates it if it doesn't.
    
    Parameters:
    -----------
    directory : str
        The path of the directory.
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)
