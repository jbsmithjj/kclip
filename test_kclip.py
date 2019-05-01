# Test cases for kctok
import kclip
import textwrap
import datetime
import unittest
import tempfile
import os


class KClipTestCase(unittest.TestCase):
    def test_get_book(self):
        book_identification_values = (
            (
                # input: kindle clipping's line containing title and author
                "Ghost Train to the Eastern Star: On the Tracks of the Great Railway Bazaar (Theroux, Paul)",
                # expected: title
                "Ghost Train to the Eastern Star: On the Tracks of the Great Railway Bazaar",
                # expected: author
                "Theroux, Paul"
            ),    
            (
                "Wicked Plants: The Weed That Killed Lincoln's Mother and Other Botanical Atrocities (Stewart, Amy)",
                "Wicked Plants: The Weed That Killed Lincoln's Mother and Other Botanical Atrocities",
                "Stewart, Amy"
            ),
            (
                "Quicksilver (The Baroque Cycle Book 1) (Stephenson, Neal)",
                "Quicksilver (The Baroque Cycle Book 1)",
                "Stephenson, Neal"
            ),
            (
                "The Big Book of Science Fiction ( )",
                "The Big Book of Science Fiction",
                ""
            ),
            (
                "A book with no parenthetical author",
                "A book with no parenthetical author",
                ""
            ),
            (
                "A book with an empty, no whitespace, parenthetical author  ()",
                "A book with an empty, no whitespace, parenthetical author",
                ""
            ),
            (
                "\ufeffA book with a leading byte-order mark  ()",
                "A book with a leading byte-order mark",
                ""
            ),

        )

        for input_string, expected_title, expected_author in book_identification_values:
            title,author = kclip._get_book(input_string)
            self.assertEqual(title,expected_title, "Title does not match expected value")
            self.assertEqual(author,expected_author, "Author does not match expected value")

    def test_get_book_errors(self):
        book_values = (
            "",
            "\n"
        )

        for input_string in book_values:
            self.assertRaises(SyntaxError,kclip._get_book,input_string)

    def test_get_clip_meta(self):
        clip_meta_values = (
            (
                # kindle clipping's line containing clip type, page, location, datetime
                "- Your Highlight on Page 376 | Location 6566-6568 | Added on Friday, January 27, 2012, 07:18 PM",
                # expected clip type
                "highlight",
                # expected page number
                376,
                # expected location range
                (6566,6568),
                # expected datetime
                "2012-01-27T19:18:00"
            ),  
            (
                "- Your Highlight on Page 37 | Location 660-668 | Added on Thursday, January 12, 2012, 11:34 PM",
                "highlight",
                37,
                (660,668),
                "2012-01-12T23:34:00"
            ),
            (
                "- Your Highlight Location 3935-3938 | Added on Wednesday, February 08, 2012, 12:44 AM",
                "highlight",
                None,
                (3935,3938),
                "2012-02-08T00:44:00"
            ),
            (
                "- Your Note Location 2060 | Added on Sunday, November 13, 2011, 06:57 PM",
                "note",
                None,
                (2060,2060),
                "2011-11-13T18:57:00"
            ),
            (
                "- Your Bookmark Location 3442 | Added on Wednesday, June 1, 2016 10:25:25 PM",
                "bookmark",
                None,
                (3442,3442),
                "2016-06-01T22:25:25"
            ),
        )
        for (input_string, 
             expected_clip_type, 
             expected_page, 
             expected_loc_range, 
             expected_dt) in clip_meta_values:
            clip_type,page,location_range,dt = kclip._get_clip_meta(input_string)
            self.assertEqual(clip_type, expected_clip_type, "Clipping type does not match expected value")
            self.assertEqual(page, expected_page, "Page number does not match expected value")
            self.assertEqual(location_range, expected_loc_range, "Location range does not match expected value")
            self.assertEqual(dt.isoformat(), expected_dt, "Datetime does not match expected value")

    def test_get_clip_meta_errors(self):
        clip_meta_values = (
            # kindle clipping's line containing clip type, page, location, datetime
            # unknown clipping type "COMMENT"
            "- Your COMMENT on Location 376 | Added on Friday, January 27, 2012, 07:18 PM",
            # blank lines
            "\n",
            "",
            "      ",
            # Malformed datetime (missing period AM/PM)
            "- Your Highlight on Location 376 | Added on January 27, 2012, 07:18"
        )
        for input_string in clip_meta_values:
            self.assertRaises(SyntaxError, kclip._get_clip_meta, input_string)

    def test_get_datetime(self):
        dt_values = (    
            (
                # kindle formatted datetime
                "November 2, 2016 9:04:02 PM",
                # expected equivalent ISO datetime
                datetime.datetime(2016, 11, 2, 21, 4, 2)
            ),
            (
                "Thursday, January 12, 2012, 11:34 PM",
                datetime.datetime(2012, 1, 12, 23, 34, 0)
            ),
            (
                "February 08, 2012, 12:44 AM",
                datetime.datetime(2012, 2, 8, 0, 44, 0)
            ),
            (
                "November 13, 2011, 06:57 PM",
                datetime.datetime(2011, 11, 13, 18, 57, 0)
            ),
            (
                "June 1, 2016 10:25:24 PM",
                datetime.datetime(2016, 6, 1, 22, 25, 24)
            ),
        )
        for input_string, expected_dt in dt_values:
            dt = kclip._get_datetime(input_string)
            self.assertEqual(dt, expected_dt, "Datetime does not match expected value")

    def test_get_datetime_errors(self):
        dt_values = (    
            # datetimes that should result in ValueError 
            "November 99, 2016 9:04:02 PM",
            "November 19, 2016 9:04:02",
            "",
            "NonexistentNovember 19, 2016 9:04:02 AM"
            "November 19, 2016 9:04:60 AM",
        )
        for input_string in dt_values:
            self.assertRaises(ValueError, kclip._get_datetime, input_string)

    def test_get_clipping_object(self):
        clipping_values = (
            (
                # list of strings corresponding to a Kindle clipping from My Clippings.txt
                ["Four Fish: The Future of the Last Wild Food (Greenberg, Paul)",
                "- Your Highlight on Page 12 | Location 203-206 | Added on Saturday, December 24, 2011, 03:24 PM",
                "\n",
                "In cases where grounds have been seemingly tapped out, ten years’ rest has sometimes been enough to restore them to at least some of their former glory. World War II, while one of the most devastating periods in history for humans, might be called “The Great Reprieve” if history were written by fish. With mines and submarines ready to blow up any unsuspecting fishing vessel, much of the North Atlantic’s depleted fishing grounds were left fallow and fish increased their numbers significantly."
                ],
                # expected equivalent Clipping object
                kclip.Clipping("Four Fish: The Future of the Last Wild Food",
                        "Greenberg, Paul",
                        "highlight",
                        12,
                        (203,206), 
                        datetime.datetime(2011,12,24,15,24,0),
                        "In cases where grounds have been seemingly tapped out, ten years’ rest has sometimes been enough to restore them to at least some of their former glory. World War II, while one of the most devastating periods in history for humans, might be called “The Great Reprieve” if history were written by fish. With mines and submarines ready to blow up any unsuspecting fishing vessel, much of the North Atlantic’s depleted fishing grounds were left fallow and fish increased their numbers significantly."
                        )
            ),
            (
                # list of strings corresponding to a Kindle clipping from My Clippings.txt
                ["Four Fish: The Future of the Last Wild Food (Greenberg, Paul)",
                "- Your Highlight on Page 12 | Location 203-206 | Added on Saturday, December 24, 2011, 03:24 PM",
                "Normally a blank line\n",
                "In cases where grounds have been seemingly tapped out, ten years’ rest has sometimes been enough to restore them to at least some of their former glory. World War II, while one of the most devastating periods in history for humans, might be called “The Great Reprieve” if history were written by fish. With mines and submarines ready to blow up any unsuspecting fishing vessel, much of the North Atlantic’s depleted fishing grounds were left fallow and fish increased their numbers significantly."
                ],
                # expected equivalent Clipping object
                kclip.Clipping("Four Fish: The Future of the Last Wild Food",
                        "Greenberg, Paul",
                        "highlight",
                        12,
                        (203,206), 
                        datetime.datetime(2011,12,24,15,24,0),
                        "Normally a blank line\nIn cases where grounds have been seemingly tapped out, ten years’ rest has sometimes been enough to restore them to at least some of their former glory. World War II, while one of the most devastating periods in history for humans, might be called “The Great Reprieve” if history were written by fish. With mines and submarines ready to blow up any unsuspecting fishing vessel, much of the North Atlantic’s depleted fishing grounds were left fallow and fish increased their numbers significantly."
                        )
            )
        )
        for input_clip_str_list, expected_clipping in clipping_values:
            clipping = kclip._get_clipping_object(input_clip_str_list)
            self.assertEqual(clipping, expected_clipping, "Clipping object does not match expected value")

    clip_string_lists_errors = (
        # list of strings too short to constitute a clipping
        ["Test case 1: Four Fish: The Future of the Last Wild Food (Greenberg, Paul)",
        "- Your Highlight on Page 12 | Location 203-206 | Added on Saturday, December 24, 2011, 03:24 PM",
        ],
        # syntax error in clip metadata
        ["Test case 2: Four Fish: The Future of the Last Wild Food (Greenberg, Paul)",
        "- Your Highlight on Page 54 | Location 203-206 | Added on Saturday, MISSING_MONTH 24, 2011, 03:24 PM",
        "Normally a blank line\n",
        "In cases where grounds have been seemingly tapped out, ten years’ rest has sometimes been enough to restore them to at least some of their former glory. World War II, while one of the most devastating periods in history for humans, might be called “The Great Reprieve” if history were written by fish. With mines and submarines ready to blow up any unsuspecting fishing vessel, much of the North Atlantic’s depleted fishing grounds were left fallow and fish increased their numbers significantly."
        ],
    )

    def test_get_clipping_object_errors(self):
        for input_clip_str_list in self.clip_string_lists_errors:
            self.assertRaises(SyntaxError, kclip._get_clipping_object,input_clip_str_list)

    def test_get_clipping_object_from_clip_strings(self):
        unparseable_clipping_values = (
            (
                # input string list
                self.clip_string_lists_errors[0],
                # expected result object
                kclip.UnparseableClipping(0, SyntaxError('Insufficient strings to constitute a clipping'), self.clip_string_lists_errors[0])
            ),
            (
                self.clip_string_lists_errors[1],
                kclip.UnparseableClipping(0, SyntaxError('Datetime not found in clipping metadata string'), self.clip_string_lists_errors[1])
            )
        )
        for input_clip_str_list, expected_obj in unparseable_clipping_values:
            clipping = kclip._get_clipping_object_from_clip_strings(input_clip_str_list, 0)
            self.assertEqual(clipping.error.msg, expected_obj.error.msg, "UnparseableClipping's error message does not match expected value.")

    def test_roundtrip_clipping_object_via_kindle_format(self):
        clipping_values = (
            kclip.Clipping(title='The Hunt for Red October (Jack Ryan)',author='Clancy, Tom',clip_type='highlight',page=35,loc_range=(679, 680),datetime=datetime.datetime(2014, 12, 12, 8, 51),clip_text='The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones\n') ,
            kclip.Clipping(title='The Hunt for Red October (Jack Ryan)',author='Clancy, Tom',clip_type='highlight',page=None,loc_range=(679, 680),datetime=datetime.datetime(2014, 12, 12, 8, 51),clip_text='The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones\n') ,
        )
        for original in clipping_values:
            kindle_strs = original.get_kindle_strs()
            roundtrip = kclip._get_clipping_object_from_clip_strings(kindle_strs, 0)
            self.assertEqual(original, roundtrip, "Roundtripped object does not match original.")


