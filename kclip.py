"""Parses data stored in Kindle clipping files. 

The function get_clippings_from_filename generates Clipping objects
from a Kindle clipping file (e.g. "My Clippings.txt"). 

Supports clipping files created by Kindle Touch (4th generation)
"""

import re
import datetime
import argparse
import fileinput
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

class Clipping(object):
    """Represents the data contained in a single Kindle clipping."""
    def __init__(self, title=None, author=None, clip_type=None, page=None,loc_range=None,datetime=None,clip_text=None):
        self.title = title
        self.author = author
        self.clip_type = clip_type
        self.page = page
        self.loc_range=loc_range
        self.datetime = datetime
        self.clip_text = clip_text

    def __repr__(self):
        format_str = 'Clipping(title=%r,'\
                    'author=%r,'\
                    'clip_type=%r,'\
                    'page=%r,'\
                    'loc_range=%r,'\
                    'datetime=%r,'\
                    'clip_text=%r)'
    
        return (format_str % (self.title,
                              self.author,
                              self.clip_type,
                              self.page,
                              self.loc_range,
                              self.datetime,
                              self.clip_text))

    def __str__(self):
        return self.__repr__()
        
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def get_kindle_strs(self):
        """Returns a Kindle representation of this clipping."""
        # Title/author
        title_line = '%s (%s)' % (self.title, self.author)

        # Metadata line
        highlight_type = '- Your %s' % (self.clip_type.capitalize())
        if (self.loc_range[0] == self.loc_range[1]):
            location_string = 'Location %d' % (self.loc_range[0])
        else:
            location_string = 'Location %d-%d' % (self.loc_range[0], self.loc_range[1])
        page_string = None
        if (self.page is not None):
            page_string = 'on Page %d' % self.page
        date_string = self.datetime.strftime('%A, %B %d, %Y %I:%M:%S %p')

        if (self.page is not None):
            metadata_line = '%s %s | %s | Added on %s' % (highlight_type, page_string, location_string, date_string)
        else:
            metadata_line = '%s %s | Added on %s' % (highlight_type, location_string, date_string)

        return (title_line, metadata_line, '\n', self.clip_text)

class UnparseableClipping(object):
    """Represents a failed attempt to parse a Kindle clipping. 
    Contains information about the failure."""

    def __init__(self, lineno=None, error=None, original_lines=None):
        self.lineno = lineno # line number in the original input where the error occurred
        self.error  = error  # error that occurred when attempting to parse
        if (original_lines is None):  # original lines of input that were being parsed
            self.original_lines=[]
        else:
            self.original_lines=original_lines
    
    def __repr__(self):
        format_str = ( 
            'UnparseableClipping(lineno=%r,'
            'error=%r,'
            'original_lines=%r)'
        )
        return (
            format_str % (
                self.lineno,
                self.error,
                self.original_lines
                )
        )

    def __str__(self):
        return self.__repr__()

# Background on Kindle clipping files:
# Kindle clipping files contain three kinds of records: highlight, note, bookmark
# Each record consists of:  
# 1. A string identifying the book (title and author(s)). 
# 2. A string identifying the kind of record, followed by an optional page number, 
#    then an ebook location or range, and a datetime.
# 3. A blank line
# 4. Some text. In the case of a highlight, it is a clipped piece of text from the book. 
#    In the case of a note, it is user-supplied. 
#    A bookmark contains just a blank line.
# 5. A delimiter signifying the end of the record consisting of ten equal signs. 
#

# The record separator used in Kindle clipping files
RECORD_SEP    = '==========\n'


