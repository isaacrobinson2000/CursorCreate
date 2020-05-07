"""
Cursor Package:
Provides core objects or data types for manipulating cursor data, including images, hotspots, and delays...
"""

from typing import Tuple, Iterable, Iterator, Union
from PIL import Image, ImageOps


class CursorIcon:
    """
    Represents a single icon within a cursor of a unique size. Contains an image and a hotspot...
    """
    def __init__(self, img: Image, hot_x: int, hot_y: int):
        """
        Create a new CursorIcon, which represents a single picture of fixed size stored in a cursor. The image of
        this object can't be modified once set, but the hotspot can.

        :param img: The PIL Image representing the cursor bitmap...
        :param hot_x: The x location of the hotspot relative to the top right corner.
        :param hot_y: The y location of the
        """
        self._image: Image.Image = img
        self._hotspot = None
        self.hotspot = (hot_x, hot_y)

    @property
    def image(self) -> Image.Image:
        """
        Get the PIL Image of this icon within the cursor.

        :return: The image representing this cursor at a given size...
        """
        return self._image

    @property
    def hotspot(self) -> Tuple[int, int]:
        """
        Get or Set the hotspot of this cursor, being the x, y tuple representing the hotspot's offset from the top
        right corner of the image. Must land within the bounds of the actual image...
        """
        return self._hotspot

    @hotspot.setter
    def hotspot(self, value: Tuple[int, int]):
        new_x, new_y = int(value[0]), int(value[1])

        if(not((0 <= new_x < self.image.size[0]) and (0 <= new_y < self.image.size[1]))):
            raise ValueError(f"{(new_x, new_y)} is not a valid hotspot for cursor icon of size {(self.image.size)}!!!")

        self._hotspot = (new_x, new_y)


class Cursor:
    """
    Represents a static cursor. Stores image and hotspot data for unique sizes. CursorIcons are accessed by size...
    """
    def __init__(self, cursors: Iterable[CursorIcon] = None):
        """
        Construct a new cursor.

        :param cursors: Optional, a iterable of CursorIcons of which to initialize this cursor with
        """
        self._curs = {}
        if(cursors is not None):
            self.extend(cursors)

    def add(self, cursor: CursorIcon):
        """
        Add a cursor icon to this cursor, or override a prior cursor icon if one of the same size already exists in
        this cursor object.

        :param cursor: The CursorIcon to add to this cursor...
        """
        self._curs[cursor.image.size] = cursor

    def extend(self, cursors: Iterable[CursorIcon]):
        """
        Add or update a sequence of CursorIcons to this cursor.

        :param cursors: A sequence of CursorIcons.
        """
        for cursor in cursors:
            self.add(cursor)

    def __getitem__(self, size: Tuple[int, int]) -> CursorIcon:
        """
        Return a CursorIcon stored in this cursor, provided it's size...

        :param size: The size of the CursorIcon to get from this cursor.
        :return: The CursorIcon of the same size. If it doesn't exist throws a KeyError...
        """
        return self._curs[size]

    def __iter__(self) -> Iterator[Tuple[int, int]]:
        """
        Iterate over all of the sizes of the CursorIcons stored in this cursor.

        :return: An iterator which iterates over all image sizes stored in this cursor object.
        """
        return self._curs.__iter__()

    def __contains__(self, size: Tuple[int, int]) -> bool:
        """
        Check if a CursorIcon of this size exists in the cursor object...

        :param size: The size to check for.
        :return: A boolean, True if the CursorIcon of this size exists in this cursor, false otherwise...
        """
        return size in self._curs

    def __delitem__(self, size: Tuple[int, int]):
        """
        Delete the specified CursorIcon of given size.

        :param size: The size of the CursorIcon to delete in this cursor object
        """
        del self._curs[size]

    def pop(self, size: Tuple[int, int]) -> CursorIcon:
        cursor_icon = self._curs[size]
        del self._curs[size]
        return cursor_icon

    def __len__(self) -> int:
        """
        Returns the total number of CursorIcons stored in this cursor object...

        :return: The 'length' of this cursor, or how many icons are stored in it...
        """
        return len(self._curs)

    def max_size(self) -> Union[Tuple[int, int], None]:
        """
        Get the size of the largest CursorIcon stored in this cursor. Will return None if this cursor object is empty...
        """
        if(len(self) == 0):
            return None
        return max(iter(self), key=lambda s: s[0] * s[1])

    def add_sizes(self, sizes: Iterable[Tuple[int, int]]):
        """
        Add specified sizes to this cursor, by resizing cursors which already exist in this CursorIcon...

        :param sizes: An iterable of tuples of 2 integers, representing width-height pairs to be added as sizes to
                      this cursor.
        """
        if(len(self) == 0):
            raise ValueError("Cursor is empty!!! Can't add sizes!!!")

        max_size = self.max_size()

        for size in sizes:
            if(size not in self):
                x_ratio, y_ratio = size[0] / max_size[0], size[1] / max_size[1]

                if(x_ratio <= y_ratio):
                    final_img_w = size[0]
                    w_offset = 0
                    final_img_h = (max_size[1] / max_size[0]) * final_img_w
                    h_offset = (size[1] - final_img_h) / 2
                else:
                    final_img_h = size[1]
                    h_offset = 0
                    final_img_w = (max_size[0] / max_size[1]) * final_img_h
                    w_offset = (size[0] - final_img_w) / 2

                new_cur = ImageOps.pad(self[max_size].image, size, Image.LANCZOS).resize(size, Image.LANCZOS)

                new_hx = w_offset + (self[max_size].hotspot[0] / max_size[0]) * final_img_w
                new_hy = h_offset + (self[max_size].hotspot[1] / max_size[1]) * final_img_h
                self.add(CursorIcon(new_cur, int(new_hx), int(new_hy)))

    def restrict_to_sizes(self, sizes: Iterable[Tuple[int, int]]):
        """
        Restricts the sizes stored in this cursor to only the sizes passed to this method, deleting the rest.

        :param sizes: An iterable of Tuples of two integers, used as the only sizes to keep.
        """
        sizes = set(sizes)
        self.add_sizes(sizes)

        for size in list(self):
            if(size not in sizes):
                del self[size]

    def remove_non_square_sizes(self):
        """
        Remove all non-square sized cursors from this cursor object.
        """
        for size in list(self):
            if(size[0] != size[1]):
                del self[size]

    def copy(self) -> "Cursor":
        """
        Creates a shallow copy of this cursor.

        :return: A shallow copy of this cursor, only copies the lookup table.
        """
        return Cursor(self._curs.values())