class KCTokFromFileTestCase(unittest.TestCase):
    def test_get_clippings_from_filename_error(self):
        with self.assertRaises(IOError):
            for clipping in kclip.get_clippings_from_filename("NONEXISTENT_FILE"):
                print(clipping)

# Raw string contents of a small Kindle "My Clippings.txt" file.
    clipping_file_content = """The Drunken Botanist (Stewart, Amy)
- Your Highlight Location 4868-4872 | Added on Wednesday, December 10, 2014, 06:09 PM

The secret to getting the essential oil out of any plant in the mint family (including mint, basil, sage, and anise hyssop) is to bruise the leaves without crushing them. This expresses the oil from the modified trichomes, or tiny hairs, on the surface of the leaf without cluttering up the drink unnecessarily with chlorophyll. Get the most flavor out of the fresh leaves by spanking them—just place the leaf in the palm of one hand and clap your hands briskly once or twice. You’ll look like a pro and you’ll release fresh aromatics into the drink. 
==========
The Drunken Botanist (Should result in unparseable clipping) (Stewart, Amy)
- Your Highlight Location 5319-5319 | Added on Wednesday, December 10, 2014, 07:44

Reich, Lee, and Vicki Herzfeld Arlein. Uncommon Fruits for Every Garden. Portland, OR: Timber Press, 2008. 
==========
The Hunt for Red October (Jack Ryan) (Clancy, Tom)
- Your Highlight Location 675-676 | Added on Friday, December 12, 2014, 08:51 AM

The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones, had once served the Russian navy for the Czaritza Catherine. 
==========
The Hunt for Red October (Jack Ryan) (Clancy, Tom)
- Your Highlight on Page 35 | Location 679-680 | Added on Friday, December 12, 2014, 08:51 AM

The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones
==========
"""

