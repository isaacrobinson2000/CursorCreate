from typing import List, Sequence, Tuple
from PIL import Image, ImageOps

class CursorIcon:
    def __init__(self, img: Image, hot_x, hot_y):
        self.image: Image = img
        self.hotspot = (hot_x, hot_y)


class Cursor:
    def __init__(self, cursors: List[CursorIcon] = None):
        self._curs = {}
        if(cursors is not None):
            self.extend(cursors)

    def add(self, cursor: CursorIcon):
        self._curs[cursor.image.size] = cursor

    def extend(self, cursors: Sequence[CursorIcon]):
        for cursor in cursors:
            self.add(cursor)

    def __getitem__(self, size):
        return self._curs[size]

    def __iter__(self):
        return self._curs.__iter__()

    def __contains__(self, size):
        return size in self._curs

    def __delitem__(self, size):
        del self._curs[size]

    def pop(self, size):
        cursor_icon = self._curs[size]
        del self._curs[size]
        return cursor_icon

    def __len__(self):
        return len(self._curs)

    def max_size(self):
        return max(iter(self), key=lambda s: s[0] * s[1])

    def add_sizes(self, sizes):
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

    def remove_non_square_sizes(self):
        for size in self:
            if(size[0] != size[1]):
                del self[size]


class AnimatedCursor(list):
    # NOTE: Delay unit is milliseconds...
    def __init__(self, cursors=None, framerates=None):
        framerates = framerates if(framerates is not None) else []
        cursors = cursors if(cursors is not None) else []

        super().__init__(self)
        self.extend(zip(cursors, framerates))

    def normalize(self, init_sizes: Sequence[Tuple[int, int]] = None):
        if(init_sizes is None):
            init_sizes = []

        sizes = set(init_sizes)

        for cursor, delay in self:
            sizes.update(set(cursor))

        for cursor, delay in self:
            cursor.add_sizes(sizes)

    def remove_non_square_sizes(self):
        for cursor, delay in self:
            cursor.remove_non_square_sizes()