def get_clippings_from_filename(filename):
    """Parse a Kindle clipping file and generate corresponding Clipping objects.
       Unparseable input results in UnparseableClipping objects.  

    Args:
        filename: The name of a file containing Kindle clippings.
    Yields:
        Clipping and UnparseableClipping objects.
    """
    clip_strings = []
    clipping_start_line = 0
    try:
        with fileinput.input(filename, openhook=fileinput.hook_encoded("utf-8")) as f:
            for line in f:
                if line != RECORD_SEP:
                    clip_strings.append(line)
                if line == RECORD_SEP:
                    clipping = _get_clipping_object_from_clip_strings(clip_strings, clipping_start_line)
                    if clipping is not None: 
                        yield clipping
                    clipping_start_line = fileinput.filelineno()
                    clip_strings = []

            # The final clipping may not have been ended by an explicit RECORD_SEP
            clipping = _get_clipping_object_from_clip_strings(clip_strings, clipping_start_line)
            if clipping is not None:
                yield clipping
    except IOError as ioe:
        logger.info('IOError occurred when processing %s',filename,exc_info=1)
        raise ioe
    return     

def _get_clipping_object_from_clip_strings(clip_strings, lineno):
    """Parse a list of strings comprising a Kindle clipping into a Clipping object, 
    or an UnparseableClipping object.

    Args:
        clip_strings: list of strings comprising the original Kindle clipping.
        lineno: for diagnostics, the line number in the original file.
    
    Returns:
        Clipping object if the clip_strings were parsed successfully, 
        otherwise it return an UnparseableClipping object.
    """
    # This function exists to catch SyntaxError and prevent it from bubbling up.

    if len(clip_strings) > 0:
        try:
            clipping = _get_clipping_object(clip_strings)
            return clipping
        except SyntaxError as se:
            # give up on this particular record 
            logger.info('SyntaxError, line %s',lineno,exc_info=1)
            return UnparseableClipping(lineno, se, clip_strings)

def _get_clipping_object(strlist):
    """Return a Clipping object by parsing a list of strings comprising a single Kindle clipping.

    Args:
        strlist: A list of strings comprising a single Kindle clipping. 
                 0: book identification string containing title and author
                 1: clip metadata string containing clip type, page, location, datetime
                 2: usually a blank line (although if it is non-blank, the content will be preserved)
                 3:: the remainder of the text is the clip_text

    Returns:
        A Clipping object.

    Raises:
        SyntaxError
    """
    if len(strlist) < 4:
        raise SyntaxError('Insufficient strings to constitute a clipping')
    # zeroth line is title and author
    title,author = _get_book(strlist[0])
    # next line is the clip metadata
    clip_type,page,location_range,datetime = _get_clip_meta(strlist[1])
    # clip metadata is followed by a line that seems to be always blank and is not part of clip text. 
    # To be safe, if it does happen to be non-empty, preserve it in the clip_text.
    text_start = 3    
    if strlist[2].strip() != '':
        text_start = 2  # ensure this non-blank line becomes part of the clip_text
    clip_text = ''.join(strlist[text_start::])

    return Clipping(title, author, clip_type, page, location_range, datetime, clip_text)


# This regular expression is used to get the author portion of
# a Kindle book identification string.
# The last parentheses-enclosed string contains the author, for example:
# Leviathan Wakes (The Expanse Book 1) (Corey, James S.A.)
# If no parenthetical expression exists, there is no author, and
# the author will be returned as empty string.
# Known bug: if the author itself contains parentheses, this regex will not
# correctly select the text. The regex can be rewritten to handle a fixed number
# of nested parentheses, or the code can be rewritten to not use a regex. 
AUTHOR_REGEX = r'\(([^()]*)\)$' 
author_regex = re.compile(AUTHOR_REGEX)

def _get_book(s):
    """Return the title and author from the book identification portion of a Kindle clipping.
    
    Args:
        s: A book identification string from a Kindle clipping
    
    Returns:
        title: Book title
        author: Book author. Can be empty.

    Raises:
        SyntaxError: An error occurred when parsing the string.
    """

    s = s.strip()
    if s == '': raise SyntaxError('The book identification string is empty')
    
    author = ''
    author_start = 0
    author_found = False 
    for match in author_regex.finditer(s):
        author_found = True
        author_start = match.start()
        author = match.group(1).strip()
    
    if author_found:
        title = s[:author_start].strip()
    else:
        title = s
    # Sometimes titles have a byte order mark prepended. The Kindle behavior
    # changed in 2011 to stop doing this to entries in My Clippings.txt. 
    # Ensure the title is consistent, strip this character if it exists.
    BOM = '\ufeff'
    if title.startswith(BOM):
        title = title[1:] 
    
    return title,author

