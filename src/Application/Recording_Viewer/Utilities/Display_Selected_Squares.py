from tkinter import *


def display_selected_squares(self):
    """
    Display the squares on the left image canvas, that have the 'Selected' flag set
    :return:
    """

    # Clear the screen and reshow the picture
    self.cn_left_image.delete("all")
    self.cn_left_image.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

    # Bind left buttons for canvas
    self.cn_left_image.bind('<Button-1>', lambda e: self.start_rectangle(e))
    self.cn_left_image.bind('<ButtonRelease-1>', lambda e: self.close_rectangle(e))
    self.cn_left_image.bind('<B1-Motion>', lambda e: self.expand_rectangle_size(e))

    if self.show_squares:
        # If there are no squares, you can stop here
        if len(self.df_squares) > 0:

            # Then draw the of squares that are assigned to a cell
            for index, squares_row in self.df_squares.iterrows():
                if squares_row['Selected']:
                    if squares_row['Cell Id'] != 0:
                        draw_single_square(
                            self.show_squares_numbers, self.nr_of_squares_in_row, self.cn_left_image, squares_row,
                            self.square_assigned_to_cell, self.provide_information_on_square)
            # Then draw the thin lines of squares that are not assigned to a cell
            for index, squares_row in self.df_squares.iterrows():
                if squares_row['Selected']:
                    draw_single_square(
                        self.show_squares_numbers, self.nr_of_squares_in_row, self.cn_left_image, squares_row,
                        self.square_assigned_to_cell, self.provide_information_on_square)

            # Then draw the thick lines of squares that are marked
            mark_selected_squares(self.squares_in_rectangle, self.nr_of_squares_in_row, self.cn_left_image)


def draw_single_square(
        show_squares_numbers,
        nr_of_squares_in_row,
        canvas,
        squares_row,
        square_assigned_to_cell,
        provide_information_on_square,
        color='white'):
    colour_table = {1: ('red', 'white'),
                    2: ('yellow', 'black'),
                    3: ('green', 'white'),
                    4: ('magenta', 'white'),
                    5: ('cyan', 'black'),
                    6: ('black', 'white')}

    square_nr = squares_row['Square Nr']
    cell_id = squares_row['Cell Id']
    label_nr = squares_row['Label Nr']

    col_nr = square_nr % nr_of_squares_in_row
    row_nr = square_nr // nr_of_squares_in_row
    width = 512 / nr_of_squares_in_row
    height = 512 / nr_of_squares_in_row

    square_tag = f'square-{square_nr}'
    text_tag = f'text-{square_nr}'

    if cell_id == -1:  # The square is deleted (for good), stop processing
        return

    if cell_id != 0:  # The square is assigned to a cell
        col = colour_table[squares_row['Cell Id']][0]
        canvas.create_rectangle(
            col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
            outline=col, fill=col, width=0, tags=square_tag)

        if show_squares_numbers:
            canvas.create_text(
                col_nr * width + 0.5 * width, row_nr * width + 0.5 * width,
                text=str(squares_row['Label Nr']), font=('Arial', -10),
                fill=colour_table[squares_row['Cell Id']][1], tags=text_tag)

    # for all the squares draw the outline without filling the rectangle
    canvas.create_rectangle(
        col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
        outline="white", fill="", width=1, tags=square_tag)

    if show_squares_numbers:
        if cell_id == 0:  # The number of a square assigned to a cell should not be overwritten
            canvas.create_text(
                col_nr * width + 0.5 * width, row_nr * width + 0.5 * width, text=str(label_nr),
                font=('Arial', -10), fill='white', tags=text_tag)

    # Create a transparent rectangle (clickable area)
    invisible_rect = canvas.create_rectangle(
        col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
        outline="", fill="", tags=f"invisible-{square_nr}")

    # Bind events to the invisible rectangle (transparent clickable area)
    canvas.tag_bind(invisible_rect, '<Button-1>', lambda e: square_assigned_to_cell(square_nr))
    canvas.tag_bind(invisible_rect, '<Button-2>',
                    lambda e: provide_information_on_square(e, squares_row['Label Nr'], square_nr))


def mark_selected_squares(list_of_squares, nr_of_squares_in_row, canvas):
    for square_nr in list_of_squares:
        col_nr = square_nr % nr_of_squares_in_row
        row_nr = square_nr // nr_of_squares_in_row
        width = 512 / nr_of_squares_in_row
        height = 512 / nr_of_squares_in_row

        # Draw the outline without filling the rectangle
        canvas.create_rectangle(
            col_nr * width, row_nr * width, col_nr * width + width, row_nr * height + height,
            outline='white', fill="", width=3)