class AnimatedCursor(list):
    """
    Represents an animated cursor. Is actually a subtype of list, storing its data in the form of a list of tuples,
    each tuple containing the Cursor object at that frame, and then the delay as an integer in milliseconds...
    """
    # NOTE: Delay unit is milliseconds...
    def __init__(self, cursors: Iterable[Cursor]=None, framerates: Iterable[int]=None):
        """
        Create a new animated cursor.

        :param cursors: A list of cursor object to add as frames, optional.
        :param framerates: A list of integer frame rates in the form of milliseconds, optional also.
        """
        framerates = framerates if(framerates is not None) else []
        cursors = cursors if(cursors is not None) else []

        super().__init__(self)
        self.extend(zip(cursors, framerates))

    def normalize(self, init_sizes: Iterable[Tuple[int, int]] = None):
        """
        Normalize this animated cursor, by making sure all frames contain the same sizes. This is done by adding
        missing sizes...

        :param init_sizes: An Iterable of a tuple of integers, being width, height pairs. These are sizes which will
                           be added to all the cursor frames in this animated cursor...
        :return:
        """
        if(init_sizes is None):
            init_sizes = []

        sizes = set(init_sizes)

        for cursor, delay in self:
            sizes.update(set(cursor))

        for cursor, delay in self:
            cursor.add_sizes(sizes)

    def remove_non_square_sizes(self):
        """
        Remove all non-square sized cursors from this animated cursor object
        (done by removing them from all sub-cursor objects).
        """
        for cursor, delay in self:
            cursor.remove_non_square_sizes()

    def restrict_to_sizes(self, sizes: Iterable[Tuple[int, int]]):
        """
        Forces all cursors in this animated cursor to only contain the sizes passed to this method

        :param sizes: An iterable of tuples of two integers, representing the sizes to keep.
        """
        for cursor, delay in self:
            cursor.restrict_to_sizes(sizes)


    def copy(self) -> "AnimatedCursor":
        """
        Creates a shallow copy of this AnimatedCursor which contains shallow copies of the Cursor objects contained
        inside of it.

        :return: An AnimatedCursor
        """
        return AnimatedCursor([cur.copy() for cur, delay in self], [delay for cur, delay in self])