# TIMESTAMP_REGEX selects the formatted datetime from the input string.
TIMESTAMP_REGEX = r"""
    (
        \|\ Added\ on.*  # for partitioning the string between cliptype/location and timestamp
    )
    (
        (?:January  |
            February |
            March    | 
            April    | 
            May      |
            June     |
            July     |
            August   |
            September|
            October  |
            November |
            December
        )
        \s*
        \d+,        # day 
        \s*
        \d{4,4}     # year
        ,?          # optional comma, some clippings have this comma
        \s*
        \d+         # hour
        \:
        \d+         # minute
        (?::\d\d)?  # optional seconds
        \s*
        (?:AM|PM)   
        \s*
    )
    $
    """
timestamp_regex = re.compile(TIMESTAMP_REGEX,re.VERBOSE)


CLIP_TYPE_REGEX = r'^\-\s*Your (Highlight|Note|Bookmark)'
clip_type_regex = re.compile(CLIP_TYPE_REGEX)

PAGE_REGEX = r'^\s*on Page (\d+)'
page_regex = re.compile(PAGE_REGEX)

LOC_REGEX = r'Location (\d+)(?:-(\d+))?\s*$'
loc_regex = re.compile(LOC_REGEX)

def _get_clip_meta(s):
    """Return the metadata items associated with a Kindle clipping metadata string.

    Args:
        s: A Kindle clipping metadata string, this kind of string is the second 
        line of a Kindle clipping, after the line containing the title and author.

    Returns:
        clip_type: A string describing the type of clipping, 
                   one of "highlight", "note", "bookmark".
        page: The integer page number associated with this clipping. 
              If no page number was specified, the page will be None.
        loc_range: A tuple of two integers, the start location and end location of the range. 
                   For clippings of type "note" or "bookmark", the start and end location 
                   are typically identical.
        datetime: An ISO 8601 formatted datetime string. No timezone is specified.

    Raises:
        SyntaxError: An error occurred when parsing the string.
    """

    # The clipping metadata consists of:
    # a clipping type (Bookmark, Highlight, Note)
    # an optional page number (optional because not all ebooks are divided into pages)
    # a location (for bookmark, note) or range (for highlight)
    # a timestamp
    # The timestamp may or may not have a comma after the four-digit year, and it may or may not include seconds, this depends on the OS level on the Kindle.
    # Examples:
    #   Highlights:
    # - Your Highlight on Page 384 | Location 6804-6807 | Added on Friday, March 02, 2012, 07:27 PM
    # - Your Highlight Location 3249-3251 | Added on Wednesday, April 22, 2015 12:33:10 PM
    #   Notes:
    # - Your Note on Page 92 | Location 1891 | Added on Sunday, December 18, 2011, 11:26 PM
    # - Your Note Location 2060 | Added on Sunday, November 13, 2011, 06:57 PM
    #  Bookmarks:
    # - Your Bookmark on Page 269 | Location 5454 | Added on Wednesday, December 21, 2011, 08:25 AM
    # - Your Bookmark Location 171 | Added on Thursday, January 12, 2012, 11:19 PM
    if s == '\n' or s == '': raise SyntaxError('The clipping metadata string is empty')
    datetime = ""
    datetime_start = 0
    datetime_found = False 
    for match in timestamp_regex.finditer(s):
        datetime_found = True
        datetime_start = match.start()
        try:
            datetime = _get_datetime(match.group(2).strip())
        except Exception as e:
            raise SyntaxError('Datetime not parseable in clipping metadata string') from e
        break
    
    if datetime_found:
        # remove the date time portion of the string
        s = s[:datetime_start].strip()
    else:
        raise SyntaxError('Datetime not found in clipping metadata string')
    
    # get the clipping type, page, and location from the remainder

    clip_type = ""
    clip_type_found = False
    for match in clip_type_regex.finditer(s):
        clip_type_found = True
        clip_type_end = match.end()
        clip_type = match.group(1).strip().lower()
        break
    if clip_type_found:
        # remove the clip type from the string
        s = s[clip_type_end:].strip()
    else:
        raise SyntaxError('Clip type not found')
    
    # get the page if it is present
    page = None
    for match in page_regex.finditer(s):
        page = int(match.group(1))
        break
    
    # Get the location range. It may be expressed as a single integer, 
    # or as two integers, examples:
    # Location 1000
    # Location 1000-1003
    # Group 1 is the first integer, 
    # and group 2, if present is the second integer.
    range_begin = None
    range_end = None
    for match in loc_regex.finditer(s):
        range_begin = int(match.group(1))
        if (match.group(2) is not None):
            range_end = int(match.group(2))
        else:
            range_end = range_begin
        break
    loc_range = (range_begin,range_end)
    return clip_type,page,loc_range,datetime