# The corresponded objects that would be parsed from the clipping_file_content.
    expected_objs_from_clipping_file_content = [
        kclip.Clipping(title='The Drunken Botanist',author='Stewart, Amy',clip_type='highlight',page=None,loc_range=(4868, 4872),datetime=datetime.datetime(2014, 12, 10, 18, 9),clip_text='The secret to getting the essential oil out of any plant in the mint family (including mint, basil, sage, and anise hyssop) is to bruise the leaves without crushing them. This expresses the oil from the modified trichomes, or tiny hairs, on the surface of the leaf without cluttering up the drink unnecessarily with chlorophyll. Get the most flavor out of the fresh leaves by spanking them—just place the leaf in the palm of one hand and clap your hands briskly once or twice. You’ll look like a pro and you’ll release fresh aromatics into the drink. \n'),
        kclip.UnparseableClipping(lineno=5,error=SyntaxError('Datetime not found in clipping metadata string'),original_lines=['The Drunken Botanist (Should result in unparseable clipping) (Stewart, Amy)\n', '- Your Highlight Location 5319-5319 | Added on Wednesday, December 10, 2014, 07:44\n', '\n', 'Reich, Lee, and Vicki Herzfeld Arlein. Uncommon Fruits for Every Garden. Portland, OR: Timber Press, 2008. \n']),
        kclip.Clipping(title='The Hunt for Red October (Jack Ryan)',author='Clancy, Tom',clip_type='highlight',page=None,loc_range=(675, 676),datetime=datetime.datetime(2014, 12, 12, 8, 51),clip_text='The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones, had once served the Russian navy for the Czaritza Catherine. \n'),        
        kclip.Clipping(title='The Hunt for Red October (Jack Ryan)',author='Clancy, Tom',clip_type='highlight',page=35,loc_range=(679, 680),datetime=datetime.datetime(2014, 12, 12, 8, 51),clip_text='The Americans, he knew, had long experience in naval warfare—their own greatest fighter, Jones\n'),        
    ]

    def test_get_clippings_from_filename(self):
        # create a temp file, populate it with the contents of clipping_file_content, then 
        # give that filename to get_clippings_from_filename.
        try:
            f = tempfile.NamedTemporaryFile(mode='w',delete=False,encoding='utf-8')
            f.writelines(self.clipping_file_content)
            f.close()

            for clipping, expected_obj in zip(kclip.get_clippings_from_filename(f.name), 
                                              self.expected_objs_from_clipping_file_content):
                self.assertEqual(type(clipping), type(expected_obj), "The type of the clipping does not match the expected type.")
                if (type(clipping) is kclip.Clipping):
                    self.assertEqual(clipping, expected_obj, "Generated clipping object does not match the expected object.")
                else:
                    self.assertEqual(clipping.error.msg, expected_obj.error.msg, "Generated UnparseableClipping object does not match the expected UnparseableClipping object.")
        finally:
            os.remove(f.name)
        
if __name__ == '__main__':
    unittest.main()

