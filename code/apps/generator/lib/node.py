from itertools import zip_longest


def block_width(block):
    try:
        return block.index('\n')
    except ValueError:
        return len(block)


def stack_str_blocks(blocks):
    """Takes a list of multiline strings, and stacks them horizontally.

    For example, given 'aaa\naaa' and 'bbbb\nbbbb', it returns
    'aaa bbbb\naaa bbbb'.  As in:

    'aaa  +  'bbbb   =  'aaa bbbb
     aaa'     bbbb'      aaa bbbb'

    Each block must be rectangular (all lines are the same length), but blocks
    can be different sizes.
    """
    builder = []
    block_lens = [block_width(bl) for bl in blocks]
    split_blocks = [bl.split('\n') for bl in blocks]

    for line_list in zip_longest(*split_blocks, fillvalue=None):
        for i, line in enumerate(line_list):
            if line is None:
                builder.append(' ' * block_lens[i])
            else:
                builder.append(line)
            if i != len(line_list) - 1:
                builder.append(' ')  # Padding
        builder.append('\n')

    return ''.join(builder[:-1])


class Node:
    def __init__(self, webroots=[]):
        # All webroot ids in this subtree
        self.webroots = webroots
        # path used to separate left and right subtree
        self.path = ""
        # Left subtree node
        self.left = None
        # Right subtree node
        self.right = None
        self.files = []
        self.file_type = ""

    def to_dict(self):
        left = None if not self.left else self.left.to_dict()
        right = None if not self.right else self.right.to_dict()
        ret = {'path': self.path,
               'type': str(self.file_type),
               'webroots': str(self.webroots),
               'files': self.files,
               'left': left,
               'right': right,
               }
        """
        s = "{\"path\": \"" + self.path + "\", " + \
            "\"type\": \"" + str(self.file_type) + "\", " + \
            "\"webroots\": " + str(self.webroots) + ", " + \
            "\"files\": " + self.files + ", " + \
            "\"left\": " + left + ", " + \
            "\"right\": " + right + "}"
        return s
        """
        return ret

    def display(self):
        if not self.left and not self.right:
            return str(self.webroots)
        child_strs = []
        if self.left:
            child_strs.append(self.left.display())
        if self.right:
            child_strs.append(self.right.display())
        child_widths = [block_width(s) for s in child_strs]

        # How wide is this block?
        display_width = max(len(self.path), len(self.webroots),
                            sum(child_widths) + len(child_widths) - 1)

        # Determines midpoints of child blocks
        child_midpoints = []
        child_end = 0
        for width in child_widths:
            child_midpoints.append(child_end + (width // 2))
            child_end += width + 1

        # Builds up the brace, using the child midpoints
        brace_builder = []
        brace_builder_2 = []
        for i in range(display_width):
            if i < child_midpoints[0] or i > child_midpoints[-1]:
                brace_builder.append(' ')
                brace_builder_2.append(' ')
            elif i in child_midpoints:
                brace_builder.append('+')
                brace_builder_2.append('|')
            else:
                brace_builder.append('-')
                brace_builder_2.append(' ')
        brace = ''.join(brace_builder) + '\n' + ''.join(brace_builder_2)

        if not self.path:
            name_str = '{:^{}}'.format(str(self.webroots), display_width)
        else:
            name_str = '{:^{}}'.format(self.path, display_width)
        below = stack_str_blocks(child_strs)

        return name_str + '\n' + brace + '\n' + below

    def __repr__(self):
        if not self.path:
            return "LEAF: {}".format(self.webroots)
        return "{}: {}".format(self.path, self.webroots)

    def __str__(self, level=0):
        ret = "\t" * level + repr(self) + "\n"
        if self.left:
            ret += "Left: " + self.left.__str__(level + 1)
        if self.right:
            ret += "Right: " + self.right.__str__(level + 1)
        return ret

    def depth(self):
        left = self.left.depth() if self.left else 0
        right = self.right.depth() if self.right else 0
        return 1 + max(left, right)

    def print_level_order(self):
        for i in range(self.depth()):
            self.__print_level_order(i)
            print("\n", end="")

    def __print_level_order(self, level):
        if level == 0:
            print(str(len(self.webroots)), end=", ")
            return

        if self.left:
            self.left.__print_level_order(level - 1)
        if self.right:
            self.right.__print_level_order(level - 1)