DATETIME_REGEX = r"""
    (
        (?:January  |
            February |
            March    | 
            April    | 
            May      |
            June     |
            July     |
            August   |
            September|
            October  |
            November |
            December)
    )              # month
    \s*
    (\d+)          # day
    ,\s*
    (\d{4,4})      # year
    ,?\s*          # optional comma after the year
    (\d+)          # hour
    \:
    (\d+)          # minute
    (?::(\d\d))?   # optional seconds
    \s*
    ((?:AM|PM))    # period
    \s*$
"""
datetime_regex = re.compile(DATETIME_REGEX, re.VERBOSE)

def _get_datetime(s):
    """Return a datetime.datetime object parsed from 
    a Kindle clipping datetime string.

    Args:
        s: A Kindle clipping datetime string. 
           Examples of such strings are "March 1, 2012, 1:36 AM" 
           and "April 2, 2018 6:33:10 PM"  
           Note that an optional comma can follow the year
           and seconds are optional in the time portion.
    Returns:
        A datetime.datetime object.
    """

    # It would be nice to be able to define a single format string 
    # for use with datetime.strptime, but as seen in the examples, 
    # Kindle clipping files can express datetimes in slightly 
    # different ways. Therefore, we first have to normalize the components 
    # of the Kindle datetime string into a consistent form. 
    # The normalized form has no commas and always specifies seconds:
    # "April 22 2018 12:33:10 PM"
    
    # Use the DATETIME_REGEX regex which contains these groups:
    # 1: Month (en_US spelling of months)
    # 2: Day
    # 3: Year
    # 4: Hour
    # 5: Minute
    # 6: Optional seconds
    # 7: AM/PM (en_US spelling)
    
    month = None
    day = None
    year = None
    hour = None
    minute = None
    seconds = '00' # the Kindle datetime may not specify any seconds
    period = 'AM'
    
    for match in datetime_regex.finditer(s):
        month  = match.group(1)
        day    = match.group(2).zfill(2) #zero padded, two digits
        year   = match.group(3)
        hour   = match.group(4).zfill(2) #zero padded, two digits
        minute = match.group(5)
        if match.group(6) is not None:
            seconds = match.group(6)
        period = match.group(7)
        break  


    normalized_string = "%s %s %s %s:%s:%s %s" % (month, day, year, hour, minute, seconds, period) 
    dt = datetime.datetime.strptime(normalized_string, "%B %d %Y %I:%M:%S %p")
    return dt

def main():
    """Demonstrate the Kindle Clipping parser by processing the 
    input file and printing the resulting clipping obects.""" 
    
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-i','--input', help='Input file name', required=True)
    args = parser.parse_args()
    i = 0
    for clipping in get_clippings_from_filename(args.input):
        print(i, ':')
        print(clipping)
        i += 1
    print('End of input')

if __name__ == '__main__':
    main()
    