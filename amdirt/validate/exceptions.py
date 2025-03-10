class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class DatasetValidationError(Error):
    """Exception raised for errors in validating the dataset againsy the standards.

    Attributes:
        message -- explanation of the error
    """

    name = "Dataset Validation Error"

    def __init__(self, message):
        self.message = message


class DuplicateError(Error):
    """Exception raised for errors due to duplicated rows"

    Attributes:
        message -- explanation of the error
    """

    name = "Duplicated Row Error"

    def __init__(self, message):
        self.message = message


class DOIDuplicateError(Error):
    """Exception raised for errors due to duplicates in standards

    Attributes:
        message -- explanation of the error
    """

    name = "Duplicated DOI Error"

    def __init__(self, message):
        self.message = message


class ColumnDifferenceError(Error):
    """Exception raised for errors due to missing/added columns

    Attributes:
        message -- explanation of the error
    """

    name = "Different Columns Error"

    def __init__(self, message):
        self.message = message


class ParsingError(Error):
    """Exception raised for parsing errors

    Attributes:
        message -- explanation of the error
    """

    name = "Parsing Error"

    def __init__(self, message):
        self.message = message

class NetworkError(Error):
    """Exception raised for parsing errors

    Attributes:
        message -- explanation of the error
    """

    name = "Network Error"

    def __init__(self, message):
        self.message = message


class DuplicateEntryError(Error):
    """Exception raised for errors due to duplicated entries in columns"

    Attributes:
        message -- explanation of the error
    """

    name = "Duplicated Entries in column Error"

    def __init__(self, message):
        self.message = message
